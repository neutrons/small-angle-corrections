import numpy as np
import pytest


@pytest.fixture
def q_grid():
    return np.geomspace(1e-4, 1e-2, 60)


@pytest.fixture
def simple_profile(q_grid):
    """Simple broad Gaussian-like profile for testing."""
    q0 = np.median(q_grid)
    return np.exp(-((q_grid - q0) / (3.0 * q0))**2)


@pytest.fixture
def model(q_grid):
    from small_angle_corrections import AlgebraicConvolutionModel
    return AlgebraicConvolutionModel(q_grid, n_basis=4, n_orders=4, n_phi=16)
