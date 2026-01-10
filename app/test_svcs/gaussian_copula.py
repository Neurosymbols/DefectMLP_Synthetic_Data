import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import re

from scipy.stats import norm, truncnorm, expon

process_parameters = {
    "Paste volume per aperture": {"NV": 0.04, "USL": 0.044, "LSL": 0.036, "dist": "expon", "target_oos": 0.003},
    "Stencil thickness": {"NV": 0.100, "tolerance": 0.005, "USL": 0.105, "LSL": 0.095, "x": 3},
    # "Squeegee speed": {"NV": 70, "tolerance": 14, "USL": 84, "LSL": 56, "x": 3},
    # "Squeegee angle": {"NV": 60, "tolerance": 5, "USL": 65, "LSL": 55, "x": 3},
    # "Paste roll bead size": {"NV": 4, "tolerance": 0.4, "USL": 4.4, "LSL": 3.6, "x": 3},
    "Paste viscosity": {"NV": 200, "tolerance": 50, "USL": 250, "LSL": 150, "x": 3},
    "Ambient RH": {"NV": 40, "tolerance": 10, "USL": 50, "LSL": 30, "x": 3}
}

#tol/x (manufacturing capability) ->
#co-variance (physics) -> 
#Cpk = [USL - mean] / 3*sigma 

#keeping tol/x constant, increasing coefficient(of directly/indirectly related params) increases their probability to go out of spec together in same or opposite direction depending on direction of their relation.
#keeping coefficients constant, increasing/decreasing "x" will decrease/increase out of spec events respectively
#allow enough out of spec events to occur to let the correlation play its part.

def is_positive_definite(X):
    try:
        np.linalg.cholesky(X)
        return True
    except np.linalg.LinAlgError:
        return False

def nearest_positive_definite(A):
    """
    Returns the nearest Positive Definite matrix to A using Higham's algorithm.
    """
    B = (A + A.T) / 2
    _, s, V = np.linalg.svd(B)
    H = np.dot(V.T * s, V)
    A2 = (B + H) / 2
    A3 = (A2 + A2.T) / 2

    if is_positive_definite(A3):
        return A3

    spacing = np.spacing(np.linalg.norm(A))
    I = np.eye(A.shape[0])
    k = 1
    while not is_positive_definite(A3):
        mineig = np.min(np.real(np.linalg.eigvals(A3)))
        A3 += I * (-mineig * k**2 + spacing)
        k += 1

    return A3

