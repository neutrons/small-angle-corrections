"""
Synthetic demonstration of the multiple-scattering correction.

Generates a fuzzy-ball primary profile (R=2, sigma=0.5), simulates the
apparent (multiple-scattered) profile at T=0.5, runs the correction, and
produces a comparison figure plus a CSV suitable for the
`small-angle-corrections correct-ms` CLI.

Note on enforce_nonneg: the fuzzy-ball profile is physically non-negative,
but its Gram-Schmidt polynomial coefficients (alpha1) include negative values.
The coefficient-level non-negativity bound in enforce_nonneg=True would block
the correct solution, so this demo uses enforce_nonneg=False.  For smooth
monotonically-decreasing small-angle scattering profiles, enforce_nonneg=True is appropriate.
"""

from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from small_angle_corrections import AlgebraicConvolutionModel

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
R = 2.0
SIGMA = 0.5
TRANSMISSION = 0.5
N_BASIS = 10
N_ORDERS = 8
N_PHI = 32
NOISE_FRAC = 0.02
SEED = 0

OUT_DIR = Path(__file__).parent / 'data'
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Profile (Q chosen so QR < 4.5, staying in the smooth Guinier + first peak)
# ---------------------------------------------------------------------------

def fuzzy_ball(q, R=R, sigma=SIGMA):
    """Fuzzy-sphere form factor (Pedersen 1994)."""
    x = q * R
    with np.errstate(divide='ignore', invalid='ignore'):
        F = np.where(x < 1e-9, 1.0,
                     3.0 * (np.sin(x) - x * np.cos(x)) / x**3)
    return F**2 * np.exp(-(sigma * q)**2)


q = np.linspace(0.05, 2.1, 80)
I_true = fuzzy_ball(q)

# ---------------------------------------------------------------------------
# Build model and forward-simulate apparent intensity
# ---------------------------------------------------------------------------
model = AlgebraicConvolutionModel(q, n_basis=N_BASIS, n_orders=N_ORDERS,
                                  n_phi=N_PHI)
alpha1_true = model._basis.coefficients(I_true, q * model._length_scale)
I_apparent = model.forward(alpha1_true, transmission=TRANSMISSION, I0=1.0)

rng = np.random.default_rng(SEED)
dI = NOISE_FRAC * np.abs(I_apparent)
I_noisy = np.abs(I_apparent + dI * rng.standard_normal(len(q)))

# ---------------------------------------------------------------------------
# Inversion on the clean forward model (so the figure is unambiguous).
# enforce_nonneg=False because alpha1_true has negative polynomial coefficients
# even though I_true itself is non-negative everywhere.
# ---------------------------------------------------------------------------
out = model.invert(I_apparent, transmission=TRANSMISSION, enforce_nonneg=False)
I_recovered = out['I_true']
I_fit = out['I_fit']

# ---------------------------------------------------------------------------
# Save CSV  (Q, I, dI)  with noise for `small-angle-corrections correct-ms`
# ---------------------------------------------------------------------------
csv_path = OUT_DIR / 'synthetic_reduced_profile.csv'
header = 'Q,I,dI'
np.savetxt(csv_path, np.column_stack([q, I_noisy, dI]),
           delimiter=',', header=header, comments='')
print(f"Saved: {csv_path}")

# ---------------------------------------------------------------------------
# Save figure
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.semilogy(q, I_true,      'k-',  lw=2,   label='True primary')
ax.semilogy(q, I_apparent,  'b--', lw=1.5, label='Apparent (T=0.5)')
ax.semilogy(q, I_fit,       'g:',  lw=1.5, label='Fitted apparent')
ax.semilogy(q, I_recovered, 'r-',  lw=2,   label='Recovered primary')
ax.set_xlabel('Q (a.u.)')
ax.set_ylabel('Intensity (a.u.)')
ax.set_title(f'Multiple-scattering correction  (R={R}, σ={SIGMA}, T={TRANSMISSION})')
ax.legend()
ax.grid(True, which='both', alpha=0.3)
fig.tight_layout()

fig_path = OUT_DIR / 'synthetic_demo.png'
fig.savefig(fig_path, dpi=150)
print(f"Saved: {fig_path}")

mean_true = np.mean(I_true)
rms_app = np.sqrt(np.mean((I_apparent - I_true)**2)) / mean_true
rms_rec = np.sqrt(np.mean((I_recovered - I_true)**2)) / mean_true
print(f"RMS relative error  apparent vs true : {rms_app:.1%}")
print(f"RMS relative error  recovered vs true: {rms_rec:.1%}")
print(f"I0 recovered: {out['I0']:.4f}  (expected ~1.0)")
