"""
Probabilistic defect assignment for synthetic data generation

Two assignment modes:
1. Probabilistic (random sampling) - Default, more realistic
2. Threshold-based (deterministic) - Simpler, interpretable
"""

import pandas as pd
import numpy as np
import random

from app.services.proximity_calculator import calculate_defect_probability
from app.config.defect_config import DEFECT_WEIGHTS, PARAMETER_MAPPING, validate_config
from app.config.generator_config import ASSIGNMENT_CONFIG


# ============================================================================
# OPTION 1: PROBABILISTIC ASSIGNMENT (Original)
# ============================================================================
def assign_defect_probabilistic(row, 
                                   process_parameters,
                                   random_seed=None):
    """
    Assign defect using random sampling based on probability
    
    This is the original approach - uses random.random() to sample
    from the probability distribution.
    
    Example: 
        probability = 0.85 → 85% chance defect, 15% chance no defect
    
    Args:
        row: DataFrame row with parameters and mechanisms
        process_parameters: Specification limits
        random_seed: Optional seed for reproducibility
    
    Returns:
        Defect label: "No Defect", "Open Circuit", or "Solder Bridging"
    """
    if random_seed is not None:
        random.seed(random_seed)
    
    mech_str = row.get('mech causes', '')
    
    if pd.isna(mech_str) or mech_str == "":
        return "No Defect"
    
    mech_str = str(mech_str).lower()
    
    # Calculate probability
    probability = calculate_defect_probability(
        row,
        process_parameters,
        DEFECT_WEIGHTS,
        PARAMETER_MAPPING
    )
    ''' 
    **Calculated probability = 0.85 means:**

    "If we run 100 boards with these exact parameters,
    approximately 85 will have solder bridging defects"
    '''

    '''
    **Problem:** 
    We calculate: "This board has 85% chance of bridging"
    But we need: "Solder Bridging" or "No Defect" (binary label)

    **Solution:**
    Use random sampling to respect the probability distribution

    85% probability → 85% of boards get "Solder Bridging"
                    → 15% of boards get "No Defect"
    '''
    # Determine defect type from mechanism
    if "paste volume per aperture high" in mech_str or "aperture overfill" in mech_str:
        # Solder bridging pathway
        return "Solder Bridging" if random.random() < probability else "No Defect"
    
    elif "paste volume per aperture low" in mech_str or "poor paste transfer" in mech_str:
        # Open circuit pathway
        return "Open Circuit" if random.random() < probability else "No Defect"
    
    return "No Defect"

# ============================================================================
# OPTION 2: THRESHOLD-BASED ASSIGNMENT (New)
# ============================================================================

def assign_defect_threshold(row,
                           process_parameters,
                           threshold=0.65):
    """
    Assign defect using probability threshold (deterministic)
    
    Simpler approach - if probability exceeds threshold, assign defect.
    No randomness, purely deterministic based on threshold.
    
    Example:
        probability = 0.70, threshold = 0.65 → Defect (0.70 > 0.65)
        probability = 0.60, threshold = 0.65 → No Defect (0.60 < 0.65)
    
    Args:
        row: DataFrame row with parameters and mechanisms
        process_parameters: Specification limits
        threshold: Probability threshold for defect assignment (0-1)
    
    Returns:
        Defect label: "No Defect", "Open Circuit", or "Solder Bridging"
    """
    mech_str = row.get('mech causes', '')
    
    if pd.isna(mech_str) or mech_str == "":
        return "No Defect"
    
    mech_str = str(mech_str).lower()
    
    # Calculate probability
    probability = calculate_defect_probability(
        row,
        process_parameters,
        DEFECT_WEIGHTS,
        PARAMETER_MAPPING
    )
    
    # Threshold comparison: if probability > threshold, assign defect
    defect_occurs = probability >= threshold
    
    # Determine defect type from mechanism
    if "paste volume per aperture high" in mech_str or "aperture overfill" in mech_str:
        # Solder bridging pathway
        return "Solder Bridging" if defect_occurs else "No Defect"
    
    elif "paste volume per aperture low" in mech_str or "poor paste transfer" in mech_str:
        # Open circuit pathway
        return "Open Circuit" if defect_occurs else "No Defect"
    
    return "No Defect"

# ============================================================================
# UNIFIED INTERFACE
# ============================================================================

