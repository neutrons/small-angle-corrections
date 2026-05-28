"""Generate synthetic USANS data: fuzzy-ball scatterer at T=0.5."""

import numpy as np
from pathlib import Path


def fuzzy_ball(q, R=500.0, sigma=50.0, A=1.0):
    """Fuzzy-sphere form factor (normalized)."""
    x = q * R
    with np.errstate(divide='ignore', invalid='ignore'):
        F = np.where(x < 1e-8, 1.0,
                     3.0 * (np.sin(x) - x * np.cos(x)) / x**3)
    return A * F**2 * np.exp(-(sigma * q)**2)


def make_synthetic(n_q=80, q_min=1e-4, q_max=1e-2,
                   transmission=0.5, noise_frac=0.02, seed=42):
    rng = np.random.default_rng(seed)
    q = np.geomspace(q_min, q_max, n_q)
    I_true = fuzzy_ball(q)

    from usans_correct import AlgebraicConvolutionModel
    model = AlgebraicConvolutionModel(q, n_basis=8, n_orders=8)
    alpha1 = model._basis.coefficients(I_true, q * model._length_scale)
    I_apparent = model.forward(alpha1, transmission, I0=1.0)

    noise = noise_frac * np.abs(I_apparent) * rng.standard_normal(n_q)
    I_apparent_noisy = np.abs(I_apparent + noise)

    return q, I_true, I_apparent, I_apparent_noisy


if __name__ == '__main__':
    outdir = Path(__file__).parent.parent / 'data' / 'synthetic'
    outdir.mkdir(parents=True, exist_ok=True)

    q, I_true, I_app, I_noisy = make_synthetic()

    np.savetxt(outdir / 'fuzzy_ball_T0p5_apparent.txt',
               np.column_stack([q, I_noisy]),
               header='Q(Ang^-1)  I_apparent')
    np.savetxt(outdir / 'fuzzy_ball_T0p5_true.txt',
               np.column_stack([q, I_true]),
               header='Q(Ang^-1)  I_true')
    np.savez(outdir / 'fuzzy_ball_T0p5.npz',
             q=q, I_true=I_true, I_apparent=I_app, I_apparent_noisy=I_noisy)
    print(f"Saved synthetic data to {outdir}")
