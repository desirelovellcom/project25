"""
Scenario builders for different use cases and regions
"""

from typing import Dict, Any, List
from .models import (
    LCOEInputs, LCOSInputs, FinancingParameters, DegradationModel, 
    LoadProfile, UseCase, TechnologyType
)

class ScenarioBuilder:
    """Builds standardized scenarios for LCOE/LCOS analysis"""
    
    def __init__(self):
        self.regional_data = self._load_regional_data()
        self.use_case_profiles = self._load_use_case_profiles()
    
    def _load_regional_data(self) -> Dict[str, Dict[str, Any]]:
        """Load regional cost and performance data"""
        return {
            "CA": {  # California
                "solar_irradiance_factor": 1.1,
                "cost_multiplier": 1.2,
                "incentives": {
                    "federal_itc": 0.30,
                    "state_rebate": 1000,  # $/kW
                    "net_metering": True
                },
                "electricity_rate": 0.25,  # $/kWh
                "peak_demand_charge": 15.0  # $/kW-month
            },
            "TX": {  # Texas
                "solar_irradiance_factor": 1.05,
                "cost_multiplier": 0.9,
                "incentives": {
                    "federal_itc": 0.30,
                    "state_rebate": 0,
                    "net_metering": False
                },
                "electricity_rate": 0.12,
                "peak_demand_charge": 10.0
            },
            "FL": {  # Florida
                "solar_irradiance_factor": 1.0,
                "cost_multiplier": 1.0,
                "incentives": {
                    "federal_itc": 0.30,
                    "state_rebate": 0,
                    "net_metering": True
                },
                "electricity_rate": 0.13,
                "peak_demand_charge": 8.0
            },
            "NY": {  # New York
                "solar_irradiance_factor": 0.85,
                "cost_multiplier": 1.3,
                "incentives": {
                    "federal_itc": 0.30,
                    "state_rebate": 1500,
                    "net_metering": True
                },
                "electricity_rate": 0.20,
                "peak_demand_charge": 18.0
            },
            "AZ": {  # Arizona
                "solar_irradiance_factor": 1.2,
                "cost_multiplier": 0.95,
                "incentives": {
                    "federal_itc": 0.30,
                    "state_rebate": 0,
                    "net_metering": True
                },
                "electricity_rate": 0.14,
                "peak_demand_charge": 12.0
            }
        }
    
    def _load_use_case_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Load typical profiles for different use cases"""
        return {
            "residential": {
                "typical_size_kw": 7.0,
                "capacity_factor": 0.19,
                "load_profile": {
                    "annual_energy_kwh": 10000,
                    "peak_demand_kw": 5.0,
                    "load_factor": 0.3
                },
                "financing": {
                    "discount_rate": 0.06,
                    "debt_fraction": 0.8,
                    "debt_interest_rate": 0.04
                }
            },
            "commercial": {
                "typical_size_kw": 100.0,
                "capacity_factor": 0.22,
                "load_profile": {
                    "annual_energy_kwh": 150000,
                    "peak_demand_kw": 75.0,
                    "load_factor": 0.4
                },
                "financing": {
                    "discount_rate": 0.08,
                    "debt_fraction": 0.7,
                    "debt_interest_rate": 0.05
                }
            },
            "utility": {
                "typical_size_kw": 50000.0,
                "capacity_factor": 0.25,
                "load_profile": {
                    "annual_energy_kwh": 100000000,
                    "peak_demand_kw": 40000.0,
                    "load_factor": 0.5
                },
                "financing": {
                    "discount_rate": 0.07,
                    "debt_fraction": 0.6,
                    "debt_interest_rate": 0.04
                }
            }
        }
    
    def build_lcoe_scenario(self, use_case: UseCase, region: str = "CA",
                           technology: TechnologyType = TechnologyType.PV,
                           custom_params: Dict[str, Any] = None) -> LCOEInputs:
        """Build LCOE scenario for given use case and region"""
        
        # Get base parameters
        use_case_data = self.use_case_profiles[use_case.value]
        regional_data = self.regional_data.get(region, self.regional_data["CA"])
        
        # Build financing parameters
        financing = FinancingParameters(
            discount_rate=use_case_data["financing"]["discount_rate"],
            debt_fraction=use_case_data["financing"]["debt_fraction"],
            debt_interest_rate=use_case_data["financing"]["debt_interest_rate"],
            federal_itc=regional_data["incentives"]["federal_itc"],
            state_rebate=regional_data["incentives"]["state_rebate"]
        )
        
        # Technology-specific parameters
        if technology == TechnologyType.PV:
            capex_per_kw = 2000 * regional_data["cost_multiplier"]
            capacity_factor = use_case_data["capacity_factor"] * regional_data["solar_irradiance_factor"]
            fixed_om = 15.0
            variable_om = 0.0
            fuel_cost = 0.0
            lifetime = 25
            degradation = DegradationModel(annual_degradation_rate=0.005)
        
        elif technology == TechnologyType.WIND:
            capex_per_kw = 1500 * regional_data["cost_multiplier"]
            capacity_factor = 0.35  # Typical wind capacity factor
            fixed_om = 25.0
            variable_om = 5.0
            fuel_cost = 0.0
            lifetime = 20
            degradation = DegradationModel(annual_degradation_rate=0.002)
        
        else:  # Default to solar
            capex_per_kw = 2000 * regional_data["cost_multiplier"]
            capacity_factor = use_case_data["capacity_factor"] * regional_data["solar_irradiance_factor"]
            fixed_om = 15.0
            variable_om = 0.0
            fuel_cost = 0.0
            lifetime = 25
            degradation = DegradationModel(annual_degradation_rate=0.005)
        
        # Create inputs
        inputs = LCOEInputs(
            capex_per_kw=capex_per_kw,
            system_size_kw=use_case_data["typical_size_kw"],
            fixed_om_per_kw_year=fixed_om,
            variable_om_per_mwh=variable_om,
            fuel_cost_per_mwh=fuel_cost,
            capacity_factor=capacity_factor,
            system_lifetime_years=lifetime,
            degradation=degradation,
            financing=financing,
            technology_type=technology,
            use_case=use_case
        )
        
        # Apply custom parameters
        if custom_params:
            for key, value in custom_params.items():
                if hasattr(inputs, key):
                    setattr(inputs, key, value)
        
        return inputs
    
    def build_lcos_scenario(self, use_case: UseCase, region: str = "CA",
                           technology: TechnologyType = TechnologyType.BATTERY,
                           custom_params: Dict[str, Any] = None) -> LCOSInputs:
        """Build LCOS scenario for given use case and region"""
        
        use_case_data = self.use_case_profiles[use_case.value]
        regional_data = self.regional_data.get(region, self.regional_data["CA"])
        
        # Build financing parameters
        financing = FinancingParameters(
            discount_rate=use_case_data["financing"]["discount_rate"],
            debt_fraction=use_case_data["financing"]["debt_fraction"],
            debt_interest_rate=use_case_data["financing"]["debt_interest_rate"],
            federal_itc=regional_data["incentives"]["federal_itc"],
            state_rebate=regional_data["incentives"]["state_rebate"]
        )
        
        # Build load profile
        load_profile = LoadProfile(
            annual_energy_kwh=use_case_data["load_profile"]["annual_energy_kwh"],
            peak_demand_kw=use_case_data["load_profile"]["peak_demand_kw"],
            load_factor=use_case_data["load_profile"]["load_factor"]
        )
        
        # Use case specific battery sizing
        if use_case == UseCase.RESIDENTIAL:
            system_size_kwh = 13.5  # Typical Powerwall size
            power_rating_kw = 5.0
            capex_per_kwh = 800 * regional_data["cost_multiplier"]
            cycles_per_year = 365
        elif use_case == UseCase.COMMERCIAL:
            system_size_kwh = 100.0
            power_rating_kw = 50.0
            capex_per_kwh = 600 * regional_data["cost_multiplier"]
            cycles_per_year = 300
        else:  # Utility
            system_size_kwh = 1000.0
            power_rating_kw = 500.0
            capex_per_kwh = 400 * regional_data["cost_multiplier"]
            cycles_per_year = 250
        
        inputs = LCOSInputs(
            capex_per_kwh=capex_per_kwh,
            system_size_kwh=system_size_kwh,
            power_rating_kw=power_rating_kw,
            fixed_om_per_kwh_year=5.0,
            variable_om_per_cycle=0.01,
            round_trip_efficiency=0.90,
            cycles_per_year=cycles_per_year,
            cycle_life=4000,
            calendar_life_years=15,
            depth_of_discharge=0.90,
            capacity_fade_per_year=0.02,
            efficiency_fade_per_cycle=0.00001,
            financing=financing,
            load_profile=load_profile,
            technology_type=technology,
            use_case=use_case
        )
        
        # Apply custom parameters
        if custom_params:
            for key, value in custom_params.items():
                if hasattr(inputs, key):
                    setattr(inputs, key, value)
        
        return inputs

class TeslaScenarioBuilder(ScenarioBuilder):
    """Tesla-specific scenario builder with product defaults"""
    
    def build_powerwall_scenario(self, region: str = "CA", num_units: int = 1,
                                custom_params: Dict[str, Any] = None) -> LCOSInputs:
        """Build scenario for Tesla Powerwall"""
        base_scenario = self.build_lcos_scenario(UseCase.RESIDENTIAL, region)
        
        # Tesla Powerwall 3 specifications
        base_scenario.capex_per_kwh = 800
        base_scenario.system_size_kwh = 13.5 * num_units
        base_scenario.power_rating_kw = 11.5 * num_units
        base_scenario.round_trip_efficiency = 0.975
        base_scenario.cycle_life = 4000
        base_scenario.calendar_life_years = 10
        base_scenario.capacity_fade_per_year = 0.02
        base_scenario.efficiency_fade_per_cycle = 0.000005
        base_scenario.depth_of_discharge = 1.0
        
        if custom_params:
            for key, value in custom_params.items():
                if hasattr(base_scenario, key):
                    setattr(base_scenario, key, value)
        
        return base_scenario
    
    def build_solar_panel_scenario(self, region: str = "CA", system_size_kw: float = 7.0,
                                  custom_params: Dict[str, Any] = None) -> LCOEInputs:
        """Build scenario for Tesla Solar Panels"""
        base_scenario = self.build_lcoe_scenario(UseCase.RESIDENTIAL, region)
        
        # Tesla Solar Panel specifications
        base_scenario.capex_per_kw = 2500
        base_scenario.system_size_kw = system_size_kw
        base_scenario.fixed_om_per_kw_year = 12.0
        base_scenario.degradation = DegradationModel(annual_degradation_rate=0.004)
        base_scenario.system_lifetime_years = 25
        
        if custom_params:
            for key, value in custom_params.items():
                if hasattr(base_scenario, key):
                    setattr(base_scenario, key, value)
        
        return base_scenario
    
    def build_solar_roof_scenario(self, region: str = "CA", system_size_kw: float = 10.0,
                                 roof_complexity: float = 1.0, custom_params: Dict[str, Any] = None) -> LCOEInputs:
        """Build scenario for Tesla Solar Roof"""
        base_scenario = self.build_lcoe_scenario(UseCase.RESIDENTIAL, region)
        
        # Tesla Solar Roof specifications (higher cost due to integrated tiles)
        base_scenario.capex_per_kw = 4000 * roof_complexity
        base_scenario.system_size_kw = system_size_kw
        base_scenario.fixed_om_per_kw_year = 8.0  # Lower O&M due to integrated design
        base_scenario.degradation = DegradationModel(annual_degradation_rate=0.004)
        base_scenario.system_lifetime_years = 25
        
        if custom_params:
            for key, value in custom_params.items():
                if hasattr(base_scenario, key):
                    setattr(base_scenario, key, value)
        
        return base_scenario
