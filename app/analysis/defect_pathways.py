import pandas as pd

def analyze_defect_pathways(df: pd.DataFrame):
    """
    Analyze exact counts of defects with/without mechanisms
    """
    print("="*70)
    print("DEFECT PATHWAY ANALYSIS")
    print("="*70)
    print()
    
    # ========================================================================
    # SOLDER BRIDGING PATHWAYS
    # ========================================================================
    print("SOLDER BRIDGING PATHWAYS (Total: 217)")
    print("-"*70)
    
    bridging_boards = df[df['Defect'] == 'Solder Bridging']
    
    # Pathway 1: With aperture overfill mechanism
    with_overfill = bridging_boards[
        bridging_boards['mech causes'].str.contains('aperture overfill', case=False, na=False)
    ]
    
    # Pathway 2: Paste volume high without mechanism
    paste_high_no_mech = bridging_boards[
        (bridging_boards['mech causes'].str.contains('Paste volume per aperture high', case=False, na=False)) &
        (~bridging_boards['mech causes'].str.contains('aperture overfill', case=False, na=False))
    ]
    
    # Pathway 3: Other causes
    other_bridging = bridging_boards[
        (~bridging_boards['mech causes'].str.contains('aperture overfill', case=False, na=False)) &
        (~bridging_boards['mech causes'].str.contains('Paste volume per aperture high', case=False, na=False))
    ]
    
    print(f"1. With aperture overfill mechanism: {len(with_overfill):4,} ({len(with_overfill)/len(bridging_boards)*100:5.1f}%)")
    print(f"2. Paste volume high (no mechanism):  {len(paste_high_no_mech):4,} ({len(paste_high_no_mech)/len(bridging_boards)*100:5.1f}%)")
    print(f"3. Other causes:                       {len(other_bridging):4,} ({len(other_bridging)/len(bridging_boards)*100:5.1f}%)")
    print(f"   Total:                              {len(bridging_boards):4,}")
    
    print()
    
    # ========================================================================
    # OPEN CIRCUIT PATHWAYS
    # ========================================================================
    print("OPEN CIRCUIT PATHWAYS (Total: 217)")
    print("-"*70)
    
    opens_boards = df[df['Defect'] == 'Open Circuit']
    
    # Pathway 1: With poor paste transfer mechanism
    with_poor_transfer = opens_boards[
        opens_boards['mech causes'].str.contains('poor paste transfer', case=False, na=False)
    ]
    
    # Pathway 2: Paste volume low without mechanism
    paste_low_no_mech = opens_boards[
        (opens_boards['mech causes'].str.contains('Paste volume per aperture low', case=False, na=False)) &
        (~opens_boards['mech causes'].str.contains('poor paste transfer', case=False, na=False))
    ]
    
    # Pathway 3: Other causes
    other_opens = opens_boards[
        (~opens_boards['mech causes'].str.contains('poor paste transfer', case=False, na=False)) &
        (~opens_boards['mech causes'].str.contains('Paste volume per aperture low', case=False, na=False))
    ]
    
    print(f"1. With poor paste transfer mechanism: {len(with_poor_transfer):4,} ({len(with_poor_transfer)/len(opens_boards)*100:5.1f}%)")
    print(f"2. Paste volume low (no mechanism):    {len(paste_low_no_mech):4,} ({len(paste_low_no_mech)/len(opens_boards)*100:5.1f}%)")
    print(f"3. Other causes:                        {len(other_opens):4,} ({len(other_opens)/len(opens_boards)*100:5.1f}%)")
    print(f"   Total:                               {len(opens_boards):4,}")
    
    print()
    
    # ========================================================================
    # MECHANISM DETAILS
    # ========================================================================
    print("MECHANISM TRIGGER BREAKDOWN")
    print("-"*70)
    
    # Aperture overfill details
    overfill_boards = df[df['mech causes'].str.contains('aperture overfill', case=False, na=False)]
    
    overfill_with_paste = overfill_boards[
        overfill_boards['mech causes'].str.contains('Paste volume per aperture high', case=False, na=False)
    ]
    overfill_without_paste = overfill_boards[
        ~overfill_boards['mech causes'].str.contains('Paste volume per aperture high', case=False, na=False)
    ]
    
    print(f"aperture overfill (Total: {len(overfill_boards)}):")
    print(f"  With paste volume high:    {len(overfill_with_paste):4,} ({len(overfill_with_paste)/len(overfill_boards)*100:5.1f}%)")
    print(f"  Without paste volume high: {len(overfill_without_paste):4,} ({len(overfill_without_paste)/len(overfill_boards)*100:5.1f}%)")
    print(f"    (Triggered by: stencil/viscosity/RH rules)")
    
    print()
    
    # Poor paste transfer details
    poor_transfer_boards = df[df['mech causes'].str.contains('poor paste transfer', case=False, na=False)]
    
    poor_with_paste = poor_transfer_boards[
        poor_transfer_boards['mech causes'].str.contains('Paste volume per aperture low', case=False, na=False)
    ]
    poor_without_paste = poor_transfer_boards[
        ~poor_transfer_boards['mech causes'].str.contains('Paste volume per aperture low', case=False, na=False)
    ]
    
    print(f"poor paste transfer (Total: {len(poor_transfer_boards)}):")
    print(f"  With paste volume low:     {len(poor_with_paste):4,} ({len(poor_with_paste)/len(poor_transfer_boards)*100:5.1f}%)")
    print(f"  Without paste volume low:  {len(poor_without_paste):4,} ({len(poor_without_paste)/len(poor_transfer_boards)*100:5.1f}%)")
    print(f"    (Triggered by: stencil/viscosity/RH rules)")
    
    print()
    print("="*70)


# Add this to your main analysis
if __name__ == "__main__":
    df = pd.read_csv("synthetic_data_with_temporal_patterns_x2-6.csv")
    
    # Run pathway analysis
    analyze_defect_pathways(df)