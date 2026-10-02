import numpy as np
import pytest
from small_angle_corrections.corrections.multiple_scattering.basis import GramSchmidtBasis, _trapz_weights


def test_orthonormality(q_grid):
    basis = GramSchmidtBasis(q_grid * (1.0 / np.median(q_grid)), n_basis=4)
    q_int = q_grid * (1.0 / np.median(q_grid))
    basis = GramSchmidtBasis(q_int, n_basis=4)
    w = _trapz_weights(q_int)
    U = basis.evaluate(q_int)
    gram = U @ (U * w[None, :]).T
    np.testing.assert_allclose(gram, np.eye(4), atol=1e-6)


def test_coefficients_roundtrip(q_grid):
    q_int = q_grid * (1.0 / np.median(q_grid))
    basis = GramSchmidtBasis(q_int, n_basis=6)
    f = np.ones_like(q_grid)
    alpha = basis.coefficients(f, q_int)
    f_reconstructed = basis.evaluate(q_int).T @ alpha
    np.testing.assert_allclose(f_reconstructed, f, atol=1e-4)


def test_evaluate_outside_range(q_grid):
    q_int = q_grid * (1.0 / np.median(q_grid))
    basis = GramSchmidtBasis(q_int, n_basis=3)
    q_beyond = np.array([0.0, q_int[-1] * 2])
    vals = basis.evaluate(q_beyond)
    assert vals.shape == (3, 2)
    np.testing.assert_array_equal(vals[:, 1], 0.0)
