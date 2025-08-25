"""
Data models for LCOE/LCOS calculations
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import numpy as np

class UseCase(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    UTILITY = "utility"

class TechnologyType(str, Enum):
    PV = "pv"
    BATTERY = "battery"
    WIND = "wind"
    HYDRO = "hydro"
    THERMAL = "thermal"

@dataclass
class FinancingParameters:
    """Financial parameters for LCOE/LCOS calculations"""
    discount_rate: float = 0.07  # Weighted Average Cost of Capital (WACC)
    inflation_rate: float = 0.025  # Annual inflation rate
    tax_rate: float = 0.21  # Corporate tax rate
    debt_fraction: float = 0.6  # Debt-to-equity ratio
    debt_interest_rate: float = 0.05  # Interest rate on debt
    
    # Incentives
    federal_itc: float = 0.30  # Federal Investment Tax Credit
    state_rebate: float = 0.0  # State rebate ($/kW or $/kWh)
    depreciation_schedule: List[float] = field(default_factory=lambda: [0.2, 0.32, 0.192, 0.1152, 0.1152, 0.0576])  # MACRS 5-year
    
    def effective_discount_rate(self) -> float:
        """Calculate effective discount rate considering tax benefits"""
        return self.discount_rate * (1 - self.tax_rate * self.debt_fraction)

@dataclass
class DegradationModel:
    """Performance degradation model over system lifetime"""
    annual_degradation_rate: float = 0.005  # 0.5% per year typical for solar
    degradation_type: str = "linear"  # "linear", "exponential", "step"
    step_years: List[int] = field(default_factory=list)  # For step degradation
    step_rates: List[float] = field(default_factory=list)  # Degradation at each step
    
    def performance_factor(self, year: int) -> float:
        """Calculate performance factor for given year"""
        if self.degradation_type == "linear":
            return max(0.0, 1.0 - (year * self.annual_degradation_rate))
        elif self.degradation_type == "exponential":
            return (1.0 - self.annual_degradation_rate) ** year
        elif self.degradation_type == "step":
            factor = 1.0
            for i, step_year in enumerate(self.step_years):
                if year >= step_year:
                    factor *= (1.0 - self.step_rates[i])
            return factor
        else:
            return 1.0

@dataclass
class LoadProfile:
    """Energy load profile for LCOS calculations"""
    annual_energy_kwh: float = 10000  # Annual energy consumption
    peak_demand_kw: float = 5.0  # Peak demand
    load_factor: float = 0.3  # Average load / peak load
    seasonal_variation: float = 0.2  # Seasonal load variation
    time_of_use_profile: Dict[str, float] = field(default_factory=dict)  # Hourly load profile
    
    def hourly_load_profile(self) -> np.ndarray:
        """Generate 8760-hour load profile"""
        if self.time_of_use_profile:
            # Use provided hourly profile
            return np.array(list(self.time_of_use_profile.values()))
        else:
            # Generate typical residential profile
            base_load = self.annual_energy_kwh / 8760
            hours = np.arange(8760)
            
            # Daily pattern (higher in evening)
            daily_pattern = 0.8 + 0.4 * np.sin(2 * np.pi * (hours % 24 - 18) / 24)
            
            # Seasonal pattern (higher in summer/winter)
            seasonal_pattern = 1.0 + self.seasonal_variation * np.sin(2 * np.pi * hours / 8760)
            
            return base_load * daily_pattern * seasonal_pattern

@dataclass
class LCOEInputs:
    """Input parameters for LCOE calculation"""
    # Capital costs
    capex_per_kw: float = 1500.0  # Capital expenditure per kW
    system_size_kw: float = 100.0  # System size in kW
    
    # Operating costs
    fixed_om_per_kw_year: float = 15.0  # Fixed O&M per kW per year
    variable_om_per_mwh: float = 0.0  # Variable O&M per MWh
    fuel_cost_per_mwh: float = 0.0  # Fuel cost per MWh (for thermal plants)
    
    # Performance
    capacity_factor: float = 0.25  # Annual capacity factor
    system_lifetime_years: int = 25  # System lifetime
    degradation: DegradationModel = field(default_factory=DegradationModel)
    
    # Financial
    financing: FinancingParameters = field(default_factory=FinancingParameters)
    
    # Technology specific
    technology_type: TechnologyType = TechnologyType.PV
    use_case: UseCase = UseCase.RESIDENTIAL

@dataclass
class LCOSInputs:
    """Input parameters for LCOS calculation"""
    # Capital costs
    capex_per_kwh: float = 400.0  # Capital expenditure per kWh
    system_size_kwh: float = 100.0  # System size in kWh
    power_rating_kw: float = 50.0  # Power rating in kW
    
    # Operating costs
    fixed_om_per_kwh_year: float = 5.0  # Fixed O&M per kWh per year
    variable_om_per_cycle: float = 0.01  # Variable O&M per cycle
    
    # Performance
    round_trip_efficiency: float = 0.90  # Round-trip efficiency
    cycles_per_year: float = 365.0  # Annual cycles
    cycle_life: int = 4000  # Total cycle life
    calendar_life_years: int = 15  # Calendar life
    depth_of_discharge: float = 0.90  # Usable capacity fraction
    
    # Degradation
    capacity_fade_per_year: float = 0.02  # Annual capacity fade
    efficiency_fade_per_cycle: float = 0.00001  # Efficiency fade per cycle
    
    # Financial
    financing: FinancingParameters = field(default_factory=FinancingParameters)
    
    # Load profile
    load_profile: LoadProfile = field(default_factory=LoadProfile)
    
    # Technology specific
    technology_type: TechnologyType = TechnologyType.BATTERY
    use_case: UseCase = UseCase.RESIDENTIAL

@dataclass
class LCOEResult:
    """Results from LCOE calculation"""
    lcoe_usd_per_mwh: float
    lcoe_usd_per_kwh: float
    
    # Cost breakdown
    capex_component: float
    opex_component: float
    fuel_component: float
    financing_component: float
    
    # Financial metrics
    total_capex: float
    total_opex_npv: float
    total_energy_mwh: float
    capacity_factor_actual: float
    
    # Sensitivity ranges (if calculated)
    p10_lcoe: Optional[float] = None
    p50_lcoe: Optional[float] = None
    p90_lcoe: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization"""
        return {
            "lcoe_usd_per_mwh": self.lcoe_usd_per_mwh,
            "lcoe_usd_per_kwh": self.lcoe_usd_per_kwh,
            "breakdown": {
                "capex": self.capex_component,
                "opex": self.opex_component,
                "fuel": self.fuel_component,
                "financing": self.financing_component
            },
            "metrics": {
                "total_capex": self.total_capex,
                "total_opex_npv": self.total_opex_npv,
                "total_energy_mwh": self.total_energy_mwh,
                "capacity_factor_actual": self.capacity_factor_actual
            },
            "sensitivity": {
                "p10": self.p10_lcoe,
                "p50": self.p50_lcoe,
                "p90": self.p90_lcoe
            }
        }

