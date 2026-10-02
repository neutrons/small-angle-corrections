import numpy as np
from small_angle_corrections.corrections.multiple_scattering.basis import GramSchmidtBasis
from small_angle_corrections.corrections.multiple_scattering.convolution import build_structure_tensor


def test_structure_tensor_shape(q_grid):
    q_int = q_grid * (1.0 / np.median(q_grid))
    basis = GramSchmidtBasis(q_int, n_basis=3)
    C = build_structure_tensor(basis, q_int, n_phi=8)
    assert C.shape == (3, 3, 3)


def test_structure_tensor_symmetry(q_grid):
    """C[l, j, k] should equal C[l, k, j] since convolution is commutative."""
    q_int = q_grid * (1.0 / np.median(q_grid))
    basis = GramSchmidtBasis(q_int, n_basis=3)
    C = build_structure_tensor(basis, q_int, n_phi=8)
    np.testing.assert_allclose(C, C.transpose(0, 2, 1), atol=1e-6)


def test_structure_tensor_finite(q_grid):
    q_int = q_grid * (1.0 / np.median(q_grid))
    basis = GramSchmidtBasis(q_int, n_basis=3)
    C = build_structure_tensor(basis, q_int, n_phi=8)
    assert np.all(np.isfinite(C))
