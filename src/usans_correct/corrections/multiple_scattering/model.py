"""AlgebraicConvolutionModel: forward model and inversion."""

import numpy as np
from math import factorial, exp
from scipy.optimize import least_squares

from .basis import AbstractBasis, GramSchmidtBasis, _trapz_weights
from .convolution import build_structure_tensor


class AlgebraicConvolutionModel:
    """
    Multiple-scattering correction model based on algebraic convolution.

    Parameters
    ----------
    q : array-like
        Momentum-transfer grid (Å⁻¹ or any consistent unit).
    n_basis : int
        Number of orthonormal basis functions (default 8).
    n_orders : int
        Maximum number of scattering orders to include (default 10).
    length_scale : float or None
        Dimensionless scaling: q_internal = q * length_scale.
        Default: 1 / np.median(q).
    basis_class : type
        Class derived from AbstractBasis (default GramSchmidtBasis).
    n_phi : int
        Gauss-Legendre quadrature points for the angular integral (default 32).
    """

    def __init__(self, q, n_basis=8, n_orders=10, length_scale=None,
                 basis_class=GramSchmidtBasis, n_phi=32):
        q = np.asarray(q, dtype=float)
        if length_scale is None:
            length_scale = 1.0 / float(np.median(q))
        self._q = q
        self._length_scale = float(length_scale)
        self._n_orders = int(n_orders)
        self._n_basis = int(n_basis)

        q_int = q * self._length_scale
        self._basis: AbstractBasis = basis_class(q_int, n_basis)
        self._C = build_structure_tensor(self._basis, q_int, n_phi=n_phi)
        self._U = self._basis.evaluate(q_int)
        self._w_ip = _trapz_weights(q_int)

    @property
    def q(self) -> np.ndarray:
        return self._q.copy()

    @property
    def n_basis(self) -> int:
        return self._n_basis

    @property
    def structure_tensor(self) -> np.ndarray:
        return self._C.copy()

    def forward(self, alpha1: np.ndarray, transmission: float,
                I0: float = 1.0) -> np.ndarray:
        """
        Compute the apparent intensity for a given true-scattering profile.

        Parameters
        ----------
        alpha1 : array, shape (n_basis,)
            Expansion coefficients of the true single-scattering profile.
        transmission : float
            Sample transmission (0 < T < 1).
        I0 : float
            Intensity scale factor.

        Returns
        -------
        I_app : ndarray, shape (n_q,)
        """
        alpha1 = np.asarray(alpha1, dtype=float)
        mu = -np.log(float(transmission))
        P = [exp(-mu) * mu**n / factorial(n) for n in range(1, self._n_orders + 1)]

        alpha_n = alpha1.copy()
        I_app = np.zeros(len(self._q))

        for n in range(1, self._n_orders + 1):
            J_n = self._U.T @ alpha_n
            I_app += P[n - 1] * J_n
            if n < self._n_orders:
                alpha_n = np.einsum('ljk,j,k->l', self._C, alpha1, alpha_n)

        return float(I0) * I_app

    def invert(self, I_apparent: np.ndarray, transmission: float,
               enforce_nonneg: bool = True) -> dict:
        """
        Recover the true single-scattering profile from apparent intensity.

        Parameters
        ----------
        I_apparent : array, shape (n_q,)
        transmission : float
        enforce_nonneg : bool
            If True, constrain alpha1 >= 0.

        Returns
        -------
        dict with keys:
            'alpha1'    : shape (n_basis,), expansion coefficients
            'I0'        : float scale factor
            'I_true'    : shape (n_q,), corrected intensity on self.q
            'I_fit'     : shape (n_q,), forward-model fit to I_apparent
            'result'    : scipy OptimizeResult
        """
        I_apparent = np.asarray(I_apparent, dtype=float)
        n_b = self._n_basis
        mu = -np.log(float(transmission))
        P1 = exp(-mu) * mu   # dominant Poisson weight

        # Better starting point: first-order approximation I_true ≈ I_apparent / P1.
        # This is far closer to the solution than projecting I_apparent directly.
        I_true_init = I_apparent / max(P1, 1e-9)
        alpha1_init = self._basis.coefficients(I_true_init, self._q * self._length_scale)
        if enforce_nonneg:
            alpha1_init = np.clip(alpha1_init, 0.0, None)

        x0 = np.concatenate([alpha1_init, [0.0]])   # log_I0 = 0 → I0 = 1

        if enforce_nonneg:
            lb = np.concatenate([np.zeros(n_b), [-np.inf]])
            ub = np.full(n_b + 1, np.inf)
        else:
            lb = np.full(n_b + 1, -np.inf)
            ub = np.full(n_b + 1, np.inf)

        # Log-space residuals give equal relative weight to all Q points,
        # preventing large-I points from dominating at the cost of small-I accuracy.
        eps = np.max(I_apparent) * 1e-6
        log_data = np.log(np.maximum(I_apparent, eps))

        def residuals(x):
            alpha1 = x[:n_b]
            I0 = np.exp(x[n_b])
            I_model = self.forward(alpha1, transmission, I0)
            return np.log(np.maximum(I_model, eps)) - log_data

        res = least_squares(residuals, x0, bounds=(lb, ub), method='trf')

        alpha1 = res.x[:n_b]
        I0 = float(np.exp(res.x[n_b]))
        I_true = I0 * (self._U.T @ alpha1)
        I_fit = self.forward(alpha1, transmission, I0)

        return {
            'alpha1': alpha1,
            'I0': I0,
            'I_true': I_true,
            'I_fit': I_fit,
            'result': res,
        }
