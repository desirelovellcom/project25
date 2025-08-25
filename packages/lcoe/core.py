"""
Core LCOE and LCOS calculation engines
"""

import numpy as np
import logging
from typing import List, Tuple, Optional
from .models import (
    LCOEInputs, LCOSInputs, LCOEResult, LCOSResult,
    FinancingParameters, DegradationModel
)

logger = logging.getLogger(__name__)

class LCOECalculator:
    """Levelized Cost of Energy calculator"""
    
    def __init__(self):
        self.logger = logger
    
    def calculate(self, inputs: LCOEInputs) -> LCOEResult:
        """Calculate LCOE for given inputs"""
        try:
            # Calculate total capital expenditure
            total_capex = self._calculate_total_capex(inputs)
            
            # Calculate annual energy generation
            annual_energy_mwh = self._calculate_annual_energy(inputs)
            
            # Calculate lifetime energy generation with degradation
            lifetime_energy_mwh = self._calculate_lifetime_energy(inputs, annual_energy_mwh)
            
            # Calculate operating costs (NPV)
            total_opex_npv = self._calculate_opex_npv(inputs)
            
            # Calculate fuel costs (NPV)
            total_fuel_npv = self._calculate_fuel_npv(inputs, annual_energy_mwh)
            
            # Calculate financing costs
            financing_cost = self._calculate_financing_cost(inputs, total_capex)
            
            # Calculate LCOE
            total_costs = total_capex + total_opex_npv + total_fuel_npv + financing_cost
            lcoe_usd_per_mwh = total_costs / lifetime_energy_mwh if lifetime_energy_mwh > 0 else 0
            lcoe_usd_per_kwh = lcoe_usd_per_mwh / 1000
            
            # Calculate component breakdown
            capex_component = total_capex / lifetime_energy_mwh if lifetime_energy_mwh > 0 else 0
            opex_component = total_opex_npv / lifetime_energy_mwh if lifetime_energy_mwh > 0 else 0
            fuel_component = total_fuel_npv / lifetime_energy_mwh if lifetime_energy_mwh > 0 else 0
            financing_component = financing_cost / lifetime_energy_mwh if lifetime_energy_mwh > 0 else 0
            
            return LCOEResult(
                lcoe_usd_per_mwh=lcoe_usd_per_mwh,
                lcoe_usd_per_kwh=lcoe_usd_per_kwh,
                capex_component=capex_component,
                opex_component=opex_component,
                fuel_component=fuel_component,
                financing_component=financing_component,
                total_capex=total_capex,
                total_opex_npv=total_opex_npv,
                total_energy_mwh=lifetime_energy_mwh,
                capacity_factor_actual=annual_energy_mwh / (inputs.system_size_kw * 8.76)
            )
            
        except Exception as e:
            self.logger.error(f"LCOE calculation failed: {e}")
            raise
    
    def _calculate_total_capex(self, inputs: LCOEInputs) -> float:
        """Calculate total capital expenditure including incentives"""
        base_capex = inputs.capex_per_kw * inputs.system_size_kw
        
        # Apply federal ITC
        itc_benefit = base_capex * inputs.financing.federal_itc
        
        # Apply state rebate
        state_rebate = inputs.financing.state_rebate * inputs.system_size_kw
        
        # Net CAPEX after incentives
        net_capex = base_capex - itc_benefit - state_rebate
        
        return max(0, net_capex)
    
    def _calculate_annual_energy(self, inputs: LCOEInputs) -> float:
        """Calculate first-year annual energy generation"""
        return inputs.system_size_kw * inputs.capacity_factor * 8760 / 1000  # MWh
    
    def _calculate_lifetime_energy(self, inputs: LCOEInputs, annual_energy_mwh: float) -> float:
        """Calculate total lifetime energy generation with degradation"""
        total_energy = 0.0
        discount_rate = inputs.financing.effective_discount_rate()
        
        for year in range(inputs.system_lifetime_years):
            # Apply degradation
            performance_factor = inputs.degradation.performance_factor(year)
            year_energy = annual_energy_mwh * performance_factor
            
            # Discount to present value
            discounted_energy = year_energy / ((1 + discount_rate) ** year)
            total_energy += discounted_energy
        
        return total_energy
    
    def _calculate_opex_npv(self, inputs: LCOEInputs) -> float:
        """Calculate net present value of operating expenses"""
        annual_fixed_om = inputs.fixed_om_per_kw_year * inputs.system_size_kw
        annual_variable_om = inputs.variable_om_per_mwh * self._calculate_annual_energy(inputs)
        annual_opex = annual_fixed_om + annual_variable_om
        
        return self._calculate_npv_series(
            annual_opex, 
            inputs.system_lifetime_years,
            inputs.financing.effective_discount_rate(),
            inputs.financing.inflation_rate
        )
    
    def _calculate_fuel_npv(self, inputs: LCOEInputs, annual_energy_mwh: float) -> float:
        """Calculate net present value of fuel costs"""
        if inputs.fuel_cost_per_mwh <= 0:
            return 0.0
        
        annual_fuel_cost = inputs.fuel_cost_per_mwh * annual_energy_mwh
        
        return self._calculate_npv_series(
            annual_fuel_cost,
            inputs.system_lifetime_years,
            inputs.financing.effective_discount_rate(),
            inputs.financing.inflation_rate
        )
    
    def _calculate_financing_cost(self, inputs: LCOEInputs, capex: float) -> float:
        """Calculate financing costs (interest on debt portion)"""
        debt_amount = capex * inputs.financing.debt_fraction
        annual_interest = debt_amount * inputs.financing.debt_interest_rate
        
        # Assume loan term equals system lifetime
        return self._calculate_npv_series(
            annual_interest,
            inputs.system_lifetime_years,
            inputs.financing.effective_discount_rate(),
            0.0  # Interest rates typically don't inflate
        )
    
    def _calculate_npv_series(self, annual_amount: float, years: int, 
                            discount_rate: float, inflation_rate: float) -> float:
        """Calculate NPV of an annual payment series with inflation"""
        npv = 0.0
        for year in range(years):
            inflated_amount = annual_amount * ((1 + inflation_rate) ** year)
            discounted_amount = inflated_amount / ((1 + discount_rate) ** year)
            npv += discounted_amount
        return npv

