import pandas as pd
def analyze_paste_volume_proximity(df: pd.DataFrame):
    """
    Analyze how close paste volume is to limits when mechanisms trigger
    WITHOUT paste volume violations
    """
    print("="*70)
    print("PASTE VOLUME PROXIMITY ANALYSIS")
    print("="*70)
    print()
    
    # Spec limits
    pv_usl = 0.044
    pv_lsl = 0.036
    pv_nv = 0.040
    
    # ========================================================================
    # APERTURE OVERFILL (without paste volume high)
    # ========================================================================
    print("APERTURE OVERFILL (without paste volume violation)")
    print("-"*70)
    
    overfill_no_paste = df[
        (df['mech causes'].str.contains('aperture overfill', case=False, na=False)) &
        (~df['mech causes'].str.contains('Paste volume per aperture high', case=False, na=False))
    ]
    
    if len(overfill_no_paste) > 0:
        paste_vals = overfill_no_paste['Paste volume per aperture']
        
        print(f"Total boards: {len(overfill_no_paste)}")
        print(f"\nPaste volume statistics:")
        print(f"  Min:    {paste_vals.min():.6f} mm³")
        print(f"  Mean:   {paste_vals.mean():.6f} mm³")
        print(f"  Median: {paste_vals.median():.6f} mm³")
        print(f"  Max:    {paste_vals.max():.6f} mm³")
        print(f"  Std:    {paste_vals.std():.6f} mm³")
        
        # Distance to USL
        distance_to_usl = pv_usl - paste_vals
        print(f"\nDistance to USL (0.044):")
        print(f"  Min distance:  {distance_to_usl.min():.6f} mm³ (closest)")
        print(f"  Mean distance: {distance_to_usl.mean():.6f} mm³")
        print(f"  Max distance:  {distance_to_usl.max():.6f} mm³ (farthest)")
        
        # Percentage of tolerance
        tolerance = pv_usl - pv_nv  # 0.004
        closest_pct = (distance_to_usl.min() / tolerance) * 100
        mean_pct = (distance_to_usl.mean() / tolerance) * 100
        
        print(f"\nAs % of tolerance (0.004):")
        print(f"  Closest board: {closest_pct:.1f}% away from USL")
        print(f"  Average:       {mean_pct:.1f}% away from USL")
        
        # Proximity bins
        print(f"\nProximity distribution:")
        very_close = (distance_to_usl < 0.001).sum()  # Within 0.001
        close = ((distance_to_usl >= 0.001) & (distance_to_usl < 0.002)).sum()
        moderate = ((distance_to_usl >= 0.002) & (distance_to_usl < 0.003)).sum()
        far = (distance_to_usl >= 0.003).sum()
        
        print(f"  Very close (<0.001 mm³):  {very_close:4,} ({very_close/len(overfill_no_paste)*100:5.1f}%)")
        print(f"  Close (0.001-0.002 mm³):  {close:4,} ({close/len(overfill_no_paste)*100:5.1f}%)")
        print(f"  Moderate (0.002-0.003):   {moderate:4,} ({moderate/len(overfill_no_paste)*100:5.1f}%)")
        print(f"  Far (>0.003 mm³):         {far:4,} ({far/len(overfill_no_paste)*100:5.1f}%)")
    else:
        print("No boards found")
    
    print()
    
    # ========================================================================
    # POOR PASTE TRANSFER (without paste volume low)
    # ========================================================================
    print("POOR PASTE TRANSFER (without paste volume violation)")
    print("-"*70)
    
    poor_no_paste = df[
        (df['mech causes'].str.contains('poor paste transfer', case=False, na=False)) &
        (~df['mech causes'].str.contains('Paste volume per aperture low', case=False, na=False))
    ]
    
    if len(poor_no_paste) > 0:
        paste_vals = poor_no_paste['Paste volume per aperture']
        
        print(f"Total boards: {len(poor_no_paste)}")
        print(f"\nPaste volume statistics:")
        print(f"  Min:    {paste_vals.min():.6f} mm³")
        print(f"  Mean:   {paste_vals.mean():.6f} mm³")
        print(f"  Median: {paste_vals.median():.6f} mm³")
        print(f"  Max:    {paste_vals.max():.6f} mm³")
        print(f"  Std:    {paste_vals.std():.6f} mm³")
        
        # Distance to LSL
        distance_to_lsl = paste_vals - pv_lsl
        print(f"\nDistance to LSL (0.036):")
        print(f"  Min distance:  {distance_to_lsl.min():.6f} mm³ (closest)")
        print(f"  Mean distance: {distance_to_lsl.mean():.6f} mm³")
        print(f"  Max distance:  {distance_to_lsl.max():.6f} mm³ (farthest)")
        
        # Percentage of tolerance
        tolerance = pv_nv - pv_lsl  # 0.004
        closest_pct = (distance_to_lsl.min() / tolerance) * 100
        mean_pct = (distance_to_lsl.mean() / tolerance) * 100
        
        print(f"\nAs % of tolerance (0.004):")
        print(f"  Closest board: {closest_pct:.1f}% away from LSL")
        print(f"  Average:       {mean_pct:.1f}% away from LSL")
        
        # Proximity bins
        print(f"\nProximity distribution:")
        very_close = (distance_to_lsl < 0.001).sum()  # Within 0.001
        close = ((distance_to_lsl >= 0.001) & (distance_to_lsl < 0.002)).sum()
        moderate = ((distance_to_lsl >= 0.002) & (distance_to_lsl < 0.003)).sum()
        far = (distance_to_lsl >= 0.003).sum()
        
        print(f"  Very close (<0.001 mm³):  {very_close:4,} ({very_close/len(poor_no_paste)*100:5.1f}%)")
        print(f"  Close (0.001-0.002 mm³):  {close:4,} ({close/len(poor_no_paste)*100:5.1f}%)")
        print(f"  Moderate (0.002-0.003):   {moderate:4,} ({moderate/len(poor_no_paste)*100:5.1f}%)")
        print(f"  Far (>0.003 mm³):         {far:4,} ({far/len(poor_no_paste)*100:5.1f}%)")
    else:
        print("No boards found")
    
    print()
    print("="*70)


# Add to your analysis
if __name__ == "__main__":
    df = pd.read_csv("synthetic_data_with_temporal_patterns_x2-6.csv")
    
    # Run proximity analysis
    analyze_paste_volume_proximity(df)