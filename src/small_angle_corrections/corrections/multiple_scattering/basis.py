"""Orthonormal basis construction via Gram-Schmidt on a Q grid."""

from abc import ABC, abstractmethod
import numpy as np


def _trapz_weights(q):
    """Trapezoidal weights for the 2π Q dQ inner product."""
    q = np.asarray(q, dtype=float)
    dq = np.empty_like(q)
    dq[0] = q[1] - q[0]
    dq[-1] = q[-1] - q[-2]
    dq[1:-1] = (q[2:] - q[:-2]) / 2.0
    return 2.0 * np.pi * q * dq


class AbstractBasis(ABC):
    """Abstract base for an orthonormal basis on a Q grid."""

    @property
    @abstractmethod
    def n_basis(self) -> int:
        ...

    @abstractmethod
    def evaluate(self, q_eval: np.ndarray) -> np.ndarray:
        """Return basis function values at q_eval, shape (n_basis, len(q_eval))."""
        ...

    @abstractmethod
    def coefficients(self, f: np.ndarray, q: np.ndarray) -> np.ndarray:
        """Expand f (defined on q) in the basis; return shape (n_basis,)."""
        ...


class GramSchmidtBasis(AbstractBasis):
    """
    Orthonormal basis constructed by Gram-Schmidt on monomials (Q/q_ref)^k
    with the inner product <f,g> = ∫ f g 2π Q dQ (trapezoid rule on q_grid).
    """

    def __init__(self, q_grid: np.ndarray, n_basis: int):
        q_grid = np.asarray(q_grid, dtype=float)
        self._q = q_grid
        self._n = n_basis
        self._q_ref = float(np.median(q_grid))
        self._w = _trapz_weights(q_grid)
        self._funcs = self._build()

    def _build(self) -> np.ndarray:
        q, w, q_ref, n = self._q, self._w, self._q_ref, self._n
        funcs: list[np.ndarray] = []
        power = 0
        while len(funcs) < n:
            v = (q / q_ref) ** power
            u = v.copy()
            for b in funcs:
                proj = float(np.dot(u * w, b))
                u = u - proj * b
            norm = float(np.sqrt(np.dot(u * u, w)))
            if norm > 1e-12:
                funcs.append(u / norm)
            power += 1
            if power > n + 20:
                break
        return np.array(funcs)

    @property
    def n_basis(self) -> int:
        return self._n

    def evaluate(self, q_eval: np.ndarray) -> np.ndarray:
        q_eval = np.asarray(q_eval, dtype=float)
        out = np.empty((self._n, q_eval.size))
        for l in range(self._n):
            out[l] = np.interp(q_eval, self._q, self._funcs[l],
                               left=self._funcs[l, 0], right=0.0)
        return out

    def coefficients(self, f: np.ndarray, q: np.ndarray) -> np.ndarray:
        f = np.asarray(f, dtype=float)
        U = self.evaluate(q)
        w = _trapz_weights(np.asarray(q, dtype=float))
        return U @ (f * w)
