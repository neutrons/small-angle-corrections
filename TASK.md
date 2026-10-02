# Task: Implement Multiple-Scattering Correction Package v0.1 (small-angle-corrections)

## Your job
Implement the complete Python package described in Project_Specification.docx.
The mathematical basis is in tung_et_al_paper.pdf (read the appendix carefully).
The software design is in software_design_paper.pdf.

## Do this in order, without stopping:

1. Create the full repository structure from Section 5 of the spec.
2. Implement all classes in Sections 6.1-6.7 with full method bodies.
3. For AlgebraicConvolutionModel, use the Gram-Schmidt numerical basis
   as the v0.1 fallback (spec Section 6.4 permits this). The basis must
   be swappable later without changing outer classes.
4. Implement the CLI (Section 7).
5. Generate synthetic example data (fuzzy-ball profile, T=0.5).
6. Implement all examples (Section 8).
7. Implement all tests (Section 9). Run pytest and fix all failures.
8. Write README following Section 14 outline.
9. Write CITATION.cff and LICENSE (MIT).
10. Run the Definition of Done commands (Section 17) and confirm they pass.

## Math to implement (from Tung et al. paper):
- Poisson weights: Pn = exp(-mu) * mu^n / n!, mu = -ln(T)
- Basis: orthonormal on 2*pi*Q*dQ measure via Gram-Schmidt on Q grid
- Structure tensor C: C[l,j,k] = inner product of u_l with (u_j * u_k)
  where convolution is the 2D isotropic convolution eq (4) of the paper
- Recursive convolution: alpha_n = sum_{j,k} C[l,j,k] * alpha1_j * alpha_{n-1}_k
- Forward model: I_app = I0 * sum_n Pn * J^(*n)(Q)
- Inversion: scipy.optimize.least_squares on alpha_1 coefficients

## Key constraints:
- length_scale default: 1.0 / np.median(q)
- enforce_nonnegative: use bounds in least_squares
- All outputs non-destructive
- pytest must pass before you finish

## Do not ask clarifying questions. Make reasonable decisions and document them.
## Token efficiency rules
- Do not re-read files you already wrote unless fixing a specific failure
- Do not explain what you are about to do; just do it
- Do not summarize what you just did; just continue
- When pytest fails, fix only the failing test, do not rewrite passing code
- Do not add comments beyond docstrings