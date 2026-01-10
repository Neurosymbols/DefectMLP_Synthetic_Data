import random
import numpy as np
import pandas as pd
from scipy.stats import norm, truncnorm, expon
from datetime import datetime, timedelta

from .helpers.npd import nearest_positive_definite
from .services.stencil_thickness_drift import get_stencil_thickness_drift
from .services.sinusoidal_temp import temperature_diurnal_cycle
from .label.label_defects import assign_defects_to_dataframe
from .label.label_mechs import assign_mech_labels
from .config.parameter_config import PROCESS_PARAMETERS
from .config.generator_config import (
    OUTPUT_CONFIG,
    get_generator_params,
    get_sample_size
)

# ============================================================================
# MAIN GENERATION FUNCTION
# ============================================================================
def sample_with_drift_and_cycles(**kwargs):
    """
        Generate synthetic data with:
        1. Correlated fluctuations (from Gaussian copula)
        2. Temporal patterns (drift for stencil, cycle for temp)
        3. Both combined while maintaining correlations
        
        Returns:
            DataFrame with all parameters including temporal patterns
    """
    n_samples = kwargs.get('n_samples')
    # Use config defaults
    config = get_generator_params()
    #get stencil params
    stencil_initial = config.get('stencil_initial')
    stencil_wear_rate = config.get('stencil_wear_rate')
    stencil_life = config.get('stencil_life')
    
    #get temp params
    temp_base = config.get('temp_base')
    temp_amplitude = config.get('temp_amplitude')
    start_hour = kwargs.get("random_seed") if kwargs.get("random_seed") else config.get('random_seed')
    
    #get throughput params
    boards_per_hour = config.get('boards_per_hour')
    
    #get seed
    if not kwargs.get("random_seed"):
        random_seed = config.get('random_seed')
    else:
        random_seed = kwargs.get("random_seed")
    
    #get correlations
    corr_matrix = config.get('corr_matrix')

    if random_seed is not None:
        np.random.seed(random_seed)
    
    # Ensure positive definite
    corr_matrix = nearest_positive_definite(corr_matrix)

    # ========================================================================
    # STEP 1: Generate correlated standard normals (anomalies/fluctuations)
    # ========================================================================
    
    L = np.linalg.cholesky(corr_matrix)
    z = np.random.randn(n_samples, 5)  # 5 parameters
    correlated_normals = z.dot(L.T)  # Correlated standard normals
    
    # Convert to uniform [0,1] via CDF
    u = norm.cdf(correlated_normals)

    # ========================================================================
    # STEP 2: Generate temporal baselines for temperature and stencil thickness
    # ========================================================================

    board_numbers = np.arange(n_samples)

    # Stencil thickness baseline (drift)
    stencil_baseline = []
    for i in board_numbers:
        drift_data = get_stencil_thickness_drift(
            i, 
            initial_thickness=stencil_initial,
            wear_rate=stencil_wear_rate,
            stencil_life=stencil_life
        )
        stencil_baseline.append(
            drift_data['base thickness']
        )
    stencil_baseline = np.array(stencil_baseline)

    # Temperature baseline (diurnal cycle)
    temp_baseline = []
    for i in board_numbers:
        temp_baseline.append(
            temperature_diurnal_cycle(
                i,
                boards_per_hour=boards_per_hour,
                start_hour=start_hour,
                base_temp=temp_base,
                amplitude=temp_amplitude
            )
        )
    temp_baseline = np.array(temp_baseline)

    # ========================================================================
    # STEP 3: Generate CORRELATED FLUCTUATIONS around baselines
    # ========================================================================
    param_keys = list(PROCESS_PARAMETERS.keys())
    samples = {}

    # --- Paste Volume (index 0) ---
    pv_info = PROCESS_PARAMETERS["Paste volume per aperture"]
    paste_volume = norm.ppf(
        u[:, 0],
        loc=pv_info['NV'],
        scale=pv_info['tolerance'] / pv_info['x']
    )
    samples["Paste volume per aperture"] = paste_volume

    # --- Stencil Thickness (index 1) ---
    # Baseline (drift) + Correlated fluctuation
    thickness_info = PROCESS_PARAMETERS["Stencil thickness"]
    thickness_fluctuation = norm.ppf(
        u[:, 1],
        loc=0,  # Mean 0 (fluctuation around baseline)
        scale=thickness_info['tolerance'] / thickness_info['x']
    )
    stencil_thickness = stencil_baseline + thickness_fluctuation
    samples["Stencil thickness"] = stencil_thickness
    
    # --- Paste Viscosity (index 2) ---
    visc_info = PROCESS_PARAMETERS["Paste viscosity"]
    paste_viscosity = norm.ppf(
        u[:, 2],
        loc=visc_info['NV'],
        scale=visc_info['tolerance'] / visc_info['x']
    )
    samples["Paste viscosity"] = paste_viscosity
    
    # --- Ambient RH (index 3) ---
    rh_info = PROCESS_PARAMETERS["Ambient RH"]
    ambient_rh = norm.ppf(
        u[:, 3],
        loc=rh_info['NV'],
        scale=rh_info['tolerance'] / rh_info['x']
    )
    samples["Ambient RH"] = ambient_rh
    
    # --- Ambient Temperature (index 4) ---
    # Baseline (diurnal cycle) + Correlated fluctuation
    temp_info = PROCESS_PARAMETERS["Ambient temperature"]
    temp_fluctuation = norm.ppf(
        u[:, 4],
        loc=0,  # Mean 0 (fluctuation around baseline cycle)
        scale=temp_info['tolerance'] / temp_info['x']
    )
    ambient_temperature = temp_baseline + temp_fluctuation
    samples["Ambient temperature"] = ambient_temperature

    # ========================================================================
    # STEP 4: Identify out-of-spec conditions and create labels
    # ========================================================================
    
    mech_causes = np.full(n_samples, "", dtype=object)
    root_causes = np.full(n_samples, "", dtype=object)
    out_of_spec = {}
    
    for i, param_key in enumerate(param_keys):
        param_info = PROCESS_PARAMETERS[param_key]
        param_samples = samples[param_key]
        
        out_of_spec[param_key] = {
            "below_lsl": int(np.sum(param_samples < param_info['LSL'])),
            "above_usl": int(np.sum(param_samples > param_info['USL']))
        }
        
        param_high_mask = param_samples > param_info['USL']
        param_low_mask = param_samples < param_info['LSL']
        
        # Mechanism causes (paste volume only)
        if param_key.lower() == "paste volume per aperture":
            mech_causes[param_high_mask] = f"{param_key} high"
            mech_causes[param_low_mask] = f"{param_key} low"
        # Root causes (all other parameters)
        else:
            root_causes[param_high_mask] = np.char.add(
                np.where(root_causes[param_high_mask] == "", "", root_causes[param_high_mask] + "; "),
                f"{param_key} high"
            )
            root_causes[param_low_mask] = np.char.add(
                np.where(root_causes[param_low_mask] == "", "", root_causes[param_low_mask] + "; "),
                f"{param_key} low"
            )
    
    samples['mech causes'] = mech_causes
    samples['root causes'] = root_causes

    samples = assign_mech_labels(samples, PROCESS_PARAMETERS)

    # ========================================================================
    # STEP 5: Create DataFrame with metadata
    # ========================================================================
    
    # Add temporal metadata
    samples['board_number'] = board_numbers
    samples['hour_of_day'] = start_hour + (board_numbers / boards_per_hour)
    samples['stencil_batch'] = board_numbers // stencil_life
    
    # Use configured column order
    columns = [col for col in OUTPUT_CONFIG['columns_order'] if col in samples]
    df = pd.DataFrame(samples)[columns]
    
    print(f"Generated {n_samples} samples")
    print(f"Out-of-spec counts: {out_of_spec}")
    
    return df, out_of_spec, random_seed

def sample_with_drift_and_cycles_and_defects(
        **kwargs
    ):
    """
    Enhanced generator that includes defect labels
    """
    if kwargs.get("n_samples") is None:
        n_samples = get_sample_size('target')
        kwargs["n_samples"] = n_samples
    # Generate base data (your existing function)
    df, out_of_spec, seed = sample_with_drift_and_cycles(**kwargs)
    
    # ========================================================================
    # Generate defect labels from mechanisms
    # ========================================================================
    
    # Approach 1: Hard labels
    df = assign_defects_to_dataframe(df, PROCESS_PARAMETERS, random_seed=seed)
        
    # ========================================================================
    # Statistics
    # ========================================================================
    return df, out_of_spec

if __name__ == "__main__":
    # Generate data with configuration defaults
    df, oos = sample_with_drift_and_cycles_and_defects()
    
    # Save to CSV
    version = 8
    filename = OUTPUT_CONFIG['csv_filename'].format(version=version)
    df.to_csv(filename, index=False)
    
    print(f"\n✓ Data saved to {filename}")