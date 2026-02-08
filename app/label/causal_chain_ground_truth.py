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
from typing import Dict
from app.config.parameter_config import PROCESS_PARAMETERS
from app.config.generator_config import PARAM_RISK_CONFIG, DEFECT_LABEL_CONFIG
from app.services.violation_calculator import calculate_all_parameter_risks
from .label_defects import assign_defects_to_dataframe


# ============================================================================
# RISK-BASED MECHANISM & ROOT CAUSE LABELING
# ============================================================================

def assign_mechanisms_risk_based(df: pd.DataFrame,
                                process_parameters: Dict) -> pd.DataFrame:
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
    threshold = PARAM_RISK_CONFIG['high_risk_threshold']
    
    df = df.copy()
    
    # Initialize
    mech_causes_risk = np.full(len(df), "", dtype=object)
    root_causes_risk = np.full(len(df), "", dtype=object)
    
    # Calculate risks for all rows
    print(f"Calculating parameter risks for {len(df):,} boards...")
    
    for idx, row in df.iterrows():
        risks = calculate_all_parameter_risks(
            df, 
            idx, 
            process_parameters
        )        
        mechanisms = []
        root_causes = []

        # ================================================================
        # COLLECT ROOT CAUSES (parameters in high-risk zone)
        # ================================================================
        for risk_key, val in risks.items():
            if val >= threshold:
                if "paste volume" not in risk_key:
                    root_causes.append({"name": risk_key, "score": val})
        root_causes.sort(key=lambda x: x["score"], reverse=True)
        
        # ================================================================
        # APERTURE OVERFILL RULES (risk-based)
        # ================================================================
        # Rule 1: High stencil OR low viscosity
        if risks['high stencil thickness'] >= threshold or risks['low paste viscosity'] >= threshold:
            mechanisms.append('aperture overfill')
        
        # Rule 2: Low viscosity AND high RH
        elif risks['low paste viscosity'] >= threshold and risks['high ambient rh'] >= threshold:
            mechanisms.append('aperture overfill')
        
        # Rule 3: High Paste Volume
        elif risks['high paste volume per aperture'] >= threshold:
            mechanisms.append('aperture overfill')
        
        # ================================================================
        # POOR PASTE TRANSFER RULES (risk-based)
        # ================================================================
        # Rule 4: Low stencil OR high viscosity
        if risks['low stencil thickness'] >= threshold or risks['high paste viscosity'] >= threshold:
            mechanisms.append('poor paste transfer')
        
        # Rule 5: Low RH AND high viscosity
        elif risks['low ambient rh'] >= threshold and risks['high paste viscosity'] >= threshold:
            mechanisms.append('poor paste transfer')
        
        # Rule 6: Low Paste Volume
        elif risks['low paste volume per aperture'] >= threshold:
            mechanisms.append('poor paste transfer')
        
        # ================================================================
        # EXCESS REFLOW SPREADING RULES (risk-based)
        # ================================================================
        # Rule 7: high peak reflow temperature OR high time above liquidus
        if risks['high peak reflow temperature'] >= threshold or risks['high time above liquidus'] >= threshold:
            mechanisms.append('excess reflow spreading')
        
        # ================================================================
        # NON COALESENCE RULES (risk-based)
        # ================================================================
        # Rule 8: low peak reflow temperature OR low time above liquidus
        if risks['low peak reflow temperature'] >= threshold or risks['low time above liquidus'] >= threshold:
            mechanisms.append('non coalescence')
        
        # ================================================================
        # ASSIGN TO DATAFRAME
        # ================================================================
        if mechanisms:
            mech_causes_risk[idx] = "; ".join(mechanisms)
        
        if root_causes:
            root_causes_risk[idx] = "; ".join([r['name'] for r in root_causes])
    
    df['mech causes'] = mech_causes_risk
    df['root causes'] = root_causes_risk
    
    print(f"✓ Risk-based mechanisms assigned")
    print(f"✓ Risk-based root causes assigned")
    
    return df

# ============================================================================
# COMPLETE PIPELINE
# ============================================================================

def create_risk_based_ground_truth(df: pd.DataFrame,
    process_parameters: Dict
    ) -> pd.DataFrame:
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
    # Step 2: Assign mechanisms
    df = assign_mechanisms_risk_based(
        df,
        process_parameters
    )

    # Step 3: Assign defects
    df = assign_defects_to_dataframe(
        df,
        process_parameters,
        mode=DEFECT_LABEL_CONFIG['mode'],
        threshold=DEFECT_LABEL_CONFIG['threshold']
    )
    
    # Statistics
    print("\n" + "="*70)
    print("STATISTICS")
    print("="*70)
    
    mech_count = (df['mech causes'] != "").sum()
    print(f"Boards with mechanisms: {mech_count:,} ({mech_count/len(df)*100:.2f}%)")
    
    defect_counts = df['Defect'].value_counts()
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
    print("Testing risk-based ground truth generation...")
    print()
    test_df = pd.read_csv("./synthetic_data_factory_ft.csv")
    # Generate risk-based labels
    result_df = create_risk_based_ground_truth(
        test_df,
        PROCESS_PARAMETERS
    )
    result_df.to_csv("./app/outputs/causal_chain_labelling_9.csv")