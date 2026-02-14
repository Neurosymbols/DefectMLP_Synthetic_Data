"""
Synthetic Data Generator Configuration

All temporal and generation parameters are configurable here.
Each parameter should be justified with citations for dissertation.
"""
from app.config.parameter_config import PROCESS_PARAMETERS

# ============================================================================
# LABELLING CONFIG
# ============================================================================

PARAM_RISK_CONFIG = {
    'high_risk_threshold': 0.60, # [NEEDS CITATION] - Threshold for high-risk zone    
    # Justification:
    # - Provides smooth gradient for MLP learning
}

# ============================================================================
# TEMPORAL PATTERN CONFIGURATION
# ============================================================================

TEMPORAL_CONFIG = {
    'stencil_drift': {
        'initial_thickness': 100.5,      # [NEEDS CITATION] - Starting stencil thickness (µm)
        'wear_rate': 0.0009,             # [NEEDS CITATION] - Wear per board (µm/board)
        'stencil_life': 5000,            # [NEEDS CITATION] - Boards before replacement
        
        # Justification notes:
        # - initial_thickness: Slightly above nominal to account for manufacturing
        # - wear_rate: Based on [cite stencil wear study]
        # - stencil_life: Industry standard replacement interval
    },
    
    'temperature_cycle': {
        'base_temp': 23,               # [NEEDS CITATION] - Average factory temperature (°C)
        'amplitude': 1.5,                # [NEEDS CITATION] - Daily temperature swing (°C)
        'start_hour': 6,                 # [NEEDS CITATION] - Production start time (24h)
        
        # Justification notes:
        # - base_temp: Typical climate-controlled factory
        # - amplitude: Based on [cite HVAC study or factory measurements]
        # - start_hour: Standard first shift start time
    },
    
    'production_rate': {
        'boards_per_hour': 320,          # [NEEDS CITATION] - Production throughput
        
        # Justification notes:
        # - Based on [cite SMT line speed study]
        # - Typical modern SMT line: 200-400 boards/hour
    }
}


# ============================================================================
# SAMPLE SIZE CONFIGURATION
# ============================================================================

SAMPLE_SIZE_CONFIG = {
    'default_samples': 5000,             # [NEEDS CITATION] - Default dataset size
    'target_samples': 80000,             # [NEEDS CITATION] - Target for ML training
    
    # Calculation basis:
    # Minimum ML samples: 1000 per class
    # Defect rate: ~1.25% per defect type
    # Required: 1000 / 0.0125 = 80,000 boards
    
    'safety_margin': 1.5,                # [NEEDS CITATION] - Safety factor
    
    # Justification:
    # - Based on class imbalance literature [cite]
    # - Ensures sufficient minority class samples
}


# ============================================================================
# RANDOM SEED CONFIGURATION
# ============================================================================

RANDOM_SEED_CONFIG = {
    'default_seed': 42,                  # Standard reproducibility seed
    'use_seed': True,                    # Set False for true randomness
    
    # Note: Seed = 42 is convention for reproducible research
}


# ============================================================================
# CORRELATION MATRIX
# ============================================================================
# Moved from main file for better organization

import numpy as np

# Correlation matrix (5x5)
# Order: PV, Thickness, Viscosity, RH, Temperature
CORRELATION_MATRIX = np.array([
    #  PV     Thk    Visc    RH     Temp
    [ 1.00,  0.80, -0.60,  0.45,  0.20],  # Paste Volume
    [ 0.80,  1.00,  0.00,  0.00,  0.00],  # Stencil Thickness
    [-0.60,  0.00,  1.00, -0.65, -0.70],  # Paste Viscosity
    [ 0.45,  0.00, -0.65,  1.00,  -0.60],  # Ambient RH
    [ 0.20,  0.00, -0.70,  -0.60,  1.00],  # Ambient Temperature
])

