"""
Tesla-specific LCOE/LCOS calculators with product-specific parameters
"""

from typing import Dict, Any
from .core import LCOECalculator, LCOSCalculator
from .models import (
    LCOEInputs, LCOSInputs, LCOEResult, LCOSResult,
    FinancingParameters, DegradationModel, LoadProfile,
    TechnologyType, UseCase
)

class TeslaLCOECalculator(LCOECalculator):
    """Tesla-specific LCOE calculator for solar products"""
    
    def __init__(self):
        super().__init__()
        self.tesla_solar_specs = self._load_tesla_solar_specs()
    
    def _load_tesla_solar_specs(self) -> Dict[str, Dict[str, Any]]:
        """Load Tesla solar product specifications"""
        return {
            "solar_panels": {
                "capex_per_kw": 2500,  # Installed cost per kW
                "capacity_factor": {
                    "residential": 0.19,  # Typical residential CF
                    "commercial": 0.22,   # Commercial rooftop CF
                    "utility": 0.25       # Utility-scale CF
                },
                "degradation_rate": 0.004,  # 0.4% per year (better than industry average)
                "warranty_years": 25,
                "efficiency": 0.222,  # 22.2% module efficiency
                "fixed_om_per_kw_year": 12.0,  # Lower O&M due to fewer moving parts
            },
            "solar_roof": {
                "capex_per_kw": 4000,  # Higher cost due to integrated tiles
                "capacity_factor": {
                    "residential": 0.18,  # Slightly lower due to tile constraints
                },
                "degradation_rate": 0.004,
                "warranty_years": 25,
                "efficiency": 0.222,
                "fixed_om_per_kw_year": 8.0,  # Very low O&M - integrated design
            }
        }
    
    def calculate_tesla_solar_panels(self, system_size_kw: float, use_case: UseCase = UseCase.RESIDENTIAL,
                                   region: str = "CA", custom_params: Dict[str, Any] = None) -> LCOEResult:
        """Calculate LCOE for Tesla Solar Panels"""
        specs = self.tesla_solar_specs["solar_panels"]
        
        # Build inputs with Tesla-specific parameters
        inputs = LCOEInputs(
            capex_per_kw=specs["capex_per_kw"],
            system_size_kw=system_size_kw,
            fixed_om_per_kw_year=specs["fixed_om_per_kw_year"],
            variable_om_per_mwh=0.0,  # No variable O&M for solar
            fuel_cost_per_mwh=0.0,    # No fuel cost
            capacity_factor=specs["capacity_factor"].get(use_case.value, 0.19),
            system_lifetime_years=specs["warranty_years"],
            degradation=DegradationModel(annual_degradation_rate=specs["degradation_rate"]),
            technology_type=TechnologyType.PV,
            use_case=use_case
        )
        
        # Apply regional adjustments
        inputs = self._apply_regional_adjustments(inputs, region)
        
        # Apply custom parameters if provided
        if custom_params:
            for key, value in custom_params.items():
                if hasattr(inputs, key):
                    setattr(inputs, key, value)
        
        return self.calculate(inputs)
    
    def calculate_tesla_solar_roof(self, system_size_kw: float, roof_area_sqft: float,
                                 region: str = "CA", custom_params: Dict[str, Any] = None) -> LCOEResult:
        """Calculate LCOE for Tesla Solar Roof"""
        specs = self.tesla_solar_specs["solar_roof"]
        
        # Adjust cost based on roof complexity (more tiles needed)
        tile_coverage_ratio = system_size_kw * 1000 / (roof_area_sqft * 15)  # Assume 15W per sqft average
        complexity_multiplier = 1.0 + max(0, (1.0 - tile_coverage_ratio) * 0.5)
        
        inputs = LCOEInputs(
            capex_per_kw=specs["capex_per_kw"] * complexity_multiplier,
            system_size_kw=system_size_kw,
            fixed_om_per_kw_year=specs["fixed_om_per_kw_year"],
            variable_om_per_mwh=0.0,
            fuel_cost_per_mwh=0.0,
            capacity_factor=specs["capacity_factor"]["residential"],
            system_lifetime_years=specs["warranty_years"],
            degradation=DegradationModel(annual_degradation_rate=specs["degradation_rate"]),
            technology_type=TechnologyType.PV,
            use_case=UseCase.RESIDENTIAL
        )
        
        # Apply regional adjustments
        inputs = self._apply_regional_adjustments(inputs, region)
        
        # Apply custom parameters
        if custom_params:
            for key, value in custom_params.items():
                if hasattr(inputs, key):
                    setattr(inputs, key, value)
        
        return self.calculate(inputs)
    
    def _apply_regional_adjustments(self, inputs: LCOEInputs, region: str) -> LCOEInputs:
        """Apply regional adjustments for solar irradiance and costs"""
        regional_factors = {
            "CA": {"capacity_factor_mult": 1.1, "cost_mult": 1.2},   # High irradiance, high costs
            "TX": {"capacity_factor_mult": 1.05, "cost_mult": 0.9},  # Good irradiance, lower costs
            "FL": {"capacity_factor_mult": 1.0, "cost_mult": 1.0},   # Baseline
            "NY": {"capacity_factor_mult": 0.85, "cost_mult": 1.3},  # Lower irradiance, high costs
            "AZ": {"capacity_factor_mult": 1.2, "cost_mult": 0.95},  # Excellent irradiance
        }
        
        if region in regional_factors:
            factors = regional_factors[region]
            inputs.capacity_factor *= factors["capacity_factor_mult"]
            inputs.capex_per_kw *= factors["cost_mult"]
        
        return inputs

