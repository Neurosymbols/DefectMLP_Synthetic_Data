"""
Defect Probability Calculation Configuration

All parameters are configurable and should be justified with citations.
"""

# ============================================================================
# DEFECT PROBABILITY WEIGHTS
# ============================================================================

DEFECT_WEIGHTS = {
    'solder_bridging': {
        # Primary factor (paste volume high)
        'primary_weight': 0.50,          # [NEEDS CITATION] - Contribution from paste volume
        
        # Contributing factors weight
        'contributing_weight': 0.18,     # [NEEDS CITATION] - Total contribution from other params
        
        # Baseline probability
        'baseline': 0.30,                # [NEEDS CITATION] - Minimum probability even at nominal
        
        # Individual factor weights (must sum to 1.0)
        'factor_weights': {
            'stencil': 0.35,             # [NEEDS CITATION] - Stencil thickness has strongest effect
            'viscosity': 0.25,           # [NEEDS CITATION] - Viscosity contribution
            'rh': 0.20,                  # [NEEDS CITATION] - Humidity effect
            'temperature': 0.20          # [NEEDS CITATION] - Temperature effect
        },
        
        # Maximum probability cap
        'max_probability': 0.98          # [NEEDS CITATION] - Never 100% certain
    },
    
    'open_circuit': {
        # Primary factor (paste volume low)
        'primary_weight': 0.50,          # [NEEDS CITATION]
        
        # Contributing factors weight
        'contributing_weight': 0.18,     # [NEEDS CITATION]
        
        # Baseline probability
        'baseline': 0.30,                # [NEEDS CITATION]
        
        # Individual factor weights (must sum to 1.0)
        'factor_weights': {
            'stencil': 0.25,             # [NEEDS CITATION]
            'viscosity': 0.35,           # [NEEDS CITATION]
            'rh': 0.20,                  # [NEEDS CITATION]
            'temperature': 0.20          # [NEEDS CITATION]
        },
        
        # Maximum probability cap
        'max_probability': 0.98          # [NEEDS CITATION]
    }
}


# ============================================================================
# PARAMETER MAPPINGS
# ============================================================================

# Map internal column names to config keys
PARAMETER_MAPPING = {
    'Paste volume per aperture': 'paste_volume',
    'Stencil thickness': 'stencil',
    'Paste viscosity': 'viscosity',
    'Ambient RH': 'rh',
    'Ambient temperature': 'temperature'
}


# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """
    Validate that configuration is internally consistent
    """
    for defect_type, config in DEFECT_WEIGHTS.items():
        # Check factor weights sum to 1.0
        factor_sum = sum(config['factor_weights'].values())
        assert abs(factor_sum - 1.0) < 0.001, \
            f"{defect_type}: Factor weights must sum to 1.0, got {factor_sum}"
        
        # Check probabilities are in valid range
        assert 0 <= config['baseline'] <= 1, \
            f"{defect_type}: Baseline must be 0-1, got {config['baseline']}"
        
        assert 0 <= config['max_probability'] <= 1, \
            f"{defect_type}: Max probability must be 0-1, got {config['max_probability']}"
        
        # Check weights are positive
        assert config['primary_weight'] >= 0, \
            f"{defect_type}: Primary weight must be >= 0"
        
        assert config['contributing_weight'] >= 0, \
            f"{defect_type}: Contributing weight must be >= 0"
    
    print("✓ Configuration validation passed")


if __name__ == "__main__":
    validate_config()