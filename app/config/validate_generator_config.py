import numpy as np
from .generator_config import SAMPLE_SIZE_CONFIG, TEMPORAL_CONFIG, CORRELATION_MATRIX
# ============================================================================
# VALIDATION FUNCTIONS (Non-Blocking)
# ============================================================================

def validate_temporal_config():
    """
    Validate temporal configuration parameters
    
    Returns:
        (is_valid, issues_list)
    """
    issues = []
    
    stencil = TEMPORAL_CONFIG['stencil_drift']
    temp = TEMPORAL_CONFIG['temperature_cycle']
    prod = TEMPORAL_CONFIG['production_rate']
    
    # Stencil validation
    if stencil['initial_thickness'] <= 0:
        issues.append({
            'severity': 'ERROR',
            'parameter': 'stencil_drift.initial_thickness',
            'value': stencil['initial_thickness'],
            'issue': 'Initial thickness must be positive',
            'action': 'Set initial_thickness > 0 (typical: 95-105 µm)'
        })
    
    if stencil['wear_rate'] <= 0:
        issues.append({
            'severity': 'ERROR',
            'parameter': 'stencil_drift.wear_rate',
            'value': stencil['wear_rate'],
            'issue': 'Wear rate must be positive',
            'action': 'Set wear_rate > 0 (typical: 0.0005-0.002 µm/board)'
        })
    
    if stencil['stencil_life'] <= 0:
        issues.append({
            'severity': 'ERROR',
            'parameter': 'stencil_drift.stencil_life',
            'value': stencil['stencil_life'],
            'issue': 'Stencil life must be positive',
            'action': 'Set stencil_life > 0 (typical: 3000-10000 boards)'
        })
    
    # Temperature validation
    if not (15 <= temp['base_temp'] <= 30):
        issues.append({
            'severity': 'WARNING',
            'parameter': 'temperature_cycle.base_temp',
            'value': temp['base_temp'],
            'issue': 'Base temperature outside typical range (15-30°C)',
            'action': 'Verify base_temp is reasonable for factory environment'
        })
    
    if not (0 < temp['amplitude'] < 5):
        issues.append({
            'severity': 'WARNING',
            'parameter': 'temperature_cycle.amplitude',
            'value': temp['amplitude'],
            'issue': 'Temperature amplitude outside typical range (0-5°C)',
            'action': 'Verify amplitude matches daily temperature variation'
        })
    
    if not (0 <= temp['start_hour'] < 24):
        issues.append({
            'severity': 'ERROR',
            'parameter': 'temperature_cycle.start_hour',
            'value': temp['start_hour'],
            'issue': 'Start hour must be 0-23',
            'action': 'Set start_hour to valid hour (typical: 6-8 for first shift)'
        })
    
    # Production validation
    if prod['boards_per_hour'] <= 0:
        issues.append({
            'severity': 'ERROR',
            'parameter': 'production_rate.boards_per_hour',
            'value': prod['boards_per_hour'],
            'issue': 'Production rate must be positive',
            'action': 'Set boards_per_hour > 0 (typical: 200-400 boards/hour)'
        })
    
    is_valid = all(issue['severity'] != 'ERROR' for issue in issues)
    
    return is_valid, issues

def validate_correlation_matrix():
    """
    Validate correlation matrix properties
    
    Returns:
        (is_valid, issues_list)
    """
    issues = []
    
    # Check symmetry
    if not np.allclose(CORRELATION_MATRIX, CORRELATION_MATRIX.T):
        issues.append({
            'severity': 'ERROR',
            'parameter': 'CORRELATION_MATRIX',
            'value': 'Matrix',
            'issue': 'Correlation matrix must be symmetric',
            'action': 'Ensure matrix[i,j] = matrix[j,i] for all i,j'
        })
    
    # Check diagonal is all 1s
    if not np.allclose(np.diag(CORRELATION_MATRIX), 1.0):
        issues.append({
            'severity': 'ERROR',
            'parameter': 'CORRELATION_MATRIX',
            'value': 'Diagonal',
            'issue': 'Diagonal elements must be 1.0',
            'action': 'Set all diagonal elements to 1.0'
        })
    
    # Check values in [-1, 1]
    if not np.all(np.abs(CORRELATION_MATRIX) <= 1.0):
        issues.append({
            'severity': 'ERROR',
            'parameter': 'CORRELATION_MATRIX',
            'value': 'Values',
            'issue': 'Correlation values must be in [-1, 1]',
            'action': 'Ensure all correlations are between -1 and 1'
        })
    
    # Check positive semi-definite
    try:
        eigenvalues = np.linalg.eigvals(CORRELATION_MATRIX)
        if not np.all(eigenvalues >= -1e-10):
            issues.append({
                'severity': 'ERROR',
                'parameter': 'CORRELATION_MATRIX',
                'value': f'Min eigenvalue: {eigenvalues.min():.6f}',
                'issue': 'Matrix is not positive semi-definite',
                'action': 'Adjust correlations or use nearest_positive_definite()'
            })
    except np.linalg.LinAlgError:
        issues.append({
            'severity': 'ERROR',
            'parameter': 'CORRELATION_MATRIX',
            'value': 'Matrix',
            'issue': 'Cannot compute eigenvalues',
            'action': 'Check matrix for numerical issues'
        })
    
    is_valid = all(issue['severity'] != 'ERROR' for issue in issues)
    
    return is_valid, issues

