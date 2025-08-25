"""
Unit normalization and conversion utilities
"""

import re
import logging
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class NormalizedValue:
    """Represents a normalized value with standard unit"""
    value: float
    unit: str
    original_value: float
    original_unit: str
    conversion_factor: float

class UnitNormalizer:
    """Normalizes units to standard forms for consistent analysis"""
    
    def __init__(self):
        self.conversion_factors = self._load_conversion_factors()
        self.unit_aliases = self._load_unit_aliases()
    
    def _load_conversion_factors(self) -> Dict[str, Dict[str, float]]:
        """Load conversion factors for different unit types"""
        return {
            "energy": {
                "Wh": 0.001,      # Wh to kWh
                "kWh": 1.0,       # kWh (base unit)
                "MWh": 1000.0,    # MWh to kWh
                "GWh": 1000000.0, # GWh to kWh
                "J": 2.78e-7,     # Joules to kWh
                "kJ": 2.78e-4,    # kJ to kWh
                "MJ": 0.278,      # MJ to kWh
                "BTU": 2.93e-4,   # BTU to kWh
                "kBTU": 0.293,    # kBTU to kWh
            },
            "power": {
                "W": 0.001,       # W to kW
                "kW": 1.0,        # kW (base unit)
                "MW": 1000.0,     # MW to kW
                "GW": 1000000.0,  # GW to kW
                "hp": 0.746,      # Horsepower to kW
                "BTU/h": 2.93e-4, # BTU/h to kW
            },
            "currency": {
                "USD": 1.0,       # USD (base unit)
                "cents": 0.01,    # cents to USD
                "¢": 0.01,        # cents symbol to USD
            },
            "time": {
                "s": 1.0/3600,    # seconds to hours
                "min": 1.0/60,    # minutes to hours
                "h": 1.0,         # hours (base unit)
                "hr": 1.0,        # hours variant
                "hours": 1.0,     # hours spelled out
                "d": 24.0,        # days to hours
                "days": 24.0,     # days spelled out
                "y": 8760.0,      # years to hours
                "yr": 8760.0,     # years variant
                "years": 8760.0,  # years spelled out
            },
            "percentage": {
                "%": 1.0,         # percent (base unit)
                "percent": 1.0,   # percent spelled out
                "pct": 1.0,       # percent abbreviated
            },
            "cycles": {
                "cycles": 1.0,    # cycles (base unit)
                "cycle": 1.0,     # cycle singular
            },
            "area": {
                "m²": 1.0,        # square meters (base unit)
                "m2": 1.0,        # square meters variant
                "ft²": 0.092903,  # square feet to m²
                "ft2": 0.092903,  # square feet variant
                "sqft": 0.092903, # square feet abbreviated
            }
        }
    
    def _load_unit_aliases(self) -> Dict[str, str]:
        """Load unit aliases and common variations"""
        return {
            # Energy aliases
            "kilowatt-hour": "kWh",
            "kilowatt-hours": "kWh",
            "kilowatthour": "kWh",
            "kilowatthours": "kWh",
            "kwh": "kWh",
            "KWH": "kWh",
            "megawatt-hour": "MWh",
            "megawatt-hours": "MWh",
            "mwh": "MWh",
            "MWH": "MWh",
            
            # Power aliases
            "kilowatt": "kW",
            "kilowatts": "kW",
            "kw": "kW",
            "KW": "kW",
            "megawatt": "MW",
            "megawatts": "MW",
            "mw": "MW",
            "MW": "MW",
            "watt": "W",
            "watts": "W",
            
            # Currency aliases
            "dollar": "USD",
            "dollars": "USD",
            "$": "USD",
            "usd": "USD",
            
            # Time aliases
            "hour": "h",
            "hrs": "h",
            "year": "years",
            "yrs": "years",
            
            # Percentage aliases
            "percentage": "%",
            "pct": "%",
        }
    
    def normalize_unit(self, value: float, unit: str) -> Optional[NormalizedValue]:
        """Normalize a value and unit to standard form"""
        try:
            # Clean and standardize the unit string
            clean_unit = self._clean_unit_string(unit)
            
            # Apply aliases
            if clean_unit in self.unit_aliases:
                clean_unit = self.unit_aliases[clean_unit]
            
            # Find the unit category and conversion factor
            unit_category, conversion_factor = self._find_conversion_factor(clean_unit)
            
            if unit_category and conversion_factor is not None:
                # Get the base unit for this category
                base_unit = self._get_base_unit(unit_category)
                
                # Convert to base unit
                normalized_value = value * conversion_factor
                
                return NormalizedValue(
                    value=normalized_value,
                    unit=base_unit,
                    original_value=value,
                    original_unit=unit,
                    conversion_factor=conversion_factor
                )
            
            logger.warning(f"Unknown unit: {unit}")
            return None
            
        except Exception as e:
            logger.error(f"Error normalizing unit {unit}: {e}")
            return None
    
    def _clean_unit_string(self, unit: str) -> str:
        """Clean and standardize unit string"""
        # Remove extra whitespace and convert to standard case
        clean = unit.strip()
        
        # Handle common formatting issues
        clean = re.sub(r'\s+', '', clean)  # Remove internal spaces
        clean = re.sub(r'[^\w%²²/\-\$¢]', '', clean)  # Keep only alphanumeric and unit chars
        
        return clean
    
    def _find_conversion_factor(self, unit: str) -> Tuple[Optional[str], Optional[float]]:
        """Find the conversion factor for a unit"""
        for category, factors in self.conversion_factors.items():
            if unit in factors:
                return category, factors[unit]
        return None, None
    
    def _get_base_unit(self, category: str) -> str:
        """Get the base unit for a category"""
        base_units = {
            "energy": "kWh",
            "power": "kW", 
            "currency": "USD",
            "time": "h",
            "percentage": "%",
            "cycles": "cycles",
            "area": "m²"
        }
        return base_units.get(category, "unknown")
    
    def normalize_price_per_unit(self, price: float, price_unit: str, 
                                per_value: float, per_unit: str) -> Optional[Dict[str, any]]:
        """Normalize price per unit expressions (e.g., $/kWh, ¢/kWh)"""
        try:
            # Normalize price
            norm_price = self.normalize_unit(price, price_unit)
            if not norm_price:
                return None
            
            # Normalize the "per" unit
            norm_per = self.normalize_unit(per_value, per_unit)
            if not norm_per:
                return None
            
            # Calculate normalized price per unit
            normalized_rate = norm_price.value / norm_per.value
            
            return {
                "rate": normalized_rate,
                "unit": f"{norm_price.unit}/{norm_per.unit}",
                "original_rate": price / per_value,
                "original_unit": f"{price_unit}/{per_unit}"
            }
            
        except Exception as e:
            logger.error(f"Error normalizing price per unit: {e}")
            return None
    
    def convert_energy_to_power_cost(self, energy_cost_per_kwh: float, 
                                   capacity_kwh: float, lifetime_hours: float) -> float:
        """Convert energy cost ($/kWh) to power cost ($/kW) for LCOE calculations"""
        try:
            # Total energy over lifetime
            total_energy_kwh = capacity_kwh * (lifetime_hours / 8760)  # Assuming annual cycles
            
            # Total cost over lifetime
            total_cost = energy_cost_per_kwh * total_energy_kwh
            
            # Cost per kW of capacity
            cost_per_kw = total_cost / capacity_kwh if capacity_kwh > 0 else 0
            
            return cost_per_kw
            
        except Exception as e:
            logger.error(f"Error converting energy to power cost: {e}")
            return 0.0
