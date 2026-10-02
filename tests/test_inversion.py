import numpy as np
from small_angle_corrections import correct


def test_correct_returns_dict(q_grid, simple_profile):
    out = correct(q_grid, simple_profile, transmission=0.7,
                  n_basis=4, n_orders=4, n_phi=16)
    assert 'I_true' in out
    assert 'I_fit' in out
    assert 'alpha1' in out
    assert 'model' in out


def test_correct_shape(q_grid, simple_profile):
    out = correct(q_grid, simple_profile, transmission=0.7,
                  n_basis=4, n_orders=4, n_phi=16)
    assert out['I_true'].shape == q_grid.shape
    assert out['I_fit'].shape == q_grid.shape


def test_correct_fit_quality(q_grid, simple_profile):
    """I_fit should closely match I_apparent."""
    out = correct(q_grid, simple_profile, transmission=0.7,
                  n_basis=6, n_orders=6, n_phi=16)
    rel_err = np.sqrt(np.mean((out['I_fit'] - simple_profile)**2)) / np.mean(np.abs(simple_profile))
    assert rel_err < 0.1
