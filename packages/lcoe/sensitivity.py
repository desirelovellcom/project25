"""
Sensitivity analysis and Monte Carlo simulation for LCOE/LCOS
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from scipy.stats import norm, uniform, triangular
from .core import LCOECalculator, LCOSCalculator
from .models import LCOEInputs, LCOSInputs, LCOEResult, LCOSResult

logger = logging.getLogger(__name__)

@dataclass
class ParameterDistribution:
    """Defines probability distribution for a parameter"""
    name: str
    distribution_type: str  # 'normal', 'uniform', 'triangular'
    base_value: float
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    std_dev: Optional[float] = None
    mode_value: Optional[float] = None  # For triangular distribution

@dataclass
class SensitivityResult:
    """Results from sensitivity analysis"""
    parameter_name: str
    base_value: float
    low_value: float
    high_value: float
    base_result: float
    low_result: float
    high_result: float
    sensitivity: float  # (high_result - low_result) / (high_value - low_value)
    elasticity: float   # % change in result / % change in parameter

@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation"""
    mean: float
    std_dev: float
    p10: float
    p25: float
    p50: float  # median
    p75: float
    p90: float
    min_value: float
    max_value: float
    samples: np.ndarray
    parameter_correlations: Dict[str, float]

class SensitivityAnalyzer:
    """Performs sensitivity analysis on LCOE/LCOS calculations"""
    
    def __init__(self):
        self.logger = logger
    
    def analyze_lcoe_sensitivity(self, base_inputs: LCOEInputs, 
                                parameters: List[str] = None,
                                variation_percent: float = 0.2) -> List[SensitivityResult]:
        """Perform sensitivity analysis on LCOE parameters"""
        if parameters is None:
            parameters = [
                'capex_per_kw', 'capacity_factor', 'system_lifetime_years',
                'fixed_om_per_kw_year', 'financing.discount_rate'
            ]
        
        calculator = LCOECalculator()
        base_result = calculator.calculate(base_inputs)
        base_lcoe = base_result.lcoe_usd_per_kwh
        
        sensitivity_results = []
        
        for param in parameters:
            try:
                # Get base parameter value
                base_value = self._get_nested_attribute(base_inputs, param)
                
                # Calculate low and high values
                low_value = base_value * (1 - variation_percent)
                high_value = base_value * (1 + variation_percent)
                
                # Calculate LCOE with low value
                low_inputs = self._copy_inputs_with_param(base_inputs, param, low_value)
                low_result = calculator.calculate(low_inputs)
                low_lcoe = low_result.lcoe_usd_per_kwh
                
                # Calculate LCOE with high value
                high_inputs = self._copy_inputs_with_param(base_inputs, param, high_value)
                high_result = calculator.calculate(high_inputs)
                high_lcoe = high_result.lcoe_usd_per_kwh
                
                # Calculate sensitivity metrics
                sensitivity = (high_lcoe - low_lcoe) / (high_value - low_value) if high_value != low_value else 0
                elasticity = ((high_lcoe - low_lcoe) / base_lcoe) / ((high_value - low_value) / base_value) if base_value != 0 and base_lcoe != 0 else 0
                
                sensitivity_results.append(SensitivityResult(
                    parameter_name=param,
                    base_value=base_value,
                    low_value=low_value,
                    high_value=high_value,
                    base_result=base_lcoe,
                    low_result=low_lcoe,
                    high_result=high_lcoe,
                    sensitivity=sensitivity,
                    elasticity=elasticity
                ))
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze sensitivity for parameter {param}: {e}")
        
        # Sort by absolute elasticity (most sensitive first)
        sensitivity_results.sort(key=lambda x: abs(x.elasticity), reverse=True)
        
        return sensitivity_results
    
    def analyze_lcos_sensitivity(self, base_inputs: LCOSInputs,
                                parameters: List[str] = None,
                                variation_percent: float = 0.2) -> List[SensitivityResult]:
        """Perform sensitivity analysis on LCOS parameters"""
        if parameters is None:
            parameters = [
                'capex_per_kwh', 'round_trip_efficiency', 'cycle_life',
                'cycles_per_year', 'capacity_fade_per_year', 'financing.discount_rate'
            ]
        
        calculator = LCOSCalculator()
        base_result = calculator.calculate(base_inputs)
        base_lcos = base_result.lcos_usd_per_kwh
        
        sensitivity_results = []
        
        for param in parameters:
            try:
                base_value = self._get_nested_attribute(base_inputs, param)
                low_value = base_value * (1 - variation_percent)
                high_value = base_value * (1 + variation_percent)
                
                low_inputs = self._copy_inputs_with_param(base_inputs, param, low_value)
                low_result = calculator.calculate(low_inputs)
                low_lcos = low_result.lcos_usd_per_kwh
                
                high_inputs = self._copy_inputs_with_param(base_inputs, param, high_value)
                high_result = calculator.calculate(high_inputs)
                high_lcos = high_result.lcos_usd_per_kwh
                
                sensitivity = (high_lcos - low_lcos) / (high_value - low_value) if high_value != low_value else 0
                elasticity = ((high_lcos - low_lcos) / base_lcos) / ((high_value - low_value) / base_value) if base_value != 0 and base_lcos != 0 else 0
                
                sensitivity_results.append(SensitivityResult(
                    parameter_name=param,
                    base_value=base_value,
                    low_value=low_value,
                    high_value=high_value,
                    base_result=base_lcos,
                    low_result=low_lcos,
                    high_result=high_lcos,
                    sensitivity=sensitivity,
                    elasticity=elasticity
                ))
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze sensitivity for parameter {param}: {e}")
        
        sensitivity_results.sort(key=lambda x: abs(x.elasticity), reverse=True)
        return sensitivity_results
    
    def _get_nested_attribute(self, obj: Any, attr_path: str) -> Any:
        """Get nested attribute value using dot notation"""
        attrs = attr_path.split('.')
        value = obj
        for attr in attrs:
            value = getattr(value, attr)
        return value
    
    def _copy_inputs_with_param(self, inputs: Any, param_path: str, new_value: Any) -> Any:
        """Create copy of inputs with modified parameter"""
        import copy
        new_inputs = copy.deepcopy(inputs)
        
        attrs = param_path.split('.')
        obj = new_inputs
        for attr in attrs[:-1]:
            obj = getattr(obj, attr)
        setattr(obj, attrs[-1], new_value)
        
        return new_inputs