# ---------- Method 1: Gaussian copula ----------
def sample_with_copula(
        n_samples,
        corr_matrix=None, 
        random_seed=None
    ):
    """
    Returns:
      samples: dict with arrays for 'paste', 'thickness', 'angle'
      counts: dict with counts and conditional probabilities showing the tendency
    Notes:
      - corr_matrix is 7x7 correlation matrix for the latent standard normals in order
        [paste, thickness, angle]. If None, default honors your textual strengths:
          corr(paste,thickness)=+0.80 (strong)
          corr(paste,angle)   =-0.50 (moderate negative)
          corr(thickness,angle)=-0.30 (weaker negative)
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    # default correlation matrix if none provided
    if corr_matrix is None:
        #this corr matrix needs to positive definite
        corr_matrix = np.array([
            #  PV     Thk    Visc    Hum
            [ 1.00,   0.80, -0.85,   0.80],  # Paste Volume
            [ 0.80,   1.00,  0.00,   0.00],  # Stencil Thickness
            [-0.85,   0.00,  1.00,  -0.95],  # Paste Viscosity
            [ 0.80,   0.00, -0.95,   1.00],  # Ambient RH
        ])

    # Cholesky to convert independent normals into correlated normals
    corr_matrix = nearest_positive_definite(corr_matrix)
    L = np.linalg.cholesky(corr_matrix)
    print(L)

    # sample independent standard normals
    z = np.random.randn(n_samples, 4)

    #correlated normals
    #these are correlated gaussian factors that define the hidden random process that drives each variable
    #they are in standard normal distribution(mean=0, SD=1)
    #They are signals that encode how paste, thickness, angle move together
    correlated = z.dot(L.T)  # shape (n_samples, 3)

    # map standard normal -> Uniform(0,1) via CDF, then to marginals via inverse CDF (ppf)
    u = norm.cdf(correlated)  # uniforms in (0,1), same shape

    param_keys = list(process_parameters.keys())
    correlated_samples = {'mech causes': [], 'root causes': []}
    mech_causes = np.full(n_samples, "", dtype=object)
    root_causes = np.full(n_samples, "", dtype=object)
    out_of_spec = {}
    for i in range(len(param_keys)):
        param_info = process_parameters[param_keys[i]]
        dist_type = param_info.get('dist', 'norm')
        if dist_type == "expon":
            target_oos = param_info['target_oos']
            delta = param_info['USL'] - param_info['NV']
            lam = -np.log(target_oos) / delta
            Y = expon.ppf(u[:,i], scale=1/lam)
            param_samples = param_info['NV'] + Y
        else:
            param_samples = norm.ppf(
                u[:,i], 
                loc=param_info['NV'], 
                scale=param_info['tolerance'] / param_info['x']
            )
        out_of_spec[param_keys[i]] = {
            "below_lsl": int(np.sum(param_samples < param_info['LSL'])),
            "above_usl": int(np.sum(param_samples > param_info['USL']))
        }
        correlated_samples[param_keys[i]] = param_samples
        param_high_mask = param_samples > process_parameters[param_keys[i]]['USL']
        param_low_mask = param_samples < process_parameters[param_keys[i]]['LSL']
        if param_keys[i].lower() == "paste volume per aperture":
            mech_causes[param_high_mask] = f"{param_keys[i]} high"
            mech_causes[param_low_mask]  = f"{param_keys[i]} low"
            correlated_samples['mech causes'] = mech_causes
        else:
            root_causes[param_high_mask] = np.char.add(
                np.where(root_causes[param_high_mask] == "", "", root_causes[param_high_mask] + "; "),
                f"{param_keys[i]} high"
            )
            root_causes[param_low_mask]  = np.char.add(
                np.where(root_causes[param_low_mask] == "", "", root_causes[param_low_mask] + "; "),
                f"{param_keys[i]} low"
            )
            correlated_samples['root causes'] = root_causes

    #verify correlation
    empirical_corr = np.corrcoef(correlated.T)
    print("######")
    #The empirical correlation will be extremely close (within ±0.01), because of 200k samples.
    #empirical correlation will keeping coming closer to the corr_matrix taken as you increase the sample size
    print(empirical_corr)

    latent_df = pd.DataFrame(correlated, columns=[
        [f"latent {k}" for k in list(process_parameters.keys())]
    ])
    # sns.pairplot(latent_df, diag_kind="kde")
    # plt.savefig("gaussian_copula_latent_pairplot.png", dpi=300, bbox_inches='tight')

    # plt.figure(figsize=(6,4))
    # sns.heatmap(latent_df.corr(), annot=True, cmap="coolwarm", vmin=-1, vmax=1)
    # plt.savefig("gaussian_copula_latent_corr_heatmap.png", dpi=300, bbox_inches='tight')
    # plt.close()

    corr_df = pd.DataFrame(correlated_samples)
    desired_order = list(process_parameters.keys())
    desired_order.extend(['mech causes', 'root causes'])
    corr_df = corr_df[desired_order]
    count = corr_df[
        corr_df["mech causes"].notna() & 
        corr_df["root causes"].notna() & 
        (corr_df["mech causes"] != "") & 
        (corr_df["root causes"] != "")
    ].shape[0]
    print(count)
    latent_df.to_csv("./app/correlated_normals.csv")
    corr_df.to_csv("./app/correlated_samples.csv")
    return {"count": count, "out_of_spec": out_of_spec}

# sample_with_copula(10000, random_seed=76)

i = 41
data = []
out_of_spec_data = []
while i < 42:
    print(i)
    res = sample_with_copula(10000, random_seed=i)
    out_of_spec_data.append({**res['out_of_spec'], **{"seed": i, "count": res['count']}})
    data.append({"seed": i, "count": res['count']})
    i += 1
with open("./counts.json", "w") as f:
    json.dump(data, f, indent = 2)

with open("./out_of_spec.json", "w") as f:
    json.dump(out_of_spec_data, f, indent = 2)