# Correlation justifications:
CORRELATION_JUSTIFICATIONS = {
    ('paste_volume', 'stencil_thickness'): {
        'value': 0.80,
        'citation': '[NEEDS CITATION]',
        'reasoning': 'Thicker stencil deposits more paste volume'
    },
    ('paste_volume', 'paste_viscosity'): {
        'value': -0.60,
        'citation': '[NEEDS CITATION]',
        'reasoning': 'Higher viscosity reduces paste release from stencil'
    },
    ('paste_viscosity', 'ambient_rh'): {
        'value': -0.65,
        'citation': '[NEEDS CITATION]',
        'reasoning': 'High humidity reduces effective paste viscosity'
    },
    ('paste_viscosity', 'ambient_temperature'): {
        'value': -0.70,
        'citation': '[NEEDS CITATION]',
        'reasoning': 'Temperature inversely affects viscosity (Arrhenius)'
    },
    ('ambient_rh', 'ambient_temperature'): {
        'value': -0.60,
        'citation': '[NEEDS CITATION]',
        'reasoning': 'Higher temperature reduces relative humidity'
    },
}


# ============================================================================
# OUTPUT CONFIGURATION
# ============================================================================
def get_output_columns_order():
    columns = []
    label_columns = [
        'mech causes',
        'root causes',
        'Defect',
        'Defect_Probability', 
        'Solder Printing Mechanism', 
        'Reflow Mechanism'
    ]
    label_columns = label_columns + [f"{k} risk" for k in PROCESS_PARAMETERS.keys()]
    metadata_columns = ['board_number','hour_of_day','stencil_batch']
    columns = columns + list(PROCESS_PARAMETERS.keys()) + label_columns + metadata_columns
    return columns

OUTPUT_CONFIG = {
    'csv_filename': 'synthetic_data_with_temporal_patterns_x2-{version}.csv',
    'include_metadata': True,            # Include board_number, hour_of_day, etc.
    'include_probabilities': True,       # Include Defect_Probability column
    'perform_labelling': True,
    'columns_order': get_output_columns_order()
}

# ============================================================================
# CITATION REQUIREMENTS
# ============================================================================

def check_citations():
    """
    Check which parameters still need citations
    """
    print("\n" + "="*70)
    print("CITATION CHECKLIST")
    print("="*70)
    
    needs_citation = []
    
    # Check temporal config
    for category, params in TEMPORAL_CONFIG.items():
        for param, value in params.items():
            if isinstance(value, (int, float)):
                needs_citation.append(f"TEMPORAL_CONFIG['{category}']['{param}'] = {value}")
    
    # Check sample size
    for param, value in SAMPLE_SIZE_CONFIG.items():
        if isinstance(value, (int, float)):
            needs_citation.append(f"SAMPLE_SIZE_CONFIG['{param}'] = {value}")
    
    # Check correlations
    for key, info in CORRELATION_JUSTIFICATIONS.items():
        if '[NEEDS CITATION]' in info['citation']:
            needs_citation.append(f"Correlation {key[0]} ↔ {key[1]} = {info['value']}")
    
    print(f"\nFound {len(needs_citation)} parameters needing citations:")
    print()
    
    for i, item in enumerate(needs_citation, 1):
        print(f"{i:2d}. {item}")
    
    print("\n" + "="*70)
    
    return needs_citation


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_generator_params():
    """
    Get all generator parameters in a single dictionary for easy passing
    
    Returns:
        Dictionary with all generator parameters
    """
    return {
        # Stencil drift
        'stencil_initial': TEMPORAL_CONFIG['stencil_drift']['initial_thickness'],
        'stencil_wear_rate': TEMPORAL_CONFIG['stencil_drift']['wear_rate'],
        'stencil_life': TEMPORAL_CONFIG['stencil_drift']['stencil_life'],
        
        # Temperature cycle
        'temp_base': TEMPORAL_CONFIG['temperature_cycle']['base_temp'],
        'temp_amplitude': TEMPORAL_CONFIG['temperature_cycle']['amplitude'],
        'start_hour': TEMPORAL_CONFIG['temperature_cycle']['start_hour'],
        
        # Production
        'boards_per_hour': TEMPORAL_CONFIG['production_rate']['boards_per_hour'],
        
        # Correlation
        'corr_matrix': CORRELATION_MATRIX,
        
        # Random seed
        'random_seed': RANDOM_SEED_CONFIG['default_seed'] if RANDOM_SEED_CONFIG['use_seed'] else None
    }


def get_sample_size(size_type='default'):
    """
    Get configured sample size
    
    Args:
        size_type: 'default' or 'target'
    
    Returns:
        Number of samples to generate
    """
    if size_type == 'default':
        return SAMPLE_SIZE_CONFIG['default_samples']
    elif size_type == 'target':
        return SAMPLE_SIZE_CONFIG['target_samples']
    else:
        raise ValueError(f"Unknown size_type: {size_type}")