class TeslaLCOSCalculator(LCOSCalculator):
    """Tesla-specific LCOS calculator for energy storage products"""
    
    def __init__(self):
        super().__init__()
        self.tesla_battery_specs = self._load_tesla_battery_specs()
    
    def _load_tesla_battery_specs(self) -> Dict[str, Dict[str, Any]]:
        """Load Tesla battery product specifications"""
        return {
            "powerwall_3": {
                "capex_per_kwh": 800,  # Installed cost per kWh
                "power_rating_kw": 11.5,
                "usable_capacity_kwh": 13.5,
                "round_trip_efficiency": 0.975,  # 97.5% efficiency
                "cycle_life": 4000,
                "calendar_life_years": 10,
                "capacity_fade_per_year": 0.02,  # 2% per year
                "efficiency_fade_per_cycle": 0.000005,  # Very low efficiency fade
                "fixed_om_per_kwh_year": 3.0,
                "variable_om_per_cycle": 0.005,
                "depth_of_discharge": 1.0,  # 100% usable
            },
            "powerwall_2": {
                "capex_per_kwh": 700,  # Lower cost, older technology
                "power_rating_kw": 5.0,
                "usable_capacity_kwh": 13.5,
                "round_trip_efficiency": 0.90,  # 90% efficiency
                "cycle_life": 3650,  # 10 years daily cycling
                "calendar_life_years": 10,
                "capacity_fade_per_year": 0.025,  # 2.5% per year
                "efficiency_fade_per_cycle": 0.00001,
                "fixed_om_per_kwh_year": 4.0,
                "variable_om_per_cycle": 0.01,
                "depth_of_discharge": 1.0,
            },
            "megapack": {
                "capex_per_kwh": 300,  # Utility-scale economics
                "power_rating_kw": 1900,  # 1.9 MW
                "usable_capacity_kwh": 3900,  # 3.9 MWh
                "round_trip_efficiency": 0.92,  # 92% efficiency
                "cycle_life": 4000,
                "calendar_life_years": 20,
                "capacity_fade_per_year": 0.015,  # 1.5% per year
                "efficiency_fade_per_cycle": 0.000003,
                "fixed_om_per_kwh_year": 2.0,
                "variable_om_per_cycle": 0.002,
                "depth_of_discharge": 1.0,
            }
        }
    
    def calculate_powerwall_3(self, num_units: int = 1, use_case: UseCase = UseCase.RESIDENTIAL,
                            load_profile: LoadProfile = None, custom_params: Dict[str, Any] = None) -> LCOSResult:
        """Calculate LCOS for Tesla Powerwall 3"""
        specs = self.tesla_battery_specs["powerwall_3"]
        
        # Scale system based on number of units
        system_size_kwh = specs["usable_capacity_kwh"] * num_units
        power_rating_kw = specs["power_rating_kw"] * num_units
        
        # Default load profile if not provided
        if load_profile is None:
            load_profile = LoadProfile(
                annual_energy_kwh=system_size_kwh * 365,  # Daily cycling
                peak_demand_kw=power_rating_kw * 0.8,
                load_factor=0.3
            )
        
        inputs = LCOSInputs(
            capex_per_kwh=specs["capex_per_kwh"],
            system_size_kwh=system_size_kwh,
            power_rating_kw=power_rating_kw,
            fixed_om_per_kwh_year=specs["fixed_om_per_kwh_year"],
            variable_om_per_cycle=specs["variable_om_per_cycle"],
            round_trip_efficiency=specs["round_trip_efficiency"],
            cycles_per_year=365.0,  # Daily cycling
            cycle_life=specs["cycle_life"],
            calendar_life_years=specs["calendar_life_years"],
            depth_of_discharge=specs["depth_of_discharge"],
            capacity_fade_per_year=specs["capacity_fade_per_year"],
            efficiency_fade_per_cycle=specs["efficiency_fade_per_cycle"],
            load_profile=load_profile,
            technology_type=TechnologyType.BATTERY,
            use_case=use_case
        )
        
        # Apply custom parameters
        if custom_params:
            for key, value in custom_params.items():
                if hasattr(inputs, key):
                    setattr(inputs, key, value)
        
        return self.calculate(inputs)
    
    def calculate_powerwall_2(self, num_units: int = 1, use_case: UseCase = UseCase.RESIDENTIAL,
                            load_profile: LoadProfile = None, custom_params: Dict[str, Any] = None) -> LCOSResult:
        """Calculate LCOS for Tesla Powerwall 2"""
        specs = self.tesla_battery_specs["powerwall_2"]
        
        system_size_kwh = specs["usable_capacity_kwh"] * num_units
        power_rating_kw = specs["power_rating_kw"] * num_units
        
        if load_profile is None:
            load_profile = LoadProfile(
                annual_energy_kwh=system_size_kwh * 365,
                peak_demand_kw=power_rating_kw * 0.8,
                load_factor=0.3
            )
        
        inputs = LCOSInputs(
            capex_per_kwh=specs["capex_per_kwh"],
            system_size_kwh=system_size_kwh,
            power_rating_kw=power_rating_kw,
            fixed_om_per_kwh_year=specs["fixed_om_per_kwh_year"],
            variable_om_per_cycle=specs["variable_om_per_cycle"],
            round_trip_efficiency=specs["round_trip_efficiency"],
            cycles_per_year=365.0,
            cycle_life=specs["cycle_life"],
            calendar_life_years=specs["calendar_life_years"],
            depth_of_discharge=specs["depth_of_discharge"],
            capacity_fade_per_year=specs["capacity_fade_per_year"],
            efficiency_fade_per_cycle=specs["efficiency_fade_per_cycle"],
            load_profile=load_profile,
            technology_type=TechnologyType.BATTERY,
            use_case=use_case
        )
        
        if custom_params:
            for key, value in custom_params.items():
                if hasattr(inputs, key):
                    setattr(inputs, key, value)
        
        return self.calculate(inputs)
    
    def calculate_megapack(self, num_units: int = 1, cycles_per_year: float = 365.0,
                         custom_params: Dict[str, Any] = None) -> LCOSResult:
        """Calculate LCOS for Tesla Megapack"""
        specs = self.tesla_battery_specs["megapack"]
        
        system_size_kwh = specs["usable_capacity_kwh"] * num_units
        power_rating_kw = specs["power_rating_kw"] * num_units
        
        # Utility-scale load profile
        load_profile = LoadProfile(
            annual_energy_kwh=system_size_kwh * cycles_per_year,
            peak_demand_kw=power_rating_kw,
            load_factor=0.4  # Higher load factor for utility applications
        )
        
        inputs = LCOSInputs(
            capex_per_kwh=specs["capex_per_kwh"],
            system_size_kwh=system_size_kwh,
            power_rating_kw=power_rating_kw,
            fixed_om_per_kwh_year=specs["fixed_om_per_kwh_year"],
            variable_om_per_cycle=specs["variable_om_per_cycle"],
            round_trip_efficiency=specs["round_trip_efficiency"],
            cycles_per_year=cycles_per_year,
            cycle_life=specs["cycle_life"],
            calendar_life_years=specs["calendar_life_years"],
            depth_of_discharge=specs["depth_of_discharge"],
            capacity_fade_per_year=specs["capacity_fade_per_year"],
            efficiency_fade_per_cycle=specs["efficiency_fade_per_cycle"],
            load_profile=load_profile,
            technology_type=TechnologyType.BATTERY,
            use_case=UseCase.UTILITY
        )
        
        if custom_params:
            for key, value in custom_params.items():
                if hasattr(inputs, key):
                    setattr(inputs, key, value)
        
        return self.calculate(inputs)
    
    def calculate_backup_hours(self, battery_kwh: float, load_kw: float, 
                             efficiency: float = 0.95) -> float:
        """Calculate backup hours for Tesla battery systems"""
        return (battery_kwh * efficiency) / load_kw if load_kw > 0 else 0
    
    def calculate_solar_plus_storage(self, solar_kw: float, battery_kwh: float,
                                   region: str = "CA", use_case: UseCase = UseCase.RESIDENTIAL) -> Dict[str, Any]:
        """Calculate combined LCOE for Tesla solar + storage system"""
        # Calculate solar LCOE
        tesla_lcoe_calc = TeslaLCOECalculator()
        solar_result = tesla_lcoe_calc.calculate_tesla_solar_panels(solar_kw, use_case, region)
        
        # Calculate storage LCOS (assuming Powerwall 3)
        num_powerwalls = max(1, int(battery_kwh / 13.5))
        storage_result = self.calculate_powerwall_3(num_powerwalls, use_case)
        
        # Combined system metrics
        total_capex = solar_result.total_capex + storage_result.total_capex
        combined_lcoe = (solar_result.lcoe_usd_per_kwh + storage_result.lcos_usd_per_kwh) / 2
        
        return {
            "solar_lcoe": solar_result.to_dict(),
            "storage_lcos": storage_result.to_dict(),
            "combined_metrics": {
                "total_capex": total_capex,
                "combined_lcoe_kwh": combined_lcoe,
                "backup_hours": self.calculate_backup_hours(battery_kwh, 5.0),  # Assume 5kW load
                "solar_kw": solar_kw,
                "battery_kwh": battery_kwh
            }
        }