def assign_defect_from_probability(row,
                                  process_parameters,
                                  mode=None,
                                  threshold=None,
                                  random_seed=None):
    """
    Unified defect assignment interface
    
    Dispatches to either probabilistic or threshold mode based on config
    
    Args:
        row: DataFrame row
        process_parameters: Spec limits
        mode: 'probabilistic' or 'threshold' (None = use config)
        threshold: Threshold value (None = use config)
        random_seed: For probabilistic mode
    
    Returns:
        Defect label
    """
    # Use config defaults if not specified
    if mode is None:
        mode = ASSIGNMENT_CONFIG['mode']
    
    if threshold is None:
        threshold = ASSIGNMENT_CONFIG['threshold']
    
    # Dispatch to appropriate function
    if mode == 'probabilistic':
        return assign_defect_probabilistic(row, process_parameters, random_seed)
    elif mode == 'threshold':
        return assign_defect_threshold(row, process_parameters, threshold)
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'probabilistic' or 'threshold'")


# ============================================================================
# DATAFRAME-LEVEL ASSIGNMENT
# ============================================================================

def assign_defects_to_dataframe(df,
                               process_parameters,
                               mode=None,
                               threshold=None,
                               random_seed=None):
    """
    Assign defects to entire DataFrame
    
    Args:
        df: DataFrame with parameters and mechanisms
        process_parameters: Specification limits
        mode: 'probabilistic' or 'threshold'
        threshold: Threshold for threshold mode
        random_seed: Seed for probabilistic mode
    
    Returns:
        DataFrame with added 'Defect' and 'Defect_Probability' columns
    """
    # Use config defaults
    if mode is None:
        mode = ASSIGNMENT_CONFIG['mode']
    
    if threshold is None:
        threshold = ASSIGNMENT_CONFIG['threshold']
    
    if random_seed is not None:
        np.random.seed(random_seed)
        random.seed(random_seed)
    
    print(f"\nDefect Assignment Mode: {mode.upper()}")
    if mode == 'threshold':
        print(f"  Threshold: {threshold*100:.1f}%")
    print()
    
    # Calculate probabilities for all rows
    df['Defect_Probability'] = df.apply(
        lambda row: calculate_defect_probability(
            row,
            process_parameters,
            DEFECT_WEIGHTS,
            PARAMETER_MAPPING
        ),
        axis=1
    )
    
    # Assign defects based on mode
    df['Defect'] = df.apply(
        lambda row: assign_defect_from_probability(
            row,
            process_parameters,
            mode=mode,
            threshold=threshold,
            random_seed=None  # Don't reseed per row
        ),
        axis=1
    )
    
    return df


# ============================================================================
# EXAMPLES & TESTING
# ============================================================================

# if __name__ == "__main__":    
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
#         'Paste volume per aperture': 0.035,
#         'Stencil thickness': 95,
#         'Paste viscosity': 256,
#         'Ambient RH': 44,
#         'Ambient temperature': 24.5,
#         'mech causes': 'poor paste transfer'
#     })
    
#     print("TEST CASE:")
#     print("="*70)
#     print(f"Paste volume: {test_row['Paste volume per aperture']}")
#     print(f"Mechanism: {test_row['mech causes']}")
#     print()
    
#     # Calculate probability
#     prob = calculate_defect_probability(
#         test_row,
#         process_params,
#         DEFECT_WEIGHTS,
#         PARAMETER_MAPPING
#     )
#     print(f"Calculated probability: {prob:.3f} ({prob*100:.1f}%)")
#     print()
    
#     # Test probabilistic (run 100 times)
#     print("OPTION 1: PROBABILISTIC (100 runs)")
#     print("-"*70)
#     prob_results = []
#     for i in range(100):
#         result = assign_defect_probabilistic(test_row, process_params)
#         prob_results.append(result)
    
#     prob_defects = sum(1 for r in prob_results if r == "Solder Bridging")
#     print(f"Solder Bridging: {prob_defects}/100 ({prob_defects}%)")
#     print(f"No Defect: {100-prob_defects}/100 ({100-prob_defects}%)")
#     print(f"Expected: ~{prob*100:.0f}% defects")
#     print()
    
#     # Test threshold
#     print("OPTION 2: THRESHOLD")
#     print("-"*70)
#     for thresh in [0.50, 0.65, 0.80, 0.90]:
#         result = assign_defect_threshold(test_row, process_params, threshold=thresh)
#         symbol = "✓" if result == "Solder Bridging" else "○"
#         print(f"Threshold {thresh:.2f}: {symbol} {result}")
    
#     print()
#     print("="*70)