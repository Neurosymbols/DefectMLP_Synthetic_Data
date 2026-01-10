import numpy as np
import pandas as pd

# ============================================================================
# TEMPORAL PATTERN FUNCTIONS
# ============================================================================
def get_stencil_thickness_drift(board_number, 
                           initial_thickness=100.0,
                           wear_rate=0.001,  # μm per board
                           stencil_life=5000,  # boards per stencil
                           manufacturing_variation=1.0):  # ±1 μm per new stencil
    """
    Stencil thickness with monotonic wear and periodic replacement
    
    Returns only the TEMPORAL component (drift)
    Correlated fluctuations will be added separately
    """
    # Which stencil batch are we on?
    batch_number = board_number // stencil_life
    boards_in_current_batch = board_number % stencil_life
    
    # Each new stencil has manufacturing variation
    np.random.seed(batch_number)  # Reproducible per batch
    batch_offset = np.random.normal(0, manufacturing_variation)
    np.random.seed(None)  # Reset seed
    
    # Wear within current batch
    wear = wear_rate * boards_in_current_batch
    
    # Base thickness for this board (temporal component only)
    base_thickness = initial_thickness + batch_offset - wear
    
    return {
        "batch number": batch_number,
        "boards in current batch": boards_in_current_batch,
        "wear": wear,
        "base thickness": base_thickness
    }

# board_number = 0
# total_boards = 100
# thickness_data = []
# for i in range(total_boards):
#     thickness_dict = get_stencil_thickness_drift(board_number)
#     thickness_data.append(thickness_dict)
#     board_number += 1
# df = pd.DataFrame(thickness_data)
# df.to_csv("./stencil_thickess_batch_0_drift.csv")