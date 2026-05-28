"""Convenience wrapper for single-call correction."""

import numpy as np
from .model import AlgebraicConvolutionModel


def correct(q, I_apparent, transmission, n_basis=8, n_orders=10,
            length_scale=None, enforce_nonneg=True, n_phi=32):
    """
    Apply multiple-scattering correction to a USANS intensity curve.

    Parameters
    ----------
    q : array-like, shape (n_q,)
    I_apparent : array-like, shape (n_q,)
    transmission : float
        Sample transmission (0 < T < 1); μ = -ln(T).
    n_basis : int
    n_orders : int
    length_scale : float or None
    enforce_nonneg : bool
    n_phi : int

    Returns
    -------
    dict with keys 'I_true', 'I_fit', 'alpha1', 'I0', 'result', 'model'.
    """
    q = np.asarray(q, dtype=float)
    I_apparent = np.asarray(I_apparent, dtype=float)
    model = AlgebraicConvolutionModel(
        q, n_basis=n_basis, n_orders=n_orders,
        length_scale=length_scale, n_phi=n_phi,
    )
    out = model.invert(I_apparent, transmission, enforce_nonneg=enforce_nonneg)
    out['model'] = model
    return out
