import numpy as np
# ============================================================================
# CONFIGURATION
# ============================================================================

PROCESS_PARAMETERS = {
    "Paste volume per aperture": {
        "NV": 0.04, 
        "tolerance": 0.004,
        "USL": 0.044,
        "LSL": 0.036, 
        "x": 2.3
    },
    "Stencil thickness": {
        "NV": 100, 
        "tolerance": 5, 
        "USL": 105, 
        "LSL": 95, 
        "x": 2.3
    },
    "Paste viscosity": {
        "NV": 200, 
        "tolerance": 50, 
        "USL": 250, 
        "LSL": 150, 
        "x": 2.3
    },
    "Ambient RH": {
        "NV": 40, 
        "tolerance": 10, 
        "USL": 50, 
        "LSL": 30, 
        "x": 2.3
    },
    "Ambient temperature": {
        "NV": 23, 
        "tolerance": 3, 
        "USL": 26, 
        "LSL": 20, 
        "x": 2.3
    }
}