def validate_sample_size_config():
    """
    Validate sample size configuration
    
    Returns:
        (is_valid, issues_list)
    """
    issues = []
    
    if SAMPLE_SIZE_CONFIG['default_samples'] <= 0:
        issues.append({
            'severity': 'ERROR',
            'parameter': 'default_samples',
            'value': SAMPLE_SIZE_CONFIG['default_samples'],
            'issue': 'Default samples must be positive',
            'action': 'Set default_samples > 0 (typical: 5000-10000)'
        })
    
    if SAMPLE_SIZE_CONFIG['target_samples'] < SAMPLE_SIZE_CONFIG['default_samples']:
        issues.append({
            'severity': 'WARNING',
            'parameter': 'target_samples',
            'value': SAMPLE_SIZE_CONFIG['target_samples'],
            'issue': 'Target samples should be >= default samples',
            'action': 'Increase target_samples or decrease default_samples'
        })
    
    if SAMPLE_SIZE_CONFIG['safety_margin'] < 1.0:
        issues.append({
            'severity': 'WARNING',
            'parameter': 'safety_margin',
            'value': SAMPLE_SIZE_CONFIG['safety_margin'],
            'issue': 'Safety margin should be >= 1.0',
            'action': 'Set safety_margin >= 1.0 (typical: 1.5-2.0)'
        })
    
    is_valid = all(issue['severity'] != 'ERROR' for issue in issues)
    
    return is_valid, issues

def validate_all_generator_config(verbose=True):
    """
    Run all validation checks and collect issues
    
    Args:
        verbose: If True, print detailed report
    
    Returns:
        (is_valid, all_issues)
    """
    all_issues = []
    
    # Run all validations
    temporal_valid, temporal_issues = validate_temporal_config()
    correlation_valid, correlation_issues = validate_correlation_matrix()
    sample_valid, sample_issues = validate_sample_size_config()
    
    all_issues.extend(temporal_issues)
    all_issues.extend(correlation_issues)
    all_issues.extend(sample_issues)
    
    # Overall validity (no ERRORS)
    is_valid = temporal_valid and correlation_valid and sample_valid
    
    if verbose:
        print_validation_report(is_valid, all_issues)
    
    return is_valid, all_issues

def print_validation_report(is_valid, issues):
    """
    Print formatted validation report
    """
    print("="*70)
    print("GENERATOR CONFIGURATION VALIDATION REPORT")
    print("="*70)
    print()
    
    if not issues:
        print("✓ All validations passed - configuration is ready!")
        print("="*70)
        return
    
    # Separate by severity
    errors = [i for i in issues if i['severity'] == 'ERROR']
    warnings = [i for i in issues if i['severity'] == 'WARNING']
    
    # Print errors
    if errors:
        print("❌ ERRORS (Must fix before generation):")
        print("-"*70)
        for i, error in enumerate(errors, 1):
            print(f"\n{i}. {error['parameter']}")
            print(f"   Value: {error['value']}")
            print(f"   Issue: {error['issue']}")
            print(f"   Action: {error['action']}")
        print()
    
    # Print warnings
    if warnings:
        print("⚠️  WARNINGS (Should review):")
        print("-"*70)
        for i, warning in enumerate(warnings, 1):
            print(f"\n{i}. {warning['parameter']}")
            print(f"   Value: {warning['value']}")
            print(f"   Issue: {warning['issue']}")
            print(f"   Action: {warning['action']}")
        print()
    
    # Summary
    print("="*70)
    print("SUMMARY:")
    print(f"  Errors:   {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    print()
    
    if is_valid:
        print("✓ Configuration is VALID (warnings only)")
        print("  You can proceed with generation, but review warnings.")
    else:
        print("✗ Configuration is INVALID")
        print("  Fix all errors before proceeding with data generation.")
    
    print("="*70)

# ============================================================================
# MAIN - FOR TESTING
# ============================================================================

if __name__ == "__main__":
    # Run complete pre-generation checklist
    is_valid, issues_list = validate_all_generator_config()
    print_validation_report(is_valid, issues_list)
    
    if not is_valid:
        print("\n⚠️  Fix errors before proceeding with data generation!")

