"""
Version 1: Simplified Hardcoded Magnitude-Based Mechanism Labeling

Assigns mechanisms based on which parameter deviation is more severe.
Uses normalized deviations (deviation / tolerance) for fair comparison.

This version is hardcoded for clarity and understanding.
"""

import numpy as np


def assign_mech_labels_latest(samples, process_parameters):
    """
    Assign mechanism labels using magnitude comparison (HARDCODED VERSION)
    
    Logic:
    - Calculate normalized deviations for each parameter
    - Compare overfill score vs poor transfer score
    - Assign mechanism based on dominant score
    
    Args:
        samples: Dictionary with parameter arrays
        process_parameters: Dictionary with spec limits
    
    Returns:
        Updated samples dictionary with mechanisms
    """
    n_samples = len(samples["Stencil thickness"])
    
    # Get parameter arrays
    paste_volume = samples['Paste volume per aperture']
    stencil_thickness = samples["Stencil thickness"]
    paste_viscosity = samples["Paste viscosity"]
    ambient_rh = samples["Ambient RH"]
    peak_reflow_temp = samples["Peak reflow temperature"]
    tal = samples['Time above liquidus']
    
    # Get specs (hardcoded keys)
    paste_vol_specs = process_parameters['Paste volume per aperture']
    stencil_specs = process_parameters["Stencil thickness"]
    visc_specs = process_parameters["Paste viscosity"]
    rh_specs = process_parameters["Ambient RH"]
    reflow_specs = process_parameters["Peak reflow temperature"]
    tal_specs = process_parameters["Time above liquidus"]

    # Initialize mechanism arrays
    printing_mechanism = np.full(n_samples, "no printing mech", dtype=object)
    reflow_mechanism = np.full(n_samples, "no reflow mech", dtype=object)
    samples['Solder Printing Mechanism'] = printing_mechanism
    samples['Reflow Mechanism'] = reflow_mechanism

    # ========================================================================
    # PRINTING STAGE MECHANISMS
    # ========================================================================
    
    for i in range(n_samples):
        # --------------------------------------------------------------------
        # Calculate Overfill Score
        # --------------------------------------------------------------------
        
        # Overfill Indicator 1: High paste volume
        paste_vol_excess_dev = max(0, paste_volume[i] - paste_vol_specs['USL']) / paste_vol_specs['tolerance']

        # Overfill Indicator 2: High stencil thickness
        stencil_overfill_dev = max(0, stencil_thickness[i] - stencil_specs['USL']) / stencil_specs['tolerance']
        
        # Overfill Indicator 3: Low paste viscosity
        visc_overfill_dev = max(0, visc_specs['LSL'] - paste_viscosity[i]) / visc_specs['tolerance']
        
        # Overfill Indicator 3: Low viscosity AND high RH
        if paste_viscosity[i] < visc_specs['LSL'] and ambient_rh[i] > rh_specs['USL']:
            # Both conditions met - use combined deviation
            visc_rh_overfill_dev = (visc_overfill_dev + 
                                    max(0, ambient_rh[i] - rh_specs['USL']) / rh_specs['tolerance']) / 2
        else:
            visc_rh_overfill_dev = 0
    
        # Aggregate overfill score (take maximum of all indicators)
        overfill_score = max(
            paste_vol_excess_dev, 
            stencil_overfill_dev, 
            visc_overfill_dev, 
            visc_rh_overfill_dev
        )
        
        # --------------------------------------------------------------------
        # Calculate Poor Transfer Score
        # --------------------------------------------------------------------    

        # Poosr Transfer Indicator 1: Low paste volume
        paste_vol_low_dev = max(0, paste_vol_specs['LSL'] - paste_volume[i]) / paste_vol_specs['tolerance']

        # Poor Transfer Indicator 2: Low stencil thickness
        stencil_poor_dev = max(0, stencil_specs['LSL'] - stencil_thickness[i]) / stencil_specs['tolerance']
        
        # Poor Transfer Indicator 3: High paste viscosity
        visc_poor_dev = max(0, paste_viscosity[i] - visc_specs['USL']) / visc_specs['tolerance']
        
        # Poor Transfer Indicator 3: Low RH AND high viscosity
        if ambient_rh[i] < rh_specs['LSL'] and paste_viscosity[i] > visc_specs['USL']:
            # Both conditions met - use combined deviation
            rh_visc_poor_dev = (max(0, rh_specs['LSL'] - ambient_rh[i]) / rh_specs['tolerance'] + 
                               visc_poor_dev) / 2
        else:
            rh_visc_poor_dev = 0
        
        # Aggregate poor transfer score (take maximum of all indicators)
        poor_transfer_score = max(
            paste_vol_low_dev, 
            stencil_poor_dev, 
            visc_poor_dev, 
            rh_visc_poor_dev
        )

        # --------------------------------------------------------------------
        # Assign Mechanism Based on Dominant Score
        # --------------------------------------------------------------------
        
        if overfill_score > poor_transfer_score and overfill_score > 0:
            printing_mechanism[i] = "aperture overfill"
        elif poor_transfer_score > overfill_score and poor_transfer_score > 0:
            printing_mechanism[i] = "poor paste transfer"

    
    # ========================================================================
    # REFLOW STAGE MECHANISMS
    # ========================================================================
    
    for i in range(n_samples):
        
        # --------------------------------------------------------------------
        # Calculate Excess Spreading Score
        # --------------------------------------------------------------------

        # Indicator 1: High peak reflow temperature
        peak_temp_excess_dev = max(0, peak_reflow_temp[i] - reflow_specs['USL']) / reflow_specs['tolerance']
        
        # Indicator 2: High time above liquidus
        tal_excess_dev = max(0, tal[i] - tal_specs['USL']) / tal_specs['tolerance']
        
        # Aggregate (take maximum)
        excess_spreading_score = max(peak_temp_excess_dev, tal_excess_dev)

        # --------------------------------------------------------------------
        # Calculate Non-Coalescence Score
        # --------------------------------------------------------------------
        
        # Indicator 1: Low peak reflow temperature
        peak_temp_non_coal_dev = max(0, reflow_specs['LSL'] - peak_reflow_temp[i]) / reflow_specs['tolerance']
        
        # Indicator 2: Low time above liquidus
        tal_non_coal_dev = max(0, tal_specs['LSL'] - tal[i]) / tal_specs['tolerance']
        
        # Aggregate (take maximum)
        non_coalescence_score = max(peak_temp_non_coal_dev, tal_non_coal_dev)
        
        # --------------------------------------------------------------------
        # Assign Mechanism Based on Dominant Score
        # --------------------------------------------------------------------
        
        if excess_spreading_score > non_coalescence_score and excess_spreading_score > 0:
            reflow_mechanism[i] = "excess reflow spreading"
        elif non_coalescence_score > excess_spreading_score and non_coalescence_score > 0:
            reflow_mechanism[i] = "non coalescence"

    # ========================================================================
    # COMBINE MECHANISMS
    # ========================================================================
    
    mech_causes = samples['mech causes']
    
    for i in range(n_samples):
        mechs = []
        if printing_mechanism[i] != "":
            mechs.append(printing_mechanism[i])
        if reflow_mechanism[i] != "":
            mechs.append(reflow_mechanism[i])
        mechs = [c for c in mechs if c not in ["no printing mech", "no reflow mech"]]
        if len(mech_causes[i].strip()) > 0:
            org_mech_causes = [c.strip() for c in mech_causes[i].split(";")]
            total_mech_causes = org_mech_causes + mechs
            mech_causes[i] = "; ".join(total_mech_causes)
        else:
            mech_causes[i] = "; ".join(mechs)
    return samples