class MonteCarloAnalyzer:
    """Performs Monte Carlo simulation for uncertainty analysis"""
    
    def __init__(self, n_samples: int = 10000):
        self.n_samples = n_samples
        self.logger = logger
    
    def analyze_lcoe_uncertainty(self, base_inputs: LCOEInputs,
                                parameter_distributions: List[ParameterDistribution]) -> MonteCarloResult:
        """Perform Monte Carlo analysis on LCOE"""
        calculator = LCOECalculator()
        
        # Generate parameter samples
        parameter_samples = self._generate_parameter_samples(parameter_distributions)
        
        # Calculate LCOE for each sample
        lcoe_samples = []
        
        for i in range(self.n_samples):
            try:
                # Create inputs with sampled parameters
                sample_inputs = self._create_sample_inputs(base_inputs, parameter_distributions, parameter_samples, i)
                
                # Calculate LCOE
                result = calculator.calculate(sample_inputs)
                lcoe_samples.append(result.lcoe_usd_per_kwh)
                
            except Exception as e:
                self.logger.warning(f"Failed to calculate LCOE for sample {i}: {e}")
                lcoe_samples.append(np.nan)
        
        # Remove NaN values
        lcoe_samples = np.array(lcoe_samples)
        lcoe_samples = lcoe_samples[~np.isnan(lcoe_samples)]
        
        if len(lcoe_samples) == 0:
            raise ValueError("No valid LCOE samples generated")
        
        # Calculate statistics
        return self._calculate_monte_carlo_stats(lcoe_samples, parameter_distributions, parameter_samples)
    
    def analyze_lcos_uncertainty(self, base_inputs: LCOSInputs,
                                parameter_distributions: List[ParameterDistribution]) -> MonteCarloResult:
        """Perform Monte Carlo analysis on LCOS"""
        calculator = LCOSCalculator()
        
        parameter_samples = self._generate_parameter_samples(parameter_distributions)
        lcos_samples = []
        
        for i in range(self.n_samples):
            try:
                sample_inputs = self._create_sample_inputs(base_inputs, parameter_distributions, parameter_samples, i)
                result = calculator.calculate(sample_inputs)
                lcos_samples.append(result.lcos_usd_per_kwh)
            except Exception as e:
                self.logger.warning(f"Failed to calculate LCOS for sample {i}: {e}")
                lcos_samples.append(np.nan)
        
        lcos_samples = np.array(lcos_samples)
        lcos_samples = lcos_samples[~np.isnan(lcos_samples)]
        
        if len(lcos_samples) == 0:
            raise ValueError("No valid LCOS samples generated")
        
        return self._calculate_monte_carlo_stats(lcos_samples, parameter_distributions, parameter_samples)
    
    def _generate_parameter_samples(self, distributions: List[ParameterDistribution]) -> Dict[str, np.ndarray]:
        """Generate random samples for each parameter distribution"""
        samples = {}
        
        for dist in distributions:
            if dist.distribution_type == 'normal':
                if dist.std_dev is None:
                    # Use 10% of base value as standard deviation
                    std_dev = dist.base_value * 0.1
                else:
                    std_dev = dist.std_dev
                
                samples[dist.name] = np.random.normal(dist.base_value, std_dev, self.n_samples)
                
            elif dist.distribution_type == 'uniform':
                min_val = dist.min_value if dist.min_value is not None else dist.base_value * 0.8
                max_val = dist.max_value if dist.max_value is not None else dist.base_value * 1.2
                
                samples[dist.name] = np.random.uniform(min_val, max_val, self.n_samples)
                
            elif dist.distribution_type == 'triangular':
                min_val = dist.min_value if dist.min_value is not None else dist.base_value * 0.8
                max_val = dist.max_value if dist.max_value is not None else dist.base_value * 1.2
                mode_val = dist.mode_value if dist.mode_value is not None else dist.base_value
                
                samples[dist.name] = np.random.triangular(min_val, mode_val, max_val, self.n_samples)
            
            else:
                # Default to base value if distribution type unknown
                samples[dist.name] = np.full(self.n_samples, dist.base_value)
        
        return samples
    
    def _create_sample_inputs(self, base_inputs: Any, distributions: List[ParameterDistribution],
                            parameter_samples: Dict[str, np.ndarray], sample_index: int) -> Any:
        """Create input object with sampled parameter values"""
        import copy
        sample_inputs = copy.deepcopy(base_inputs)
        
        for dist in distributions:
            sample_value = parameter_samples[dist.name][sample_index]
            
            # Set the parameter value using dot notation
            attrs = dist.name.split('.')
            obj = sample_inputs
            for attr in attrs[:-1]:
                obj = getattr(obj, attr)
            setattr(obj, attrs[-1], sample_value)
        
        return sample_inputs
    
    def _calculate_monte_carlo_stats(self, samples: np.ndarray, 
                                   distributions: List[ParameterDistribution],
                                   parameter_samples: Dict[str, np.ndarray]) -> MonteCarloResult:
        """Calculate statistics from Monte Carlo samples"""
        # Calculate correlations between parameters and results
        correlations = {}
        for dist in distributions:
            param_samples = parameter_samples[dist.name][:len(samples)]  # Match sample length
            correlation = np.corrcoef(param_samples, samples)[0, 1]
            correlations[dist.name] = correlation if not np.isnan(correlation) else 0.0
        
        return MonteCarloResult(
            mean=np.mean(samples),
            std_dev=np.std(samples),
            p10=np.percentile(samples, 10),
            p25=np.percentile(samples, 25),
            p50=np.percentile(samples, 50),
            p75=np.percentile(samples, 75),
            p90=np.percentile(samples, 90),
            min_value=np.min(samples),
            max_value=np.max(samples),
            samples=samples,
            parameter_correlations=correlations
        )
