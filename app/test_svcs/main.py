import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import norm

# mean = 0.100
# x = 3
# tol = 0.005
# LSL = 0.095
# USL = 0.105

mean = 0.040
x = 3
tol = 0.004
LSL = 0.036
USL = 0.044

def sample_excess_paste_volume(n_samples):
    u = np.random.rand(n_samples)
    return norm.ppf(u, loc=mean, scale=(tol/x))

# Generate samples
samples = sample_excess_paste_volume(50000)

# Count below LSL and above USL
below_lsl = np.sum(samples < LSL)
above_usl = np.sum(samples > USL)

print("Below LSL:", below_lsl)
print("Above USL:", above_usl)
print("Total Out-of-Spec:", below_lsl + above_usl)