# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is `small-angle-corrections` (import package `small_angle_corrections`), a Python package of post-processing corrections for small-angle scattering data (neutron and X-ray: SANS, SAXS, USANS). The first supported use case is multiple-scattering correction for USANS (Ultra-Small Angle Neutron Scattering) data, based on the algebraic convolution method from Tung et al. The scientific specification lives in `Project_Multiple_Scattering_Correction.pdf` (software design) and `USANS_Multiple_Scattering_Correction_Reduction_Software.pdf` (mathematical basis — read the appendix carefully). `TASK.md` lists the full implementation plan.

The project uses conda (managed via the `ms-python.python:conda` extension).

## Commands

Once the package is created, standard commands will be:

```bash
# Install in editable mode
pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test file
pytest tests/test_<module>.py

# Run a single test by name
pytest tests/test_<module>.py::test_function_name -v

# Run the CLI
small-angle-corrections --help
small-angle-corrections correct-ms --help
```

## Architecture

The package is structured around an algebraic convolution model. Key components (from the spec, Sections 6.1–6.7):

- **Basis classes** — orthonormal function basis on a Q grid, constructed via Gram-Schmidt on the 2π·Q·dQ measure. The basis is an internal detail, swappable without changing the outer API.
- **AlgebraicConvolutionModel** — core class that precomputes the structure tensor `C[l,j,k]` (inner product of `u_l` with the isotropic 2D convolution of `u_j * u_k`, equation (4) of the paper), then uses it for recursive convolution of scattering orders.
- **Forward model** — computes the apparent intensity: `I_app = I0 * Σ_n P_n * J^(*n)(Q)` where Poisson weights are `P_n = exp(-μ) * μ^n / n!` with `μ = -ln(T)` (T = sample transmission).
- **Inversion** — `scipy.optimize.least_squares` over the α₁ basis coefficients; `enforce_nonneg=True` uses `bounds=(0, ∞)`.
- **CLI** (Section 7) — entry point `small-angle-corrections` with subcommands `correct-ms`, `diagnose`, and `desmear` (placeholder).
- **Examples** (Section 8) — synthetic data generated with a fuzzy-ball profile at T=0.5.

## Key Implementation Constraints

- `length_scale` parameter default: `1.0 / np.median(q)`
- All public methods must be non-destructive (never mutate inputs)
- No comments beyond docstrings
- `pytest` must pass before any commit
- Definition of Done commands are in Section 17 of the spec PDF
