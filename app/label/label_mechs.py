import numpy as np

def assign_mech_labels(samples, process_parameters):
    """
    Assign mechanism labels based on rules
    
    Args:
        samples: Dictionary with parameter arrays
        process_parameters: Dictionary with spec limits
    
    Returns:
        Updated samples dictionary with mechanisms
    """
    # ========================================================================
    # MECHANISM ASSIGNMENT (Your Specified Rules)
    # ========================================================================

    # Get parameter values
    stencil_thickness_vals = samples["Stencil thickness"]
    paste_viscosity_vals = samples["Paste viscosity"]
    ambient_rh_vals = samples["Ambient RH"]
    peak_reflow_temp_vals = samples["Peak reflow temperature"]
    tal_vals = samples['Time above liquidus']
    mech_causes = samples['mech causes']
    
    # Get number of samples
    n_samples = len(stencil_thickness_vals)

    # Get thresholds
    thick_info = process_parameters["Stencil thickness"]
    visc_info = process_parameters["Paste viscosity"]
    rh_info = process_parameters["Ambient RH"]
    reflow_info = process_parameters["Peak reflow temperature"]
    tal_info = process_parameters["Time above liquidus"]

    # Define mechanism rules
    mechanism_rules = [
        {
            'name': 'Aperture Overfill',
            'conditions': [
                # Rule 1: StencilThickness > USL OR PasteViscosity < LSL
                lambda: (stencil_thickness_vals > thick_info['USL']) | 
                       (paste_viscosity_vals < visc_info['LSL']),
                # Rule 2: PasteViscosity < LSL AND AmbientRh > USL
                lambda: (paste_viscosity_vals < visc_info['LSL']) & 
                       (ambient_rh_vals > rh_info['USL'])
            ]
        },
        {
            'name': 'Poor Paste Transfer',
            'conditions': [
                # Rule 3: StencilThickness < LSL OR PasteViscosity > USL
                lambda: (stencil_thickness_vals < thick_info['LSL']) | 
                       (paste_viscosity_vals > visc_info['USL']),
                # Rule 4: AmbientRh < LSL AND PasteViscosity > USL
                lambda: (ambient_rh_vals < rh_info['LSL']) & 
                       (paste_viscosity_vals > visc_info['USL'])
            ]
        },
        {
            'name': 'Excess Reflow Spreading',
            'conditions': [
                # Rule 5: PeakReflowTemperature > USL OR TimeAboveLiquidus > USL
                lambda: (peak_reflow_temp_vals > reflow_info['USL']) | 
                       (tal_vals > tal_info['USL'])
            ]
        },
        {
            'name': 'Non Coalescence',
            'conditions': [
                # Rule 6: PeakReflowTemperature < LSL OR TimeAboveLiquidus > LSL    
                lambda: (peak_reflow_temp_vals < reflow_info['LSL']) | 
                       (tal_vals < tal_info['LSL'])
            ]
        }
    ]

    # Apply rules (vectorized, allows multiple)
    for rule in mechanism_rules:
        mech_name = rule['name'].lower()
        
        # Combine all conditions with OR
        combined_mask = np.zeros(n_samples, dtype=bool)  # FIX: Use n_samples
        for condition_func in rule['conditions']:
            combined_mask |= condition_func()
        
        # Vectorized append
        mech_causes[combined_mask] = np.where(
            mech_causes[combined_mask] == "",
            mech_name,
            mech_causes[combined_mask] + "; " + mech_name
        )
    
    # Update samples dictionary
    samples['mech causes'] = mech_causes
    
    return samples  # FIX: Return samples, not df