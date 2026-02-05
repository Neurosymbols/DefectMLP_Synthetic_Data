from typing import Dict
import numpy as np
from app.services.violation_calculator import calculate_all_parameter_risks

def create_parameter_risk_labels(samples: Dict, 
                                 process_parameters: Dict) -> Dict:
    """
    Create risk score ground truth for each parameter
    
    Returns continuous risk scores [0.0 - 1.0] for each parameter.
    Uses max(high_risk, low_risk) since only one direction can be risky.
    
    Args:
        df: DataFrame with parameter values
        process_parameters: Specification limits
    
    Returns:
        DataFrame with added risk score columns (e.g., 'stencil_thickness_risk')
    """
    samples_len = len(samples['Stencil thickness'])
    print("\nCalculating parameter risk scores...")
    print(f"Processing {samples_len:,} boards...")
    
    # Initialize risk score columns dynamically
    risk_columns = []
    for col_name in process_parameters.keys():
        risk_col = f"{col_name} risk"
        samples[risk_col] = []
        risk_columns.append(risk_col)
    
    # Calculate risk for each row
    for i in range(samples_len):
        # Get risks using risk calculation function
        risks = calculate_all_parameter_risks(
            samples, 
            i, 
            process_parameters
        )
        
        # For each parameter, take MAX of high_risk and low_risk
        for col_name in process_parameters.keys():
            risk_score = max(
                risks[f'high {col_name.lower()}'],
                risks[f'low {col_name.lower()}']
            )
            samples[f"{col_name} risk"].append(risk_score)
    print("✓ Parameter risk scores calculated")
    
    # Print statistics
    print("\n" + "="*60)
    print("PARAMETER RISK SCORE STATISTICS")
    print("="*60)
    
    for risk_col in risk_columns:
        values = np.array(samples[risk_col])
        mean_risk = values.mean()
        median_risk = np.median(values)
        max_risk = values.max()
        high_risk_count = (values > 0.70).sum()
        high_risk_pct = (values > 0.70).mean() * 100

        print(f"\n{risk_col}:")
        print(f"  Mean:              {mean_risk:.4f}")
        print(f"  Median:            {median_risk:.4f}")
        print(f"  Max:               {max_risk:.4f}")
        print(f"  High risk (>0.70): {high_risk_count:>6,} ({high_risk_pct:5.2f}%)")

    print("=" * 60)
    
    return samples