class LCOSCalculator:
    """Levelized Cost of Storage calculator"""
    
    def __init__(self):
        self.logger = logger
    
    def calculate(self, inputs: LCOSInputs) -> LCOSResult:
        """Calculate LCOS for given inputs"""
        try:
            # Calculate total capital expenditure
            total_capex = self._calculate_total_capex(inputs)
            
            # Calculate lifetime throughput
            lifetime_throughput_mwh = self._calculate_lifetime_throughput(inputs)
            
            # Calculate operating costs (NPV)
            total_opex_npv = self._calculate_opex_npv(inputs)
            
            # Calculate replacement costs (NPV)
            replacement_cost_npv = self._calculate_replacement_cost(inputs)
            
            # Calculate financing costs
            financing_cost = self._calculate_financing_cost(inputs, total_capex)
            
            # Calculate LCOS
            total_costs = total_capex + total_opex_npv + replacement_cost_npv + financing_cost
            lcos_usd_per_mwh = total_costs / lifetime_throughput_mwh if lifetime_throughput_mwh > 0 else 0
            lcos_usd_per_kwh = lcos_usd_per_mwh / 1000
            
            # Calculate performance metrics
            effective_cycles = self._calculate_effective_cycles(inputs)
            end_of_life_capacity = self._calculate_end_of_life_capacity(inputs)
            average_efficiency = self._calculate_average_efficiency(inputs)
            
            # Calculate component breakdown
            capex_component = total_capex / lifetime_throughput_mwh if lifetime_throughput_mwh > 0 else 0
            opex_component = total_opex_npv / lifetime_throughput_mwh if lifetime_throughput_mwh > 0 else 0
            replacement_component = replacement_cost_npv / lifetime_throughput_mwh if lifetime_throughput_mwh > 0 else 0
            financing_component = financing_cost / lifetime_throughput_mwh if lifetime_throughput_mwh > 0 else 0
            
            return LCOSResult(
                lcos_usd_per_mwh=lcos_usd_per_mwh,
                lcos_usd_per_kwh=lcos_usd_per_kwh,
                capex_component=capex_component,
                opex_component=opex_component,
                replacement_component=replacement_component,
                financing_component=financing_component,
                total_throughput_mwh=lifetime_throughput_mwh,
                effective_cycles=effective_cycles,
                end_of_life_capacity=end_of_life_capacity,
                average_efficiency=average_efficiency,
                total_capex=total_capex,
                total_opex_npv=total_opex_npv,
                replacement_cost_npv=replacement_cost_npv
            )
            
        except Exception as e:
            self.logger.error(f"LCOS calculation failed: {e}")
            raise
    
    def _calculate_total_capex(self, inputs: LCOSInputs) -> float:
        """Calculate total capital expenditure including incentives"""
        base_capex = inputs.capex_per_kwh * inputs.system_size_kwh
        
        # Apply federal ITC
        itc_benefit = base_capex * inputs.financing.federal_itc
        
        # Apply state rebate
        state_rebate = inputs.financing.state_rebate * inputs.system_size_kwh
        
        # Net CAPEX after incentives
        net_capex = base_capex - itc_benefit - state_rebate
        
        return max(0, net_capex)
    
    def _calculate_lifetime_throughput(self, inputs: LCOSInputs) -> float:
        """Calculate total lifetime energy throughput"""
        # Determine limiting factor: cycle life or calendar life
        cycle_limited_years = inputs.cycle_life / inputs.cycles_per_year
        actual_lifetime = min(cycle_limited_years, inputs.calendar_life_years)
        
        # Calculate annual throughput with degradation
        usable_capacity_kwh = inputs.system_size_kwh * inputs.depth_of_discharge
        annual_throughput_base = usable_capacity_kwh * inputs.cycles_per_year * inputs.round_trip_efficiency / 1000  # MWh
        
        total_throughput = 0.0
        discount_rate = inputs.financing.effective_discount_rate()
        
        for year in range(int(actual_lifetime)):
            # Apply capacity fade
            capacity_factor = max(0.5, 1.0 - (year * inputs.capacity_fade_per_year))
            
            # Apply efficiency degradation
            total_cycles = year * inputs.cycles_per_year
            efficiency_factor = max(0.7, inputs.round_trip_efficiency - (total_cycles * inputs.efficiency_fade_per_cycle))
            
            year_throughput = annual_throughput_base * capacity_factor * (efficiency_factor / inputs.round_trip_efficiency)
            
            # Discount to present value
            discounted_throughput = year_throughput / ((1 + discount_rate) ** year)
            total_throughput += discounted_throughput
        
        return total_throughput
    
    def _calculate_opex_npv(self, inputs: LCOSInputs) -> float:
        """Calculate net present value of operating expenses"""
        annual_fixed_om = inputs.fixed_om_per_kwh_year * inputs.system_size_kwh
        annual_variable_om = inputs.variable_om_per_cycle * inputs.cycles_per_year
        annual_opex = annual_fixed_om + annual_variable_om
        
        return self._calculate_npv_series(
            annual_opex,
            inputs.calendar_life_years,
            inputs.financing.effective_discount_rate(),
            inputs.financing.inflation_rate
        )
    
    def _calculate_replacement_cost(self, inputs: LCOSInputs) -> float:
        """Calculate NPV of battery replacement costs"""
        cycle_limited_years = inputs.cycle_life / inputs.cycles_per_year
        
        if cycle_limited_years < inputs.calendar_life_years:
            # Battery needs replacement during system life
            replacement_year = int(cycle_limited_years)
            replacement_cost = inputs.capex_per_kwh * inputs.system_size_kwh * 0.7  # Assume 30% cost reduction
            
            # Discount replacement cost to present value
            discount_rate = inputs.financing.effective_discount_rate()
            return replacement_cost / ((1 + discount_rate) ** replacement_year)
        
        return 0.0
    
    def _calculate_financing_cost(self, inputs: LCOSInputs, capex: float) -> float:
        """Calculate financing costs (interest on debt portion)"""
        debt_amount = capex * inputs.financing.debt_fraction
        annual_interest = debt_amount * inputs.financing.debt_interest_rate
        
        return self._calculate_npv_series(
            annual_interest,
            inputs.calendar_life_years,
            inputs.financing.effective_discount_rate(),
            0.0
        )
    
    def _calculate_effective_cycles(self, inputs: LCOSInputs) -> float:
        """Calculate effective number of cycles over lifetime"""
        cycle_limited_years = inputs.cycle_life / inputs.cycles_per_year
        actual_lifetime = min(cycle_limited_years, inputs.calendar_life_years)
        return actual_lifetime * inputs.cycles_per_year
    
    def _calculate_end_of_life_capacity(self, inputs: LCOSInputs) -> float:
        """Calculate remaining capacity at end of life"""
        cycle_limited_years = inputs.cycle_life / inputs.cycles_per_year
        actual_lifetime = min(cycle_limited_years, inputs.calendar_life_years)
        return max(0.5, 1.0 - (actual_lifetime * inputs.capacity_fade_per_year))
    
    def _calculate_average_efficiency(self, inputs: LCOSInputs) -> float:
        """Calculate average round-trip efficiency over lifetime"""
        cycle_limited_years = inputs.cycle_life / inputs.cycles_per_year
        actual_lifetime = min(cycle_limited_years, inputs.calendar_life_years)
        total_cycles = actual_lifetime * inputs.cycles_per_year
        
        end_efficiency = max(0.7, inputs.round_trip_efficiency - (total_cycles * inputs.efficiency_fade_per_cycle))
        return (inputs.round_trip_efficiency + end_efficiency) / 2
    
    def _calculate_npv_series(self, annual_amount: float, years: int,
                            discount_rate: float, inflation_rate: float) -> float:
        """Calculate NPV of an annual payment series with inflation"""
        npv = 0.0
        for year in range(years):
            inflated_amount = annual_amount * ((1 + inflation_rate) ** year)
            discounted_amount = inflated_amount / ((1 + discount_rate) ** year)
            npv += discounted_amount
        return npv
