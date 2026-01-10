"""
Proximity-based defect probability calculation

Uses distance to specification limits for all parameters
"""

import numpy as np
import pandas as pd

from app.config.defect_config import DEFECT_WEIGHTS, PARAMETER_MAPPING, validate_config


def get_proximity(value, param_info):
    """
    Calculate how close a value is to its nearest specification limit
    
    Args:
        value: Actual parameter value
        param_info: Dictionary with 'NV', 'USL', 'LSL' keys
    
    Returns:
        Proximity score: 0.0 (at nominal) to 1.0 (at/beyond limit)
    
    Physical meaning:
        0.0 = At nominal value (safe)
        0.5 = Halfway between nominal and limit (warning)
        1.0 = At or beyond specification limit (critical)
    """
    nominal = param_info['NV']
    usl = param_info['USL']
    lsl = param_info['LSL']
    
    if value > nominal:
        # High side - approaching USL
        if value >= usl:
            return 1.0  # At or beyond upper limit
        
        distance_to_limit = usl - value
        total_range = usl - nominal
        proximity = 1.0 - (distance_to_limit / total_range)
    
    else:
        # Low side - approaching LSL
        if value <= lsl:
            return 1.0  # At or beyond lower limit
        
        distance_to_limit = value - lsl
        total_range = nominal - lsl
        proximity = 1.0 - (distance_to_limit / total_range)
    
    # Ensure in valid range
    return max(0.0, min(1.0, proximity))


def calculate_all_proximities(row, process_parameters, parameter_mapping):
    """
    Calculate proximity for all parameters
    
    Args:
        row: DataFrame row with parameter values
        process_parameters: Dictionary with specification limits
        parameter_mapping: Maps column names to config keys
    
    Returns:
        Dictionary of proximities keyed by config names
    """
    proximities = {}
    
    for col_name, config_key in parameter_mapping.items():
        if col_name in row.index and col_name in process_parameters:
            value = row[col_name]
            param_info = process_parameters[col_name]
            proximities[config_key] = get_proximity(value, param_info)
        else:
            proximities[config_key] = 0.0  # Default if missing
    
    return proximities


def calculate_contributing_score(proximities, factor_weights, exclude_primary=None):
    """
    Calculate weighted contribution from multiple factors
    
    Args:
        proximities: Dictionary of proximity scores
        factor_weights: Dictionary of weights for each factor
        exclude_primary: Key to exclude (e.g., 'paste_volume' if it's primary)
    
    Returns:
        Weighted sum of contributing factors
    """
    contributing = 0.0
    
    for factor, weight in factor_weights.items():
        if factor != exclude_primary and factor in proximities:
            contributing += weight * proximities[factor]
    
    return contributing


def calculate_defect_probability(row, 
                                 process_parameters,
                                 defect_weights,
                                 parameter_mapping):
    """
    Calculate defect probability using proximity-based approach
    
    Args:
        row: DataFrame row with parameter values and mechanism
        process_parameters: Specification limits
        defect_weights: Configuration from defect_config.py
        parameter_mapping: Column name mapping
    
    Returns:
        Defect probability (0.0 to 1.0)
    """
    mech_str = row.get('mech causes', '')
    
    if pd.isna(mech_str) or mech_str == "":
        return 0.0  # No mechanism, no defect
    
    mech_str = str(mech_str).lower()
    
    # Calculate all proximities
    proximities = calculate_all_proximities(row, process_parameters, parameter_mapping)
    
    # ========================================================================
    # SOLDER BRIDGING PATHWAY
    # ========================================================================
    if "paste volume per aperture high" in mech_str or "aperture overfill" in mech_str:
        config = defect_weights['solder_bridging']
        
        # Primary factor: Paste volume proximity
        primary = proximities.get('paste_volume', 0.0)
        
        # Contributing factors (all except paste volume)
        contributing = calculate_contributing_score(
            proximities,
            config['factor_weights'],
            exclude_primary='paste_volume'
        )
        
        # Combine
        probability = (
            config['baseline'] +
            config['primary_weight'] * primary +
            config['contributing_weight'] * contributing
        )
        
        # Cap at maximum
        probability = min(config['max_probability'], probability)
        
        return probability
    
    # ========================================================================
    # OPEN CIRCUIT PATHWAY
    # ========================================================================
    elif "paste volume per aperture low" in mech_str or "poor paste transfer" in mech_str:
        config = defect_weights['open_circuit']
        
        # Primary factor: Paste volume proximity
        primary = proximities.get('paste_volume', 0.0)
        
        # Contributing factors
        contributing = calculate_contributing_score(
            proximities,
            config['factor_weights'],
            exclude_primary='paste_volume'
        )
        
        # Combine
        probability = (
            config['baseline'] +
            config['primary_weight'] * primary +
            config['contributing_weight'] * contributing
        )
        
        # Cap at maximum
        probability = min(config['max_probability'], probability)
        
        return probability
    
    return 0.0  # No recognized mechanism


# if __name__ == "__main__":
#     # Test with sample data
#     validate_config()
    
#     # Sample process parameters
#     process_params = {
#         'Paste volume per aperture': {'NV': 0.040, 'USL': 0.044, 'LSL': 0.036},
#         'Stencil thickness': {'NV': 100, 'USL': 105, 'LSL': 95},
#         'Paste viscosity': {'NV': 200, 'USL': 250, 'LSL': 150},
#         'Ambient RH': {'NV': 40, 'USL': 50, 'LSL': 30},
#         'Ambient temperature': {'NV': 23, 'USL': 26, 'LSL': 20}
#     }
    
#     # Test case
#     test_row = pd.Series({
#         'Paste volume per aperture': 0.044,
#         'Stencil thickness': 106,
#         'Paste viscosity': 148,
#         'Ambient RH': 52,
#         'Ambient temperature': 24.5,
#         'mech causes': 'aperture overfill'
#     })
    
#     prob = calculate_defect_probability(
#         test_row,
#         process_params,
#         DEFECT_WEIGHTS,
#         PARAMETER_MAPPING
#     )
    
#     print(f"\nTest case probability: {prob:.3f} ({prob*100:.1f}%)")