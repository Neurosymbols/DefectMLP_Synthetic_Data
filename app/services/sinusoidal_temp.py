import numpy as np
import pandas as pd

def temperature_diurnal_cycle(board_number,
                              boards_per_hour=120,
                              start_hour=6,  # 6 AM shift start
                              base_temp=23.0,
                              amplitude=2.0,  # ±2°C daily swing
                              peak_hour=14):  # 2 PM peak
    """
    Temperature diurnal cycle (daily pattern)
    
    Returns only the TEMPORAL component (cycle)
    Correlated fluctuations will be added separately
    """
    # What hour of day is this board?
    hours_elapsed = board_number / boards_per_hour
    hour_of_day = (start_hour + hours_elapsed) % 24
    
    # Sinusoidal daily cycle (peaks at 2 PM). Dividing by 24 makes the sine wave complete its full cycle in 24 hours
    #y = 2*pi*r
    phase = 2 * np.pi * ((hour_of_day - peak_hour) / 24)
    # multiplying by amplitude scales the temp to oscillate between -2 -> +2 range with units in degree celsius
    cycle_component = amplitude * np.cos(phase)
    
    return base_temp + cycle_component