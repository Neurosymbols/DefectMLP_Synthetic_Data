"""
Probabilistic defect assignment for synthetic data generation

Two assignment modes:
1. Probabilistic (random sampling) - Default, more realistic
2. Threshold-based (deterministic) - Simpler, interpretable
3. Direct (mechanism → defect) - Simple rule-based ( in use )
"""

import pandas as pd
import numpy as np
import random

# ============================================================================
# OPTION 1: DIRECT MECHANISM-TO-DEFECT
# ============================================================================

def assign_defect_direct(row):
    """
    Direct assignment: Mechanism fires → Defect fires (100%)
    
    Simplest approach - no probability calculation needed.
    If mechanism is present, defect always occurs.
    
    Example:
        aperture overfill present → Solder Bridging (always)
        poor paste transfer present → Open Circuit (always)
        no mechanism → No Defect
    
    Args:
        row: DataFrame row with 'mech causes' column
    
    Returns:
        Defect label: "No Defect", "Open Circuit", or "Solder Bridging"
    """
    mech_str = row.get('mech causes', '')
    
    if pd.isna(mech_str) or mech_str == "":
        return "No Defect"
    
    mech_str = str(mech_str).lower()
    
    # Direct mapping: mechanism → defect
    if "excess reflow spreading" in mech_str or "aperture overfill" in mech_str:
        return "Solder Bridging"
    
    elif "non coalescence" in mech_str or "poor paste transfer" in mech_str:
        return "Open Circuit"

    return "No Defect"

# ============================================================================
# DATAFRAME-LEVEL ASSIGNMENT
# ============================================================================

def assign_defects_to_dataframe(df):
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
    # Assign defects based on mode
    df['Defect'] = df.apply(
        lambda row: assign_defect_direct(row),
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