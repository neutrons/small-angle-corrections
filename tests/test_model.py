import numpy as np
import pytest
from small_angle_corrections import AlgebraicConvolutionModel


def test_forward_shape(model, q_grid, simple_profile):
    alpha1 = model._basis.coefficients(simple_profile,
                                       q_grid * model._length_scale)
    I_app = model.forward(alpha1, transmission=0.5)
    assert I_app.shape == q_grid.shape


def test_forward_positive(model, q_grid, simple_profile):
    alpha1 = model._basis.coefficients(simple_profile,
                                       q_grid * model._length_scale)
    I_app = model.forward(alpha1, transmission=0.5, I0=1.0)
    assert np.all(I_app >= 0)


def test_forward_low_transmission_larger(model, q_grid, simple_profile):
    """Lower transmission (more scattering) should broaden the apparent profile."""
    alpha1 = model._basis.coefficients(simple_profile,
                                       q_grid * model._length_scale)
    I_high_T = model.forward(alpha1, transmission=0.9, I0=1.0)
    I_low_T = model.forward(alpha1, transmission=0.3, I0=1.0)
    assert np.sum(I_low_T) >= np.sum(I_high_T) * 0.5


def test_invert_shape(model, q_grid, simple_profile):
    alpha1_true = model._basis.coefficients(simple_profile,
                                            q_grid * model._length_scale)
    I_app = model.forward(alpha1_true, transmission=0.5)
    out = model.invert(I_app, transmission=0.5)
    assert out['I_true'].shape == q_grid.shape
    assert out['alpha1'].shape == (model.n_basis,)


def test_invert_recovers_profile(model, q_grid, simple_profile):
    """Round-trip: forward then invert should approximately recover the input."""
    alpha1_true = model._basis.coefficients(simple_profile,
                                            q_grid * model._length_scale)
    I_app = model.forward(alpha1_true, transmission=0.5, I0=1.0)
    out = model.invert(I_app, transmission=0.5)
    err_corr = np.mean((out['I_true'] - simple_profile)**2)
    err_app = np.mean((I_app - simple_profile)**2)
    assert err_corr <= err_app * 2.0


def test_invert_nonneg(model, q_grid, simple_profile):
    alpha1_true = model._basis.coefficients(
        np.abs(simple_profile), q_grid * model._length_scale)
    I_app = model.forward(alpha1_true, transmission=0.5)
    out = model.invert(I_app, transmission=0.5, enforce_nonneg=True)
    assert np.all(out['alpha1'] >= -1e-10)
