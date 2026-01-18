"""
Store synthetic data analysis results in MongoDB
"""
import pandas as pd
from datetime import datetime
from collections import Counter
from app.config.mongo_config import client, db
from app.config.parameter_config import PROCESS_PARAMETERS
import json

def analyze_and_convert_to_document(df: pd.DataFrame, metadata: dict = None):
    """
    Analyze DataFrame and convert results to MongoDB document
    
    Args:
        df: DataFrame with synthetic data
        metadata: Optional metadata (version, description, etc.)
    
    Returns:
        Dictionary ready for MongoDB insertion
    """
    
    # Initialize document
    doc = {
        'timestamp': datetime.utcnow(),
        'total_samples': len(df),
        'metadata': metadata or {}
    }

    # ========================================================================
    # 1. DEFECT DISTRIBUTION
    # ========================================================================
    
    defect_counts = df['Defect'].value_counts().to_dict()
    defect_pcts = (df['Defect'].value_counts(normalize=True) * 100).to_dict()
    
    doc['defect_distribution'] = {
        'counts': defect_counts,
        'percentages': defect_pcts
    }

    # ========================================================================
    # 2. MECHANISM DISTRIBUTION
    # ========================================================================
    
    # Raw combinations
    mech_counts = df['mech causes'].value_counts().to_dict()
    
    # Individual mechanisms
    individual_mechs = []
    for mech_str in df['mech causes']:
        if pd.isna(mech_str) or mech_str == "":
            continue
        mech_str = str(mech_str)
        mechs = [m.strip() for m in mech_str.split(';')]
        individual_mechs.extend(mechs)
    
    individual_counts = dict(Counter(individual_mechs))
    
    # Multiple mechanisms
    multiple_mechs = df[df['mech causes'].astype(str).str.contains(';', na=False)]
    
    doc['mechanism_distribution'] = {
        'raw_combinations': mech_counts,
        'individual_counts': individual_counts,
        'multiple_mechanisms_count': len(multiple_mechs),
        'multiple_mechanisms_pct': (len(multiple_mechs) / len(df)) * 100
    }

    # ========================================================================
    # 3. PARAMETER VIOLATIONS
    # ========================================================================
    
    violations = {}
    for param, limits in PROCESS_PARAMETERS.items():
        below_lsl = int((df[param] < limits['LSL']).sum())
        above_usl = int((df[param] > limits['USL']).sum())
        total = below_lsl + above_usl
        
        violations[param] = {
            'LSL': limits['LSL'],
            'USL': limits['USL'],
            'below_lsl': below_lsl,
            'above_usl': above_usl,
            'total_violations': total,
            'pct_below_lsl': (below_lsl / len(df)) * 100,
            'pct_above_usl': (above_usl / len(df)) * 100,
            'pct_total': (total / len(df)) * 100
        }
    
    doc['parameter_violations'] = violations

    # ========================================================================
    # 4. DEFECT-MECHANISM RELATIONSHIP
    # ========================================================================
    
    df_analysis = df.copy()
    all_mechanisms = ['aperture overfill', 'poor paste transfer']
    
    mechanism_relationships = {}
    for mech in all_mechanisms:
        df_analysis[f'has_{mech}'] = df_analysis['mech causes'].str.contains(mech, case=False, na=False)
        
        # Crosstab
        crosstab = pd.crosstab(
            df_analysis['Defect'],
            df_analysis[f'has_{mech}']
        )
        
        # Convert to dict and fix boolean keys
        crosstab_dict = {}
        for col in crosstab.columns:
            key = 'present' if col else 'absent'  # Convert True/False to strings
            crosstab_dict[key] = crosstab[col].to_dict()
        
        mechanism_relationships[mech] = crosstab_dict
    
    doc['defect_mechanism_relationship'] = mechanism_relationships

    # ========================================================================
    # 5. CLASS BALANCE
    # ========================================================================
    
    min_samples = 1000
    
    defect_balance = {}
    for defect, count in defect_counts.items():
        defect_balance[defect] = {
            'count': int(count),
            'ratio': float(count / min_samples),
            'meets_minimum': bool(count >= min_samples)
        }
    
    mechanism_balance = {}
    for mech, count in individual_counts.items():
        mechanism_balance[mech] = {
            'count': int(count),
            'ratio': float(count / min_samples),
            'meets_minimum': bool(count >= min_samples)
        }
    
    doc['class_balance'] = {
        'minimum_required': int(min_samples),
        'defects': defect_balance,
        'mechanisms': mechanism_balance
    }

    # ========================================================================
    # 6. IMBALANCE METRICS
    # ========================================================================
    
    max_defect = max(defect_counts.values())
    min_defect = min(defect_counts.values())
    defect_imbalance = max_defect / min_defect
    
    if individual_counts:
        max_mech = max(individual_counts.values())
        min_mech = min(individual_counts.values())
        mech_imbalance = max_mech / min_mech
    else:
        max_mech = 0
        min_mech = 0
        mech_imbalance = 0
    
    doc['imbalance_metrics'] = {
        'defects': {
            'largest_class': str(max(defect_counts, key=defect_counts.get)),
            'smallest_class': str(min(defect_counts, key=defect_counts.get)),
            'largest_count': int(max_defect),
            'smallest_count': int(min_defect),
            'imbalance_ratio': float(defect_imbalance),
            'severity': 'SEVERE' if defect_imbalance > 10 else ('MODERATE' if defect_imbalance > 3 else 'ACCEPTABLE')
        },
        'mechanisms': {
            'largest_count': int(max_mech),
            'smallest_count': int(min_mech),
            'imbalance_ratio': float(mech_imbalance) if mech_imbalance else None
        }
    }

    collection = db['analysis_results']
    # Insert document
    result = collection.insert_one(doc)
    
    print(f"✓ Analysis stored in MongoDB")
    return result.inserted_id

if __name__ == "__main__":
    # Load data
    # df = pd.read_csv("synthetic_data_with_temporal_patterns_x2-8.csv")
    df = pd.read_csv("training_data_200k_v3.csv")
    
    # Metadata for this run
    metadata = {
        'version': '2.7',
        'n_samples': len(df),
        'description': 'Probabilistic defect assignment test'
    }
    analyze_and_convert_to_document(
        df, metadata
    )