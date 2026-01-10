"""
Risk-Based Ground Truth Labeling for Causal Chains

Uses risk probability thresholds instead of hard specification limits.
Better alignment with MLP probabilistic outputs.

Key Principle:
- Parameters in HIGH RISK zone (>70% probability) trigger mechanisms
- Mechanisms with high risk trigger defects (probabilistically)
- Smooth gradients instead of step functions
"""

import numpy as np
import pandas as pd
import math
import random
from typing import Dict
from app.config.parameter_config import PROCESS_PARAMETERS
from app.config.generator_config import RISK_CONFIG
from app.services.violation_calculator import calculate_all_parameter_risks


# ============================================================================
# RISK-BASED MECHANISM LABELING
# ============================================================================

def assign_mechanisms_risk_based(df: pd.DataFrame,
                                process_parameters: Dict,
                                threshold: float = None) -> pd.DataFrame:
    """
    Assign mechanisms based on risk probability thresholds
    
    Instead of hard limits, uses risk zones:
    - Risk > threshold → Trigger mechanism
    
    Args:
        df: DataFrame with parameter values
        process_parameters: Specification limits
        threshold: Risk threshold (default from config)
    
    Returns:
        DataFrame with 'mech_causes_risk' column
    """
    if threshold is None:
        threshold = RISK_CONFIG['mechanism_threshold']
    
    df = df.copy()
    
    # Initialize
    mech_causes_risk = np.full(len(df), "", dtype=object)
    
    # Calculate risks for all rows
    print(f"Calculating parameter risks for {len(df):,} boards...")
    
    for idx, row in df.iterrows():
        risks = calculate_all_parameter_risks(row, process_parameters)
        
        mechanisms = []
        
        # ================================================================
        # APERTURE OVERFILL RULES (risk-based)
        # ================================================================
        # Rule 1: High stencil OR low viscosity
        if risks['stencil_high'] > threshold or risks['viscosity_low'] > threshold:
            mechanisms.append('aperture overfill')
        
        # Rule 2: Low viscosity AND high RH
        elif risks['viscosity_low'] > threshold and risks['rh_high'] > threshold:
            mechanisms.append('aperture overfill')
        
        # ================================================================
        # POOR PASTE TRANSFER RULES (risk-based)
        # ================================================================
        # Rule 3: Low stencil OR high viscosity
        if risks['stencil_low'] > threshold or risks['viscosity_high'] > threshold:
            mechanisms.append('poor paste transfer')
        
        # Rule 4: Low RH AND high viscosity
        elif risks['rh_low'] > threshold and risks['viscosity_high'] > threshold:
            mechanisms.append('poor paste transfer')
        
        # Combine mechanisms
        if mechanisms:
            mech_causes_risk[idx] = "; ".join(mechanisms)
    
    df['mech_causes_risk'] = mech_causes_risk
    
    print(f"✓ Risk-based mechanisms assigned")
    
    return df

# ============================================================================
# COMPLETE PIPELINE
# ============================================================================

def create_risk_based_ground_truth(df: pd.DataFrame,
                                   process_parameters: Dict,
                                   mechanism_threshold: float = 0.70,
                                   defect_mode: str = 'probabilistic',
                                   defect_threshold: float = 0.65,
                                   random_seed: int = None) -> pd.DataFrame:
    """
    Complete pipeline for risk-based ground truth generation
    
    Args:
        df: DataFrame with parameter values
        process_parameters: Specification limits
        mechanism_threshold: Risk threshold for mechanisms
        defect_mode: 'probabilistic' or 'threshold'
        defect_threshold: Threshold for defect assignment
        random_seed: Random seed
    
    Returns:
        DataFrame with risk-based labels
    """
    print("="*70)
    print("RISK-BASED GROUND TRUTH GENERATION")
    print("="*70)
    print(f"Mechanism threshold: {mechanism_threshold*100:.0f}%")
    print(f"Defect mode: {defect_mode}")
    if defect_mode == 'threshold':
        print(f"Defect threshold: {defect_threshold*100:.0f}%")
    print()
    
    # Step 1: Assign mechanisms
    df = assign_mechanisms_risk_based(
        df,
        process_parameters,
        threshold=mechanism_threshold
    )
    
    # Statistics
    print("\n" + "="*70)
    print("STATISTICS")
    print("="*70)
    
    mech_count = (df['mech_causes_risk'] != "").sum()
    print(f"Boards with mechanisms: {mech_count:,} ({mech_count/len(df)*100:.2f}%)")
    
    defect_counts = df['Defect_risk'].value_counts()
    print(f"\nDefect distribution:")
    for defect, count in defect_counts.items():
        pct = (count / len(df)) * 100
        print(f"  {defect:20s} {count:6,} ({pct:5.2f}%)")
    
    print("="*70)
    
    return df


# ============================================================================
# MAIN - FOR TESTING
# ============================================================================

if __name__ == "__main__":
    # Test with sample data
    from config.parameter_config import process_parameters
    
    print("Testing risk-based ground truth generation...")
    print()
    
    # Create sample data
    test_df = pd.DataFrame({
        'Paste volume per aperture': [0.040, 0.043, 0.044, 0.046],
        'Stencil thickness': [100, 103, 106, 108],
        'Paste viscosity': [200, 180, 160, 150],
        'Ambient RH': [40, 45, 52, 55],
        'Ambient temperature': [23, 24, 25, 26]
    })
    
    # Generate risk-based labels
    result_df = create_risk_based_ground_truth(
        test_df,
        process_parameters,
        mechanism_threshold=0.70,
        defect_mode='probabilistic',
        random_seed=42
    )
    
    print("\nResults:")
    print(result_df[['Paste volume per aperture', 'mech_causes_risk', 'Defect_risk']])