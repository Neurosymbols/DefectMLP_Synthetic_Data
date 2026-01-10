"""
Analyze synthetic PCB data distribution
"""
import pandas as pd
import numpy as np

def analyze_synthetic_data(df: pd.DataFrame):
    """
    Analyze defects, mechanisms, and parameter violations
    
    Args:
        df: DataFrame with synthetic data
    """
    
    print("="*70)
    print("SYNTHETIC DATA ANALYSIS")
    print("="*70)
    print(f"Total samples: {len(df):,}\n")
    
    # ========================================================================
    # 1. DEFECT DISTRIBUTION
    # ========================================================================
    print("1. DEFECT DISTRIBUTION")
    print("-"*70)
    
    defect_counts = df['Defect'].value_counts()
    defect_pcts = df['Defect'].value_counts(normalize=True) * 100
    
    for defect in defect_counts.index:
        count = defect_counts[defect]
        pct = defect_pcts[defect]
        bar = "█" * int(pct / 2)
        print(f"{defect:20s} {count:6,} ({pct:5.2f}%) {bar}")
    
    print()
    
    # ========================================================================
    # 2A. MECHANISM DISTRIBUTION (Enhanced for Multiple Mechanisms)
    # ========================================================================
    print("2. MECHANISM DISTRIBUTION")
    print("-"*70)
    
    # Count overall mechanism column values
    mech_counts = df['mech causes'].value_counts()
    
    print("Raw mechanism combinations:")
    for mech in mech_counts.index:
        count = mech_counts[mech]
        pct = (count / len(df)) * 100
        display_name = mech if mech != "" else "No mechanism"
        bar = "█" * int(pct / 2)
        print(f"{display_name:50s} {count:6,} ({pct:5.2f}%) {bar}")
    
    print()

    # ========================================================================
    # 2B. INDIVIDUAL MECHANISM BREAKDOWN
    # ========================================================================
    print("Individual mechanism occurrences:")
    print("-"*70)

    # Parse individual mechanisms (split by semicolon)
    individual_mechs = []
    for mech_str in df['mech causes']:
        # Handle NA/NaN values
        if pd.isna(mech_str) or mech_str == "":
            continue
        
        # Convert to string if needed
        mech_str = str(mech_str)
        
        # Split by semicolon and strip whitespace
        mechs = [m.strip() for m in mech_str.split(';')]
        individual_mechs.extend(mechs)

    # Count individual mechanisms
    from collections import Counter
    individual_counts = Counter(individual_mechs)

    if len(individual_counts) > 0:
        for mech, count in sorted(individual_counts.items(), key=lambda x: x[1], reverse=True):
            pct = (count / len(df)) * 100
            bar = "█" * int(pct / 2)
            print(f"{mech:40s} {count:6,} ({pct:5.2f}%) {bar}")
    else:
        print("No mechanisms detected")

    # Count boards with multiple mechanisms
    multiple_mechs = df[df['mech causes'].astype(str).str.contains(';', na=False)]
    print(f"\nBoards with multiple mechanisms: {len(multiple_mechs):,} ({len(multiple_mechs)/len(df)*100:.2f}%)")

    print()
    
    # ========================================================================
    # 3. PARAMETER VIOLATIONS
    # ========================================================================
    print("3. PARAMETER VIOLATIONS")
    print("-"*70)
    
    params = [
        'Paste volume per aperture',
        'Stencil thickness',
        'Paste viscosity',
        'Ambient RH',
        'Ambient temperature'
    ]
    
    # Define spec limits (from your config)
    specs = {
        'Paste volume per aperture': {'LSL': 0.036, 'USL': 0.044},
        'Stencil thickness': {'LSL': 95, 'USL': 105},
        'Paste viscosity': {'LSL': 150, 'USL': 250},
        'Ambient RH': {'LSL': 30, 'USL': 50},
        'Ambient temperature': {'LSL': 20, 'USL': 26}
    }
    
    for param in params:
        lsl = specs[param]['LSL']
        usl = specs[param]['USL']
        
        below_lsl = (df[param] < lsl).sum()
        above_usl = (df[param] > usl).sum()
        total_viol = below_lsl + above_usl
        
        pct_low = (below_lsl / len(df)) * 100
        pct_high = (above_usl / len(df)) * 100
        pct_total = (total_viol / len(df)) * 100
        
        print(f"\n{param}:")
        print(f"  Below LSL ({lsl}): {below_lsl:5,} ({pct_low:5.2f}%)")
        print(f"  Above USL ({usl}): {above_usl:5,} ({pct_high:5.2f}%)")
        print(f"  Total violations: {total_viol:5,} ({pct_total:5.2f}%)")
    
    print()
    
    # ========================================================================
    # 4. DEFECT-MECHANISM RELATIONSHIP (Enhanced)
    # ========================================================================
    print("4. DEFECT-MECHANISM RELATIONSHIP")
    print("-"*70)
    
    # Create binary columns for each mechanism
    df_analysis = df.copy()
    
    # List of individual mechanisms to track
    all_mechanisms = ['aperture overfill', 'poor paste transfer']
    
    for mech in all_mechanisms:
        df_analysis[f'has_{mech}'] = df_analysis['mech causes'].str.contains(mech, na=False)
    
    # Crosstab for each mechanism
    for mech in all_mechanisms:
        print(f"\n{mech}:")
        crosstab = pd.crosstab(
            df_analysis['Defect'],
            df_analysis[f'has_{mech}'],
            margins=True
        )
        crosstab.columns = ['Absent', 'Present', 'Total']
        print(crosstab)
    
    print()
    
    # ========================================================================
    # 5. CLASS BALANCE CHECK
    # ========================================================================
    print("6. CLASS BALANCE ASSESSMENT")
    print("-"*70)
    
    min_samples = 1000  # ML minimum
    
    print(f"Minimum samples needed per class: {min_samples:,}")
    print()
    
    # Check defects
    print("Defect classes:")
    for defect in defect_counts.index:
        count = defect_counts[defect]
        status = "✓" if count >= min_samples else "✗"
        ratio = count / min_samples
        print(f"{status} {defect:20s} {count:6,} (ratio: {ratio:.2f}x)")
    
    print()
    
    # Check mechanisms
    print("Mechanism classes:")
    for mech, count in sorted(individual_counts.items(), key=lambda x: x[1], reverse=True):
        status = "✓" if count >= min_samples else "✗"
        ratio = count / min_samples
        print(f"{status} {mech:20s} {count:6,} (ratio: {ratio:.2f}x)")
    
    print()
    
    # ========================================================================
    # 7. IMBALANCE METRICS
    # ========================================================================
    print("7. IMBALANCE METRICS")
    print("-"*70)
    
    # Defect imbalance
    max_class = defect_counts.max()
    min_class = defect_counts.min()
    imbalance_ratio = max_class / min_class
    
    print("Defect classes:")
    print(f"  Largest class: {defect_counts.idxmax()} ({max_class:,})")
    print(f"  Smallest class: {defect_counts.idxmin()} ({min_class:,})")
    print(f"  Imbalance ratio: {imbalance_ratio:.2f}:1")
    
    if imbalance_ratio > 10:
        print("  ⚠️  SEVERE IMBALANCE - Consider rebalancing")
    elif imbalance_ratio > 3:
        print("  ⚠️  MODERATE IMBALANCE - Use class weights")
    else:
        print("  ✓ ACCEPTABLE BALANCE")
    
    # Mechanism imbalance
    if len(individual_counts) > 0:
        mech_values = list(individual_counts.values())
        max_mech = max(mech_values)
        min_mech = min(mech_values)
        mech_ratio = max_mech / min_mech if min_mech > 0 else float('inf')
        
        print(f"\nMechanism classes:")
        print(f"  Largest: {max_mech:,}")
        print(f"  Smallest: {min_mech:,}")
        print(f"  Imbalance ratio: {mech_ratio:.2f}:1")
    
    print("\n" + "="*70)


# ============================================================================
# USAGE
# ============================================================================

if __name__ == "__main__":
    # Load your generated data
    df = pd.read_csv("synthetic_data_with_temporal_patterns_x2-6.csv")
    
    # Run analysis
    analyze_synthetic_data(df)