@dataclass
class LCOSResult:
    """Results from LCOS calculation"""
    lcos_usd_per_mwh: float
    lcos_usd_per_kwh: float
    
    # Cost breakdown
    capex_component: float
    opex_component: float
    replacement_component: float
    financing_component: float
    
    # Performance metrics
    total_throughput_mwh: float
    effective_cycles: float
    end_of_life_capacity: float
    average_efficiency: float
    
    # Financial metrics
    total_capex: float
    total_opex_npv: float
    replacement_cost_npv: float
    
    # Sensitivity ranges (if calculated)
    p10_lcos: Optional[float] = None
    p50_lcos: Optional[float] = None
    p90_lcos: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization"""
        return {
            "lcos_usd_per_mwh": self.lcos_usd_per_mwh,
            "lcos_usd_per_kwh": self.lcos_usd_per_kwh,
            "breakdown": {
                "capex": self.capex_component,
                "opex": self.opex_component,
                "replacement": self.replacement_component,
                "financing": self.financing_component
            },
            "performance": {
                "total_throughput_mwh": self.total_throughput_mwh,
                "effective_cycles": self.effective_cycles,
                "end_of_life_capacity": self.end_of_life_capacity,
                "average_efficiency": self.average_efficiency
            },
            "metrics": {
                "total_capex": self.total_capex,
                "total_opex_npv": self.total_opex_npv,
                "replacement_cost_npv": self.replacement_cost_npv
            },
            "sensitivity": {
                "p10": self.p10_lcos,
                "p50": self.p50_lcos,
                "p90": self.p90_lcos
            }
        }
