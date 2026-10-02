"""2D isotropic convolution and structure tensor precomputation."""

import numpy as np
from .basis import AbstractBasis, _trapz_weights


def _build_angular_integral(U_j: np.ndarray, q: np.ndarray, n_phi: int = 32) -> np.ndarray:
    """
    For a single basis function u_j (values U_j on q), compute the angular
    integral A[i, m] = 2 * ∫₀^π u_j(Q_cross(q[i], q[m], φ)) dφ
    using Gauss-Legendre quadrature on [0, π].

    Returns shape (n_q, n_q).
    """
    phi_pts, phi_w = np.polynomial.legendre.leggauss(n_phi)
    phi = np.pi * (phi_pts + 1.0) / 2.0
    phi_w = phi_w * np.pi / 2.0

    qi = q[:, None, None]
    qm = q[None, :, None]
    ph = phi[None, None, :]

    arg = qi**2 + qm**2 - 2.0 * qi * qm * np.cos(ph)
    Q_cross = np.sqrt(np.maximum(arg, 0.0))

    u_vals = np.interp(Q_cross.ravel(), q, U_j,
                       left=U_j[0], right=0.0).reshape(Q_cross.shape)

    return 2.0 * np.einsum('imp,p->im', u_vals, phi_w)


def build_structure_tensor(basis: AbstractBasis, q: np.ndarray,
                           n_phi: int = 32) -> np.ndarray:
    """
    Precompute C[l, j, k] = <u_l, u_j ⊗ u_k> for all (l, j, k).

    Returns ndarray of shape (n_basis, n_basis, n_basis).
    """
    q = np.asarray(q, dtype=float)
    n_b = basis.n_basis
    n_q = len(q)

    dq = np.empty(n_q)
    dq[0] = q[1] - q[0]
    dq[-1] = q[-1] - q[-2]
    dq[1:-1] = (q[2:] - q[:-2]) / 2.0

    w_ip = _trapz_weights(q)

    U = basis.evaluate(q)

    C = np.zeros((n_b, n_b, n_b))

    for j in range(n_b):
        ang_j = _build_angular_integral(U[j], q, n_phi)
        for k in range(j, n_b):
            wm = U[k] * q * dq
            conv_jk = ang_j @ wm
            C[:, j, k] = U @ (conv_jk * w_ip)
            if k != j:
                ang_k = _build_angular_integral(U[k], q, n_phi)
                wm_j = U[j] * q * dq
                conv_kj = ang_k @ wm_j
                C_kj = U @ (conv_kj * w_ip)
                C[:, j, k] = 0.5 * (C[:, j, k] + C_kj)
                C[:, k, j] = C[:, j, k]

    return C
