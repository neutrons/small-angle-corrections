"""Demonstrate multiple-scattering correction on the synthetic fuzzy-ball dataset."""

import numpy as np
from pathlib import Path
from usans_correct import correct
from examples.generate_synthetic import make_synthetic


def main():
    q, I_true, I_apparent, I_noisy = make_synthetic()
    result = correct(q, I_noisy, transmission=0.5, n_basis=8, n_orders=8)

    I_corr = result['I_true']
    residual = np.sqrt(np.mean((I_corr - I_true)**2)) / np.mean(I_true)
    print(f"RMS relative residual (corrected vs true): {residual:.3%}")

    data_dir = Path(__file__).parent.parent / 'data' / 'synthetic'
    data_dir.mkdir(parents=True, exist_ok=True)
    np.savetxt(data_dir / 'fuzzy_ball_T0p5_corrected.txt',
               np.column_stack([q, I_corr]),
               header='Q(Ang^-1)  I_corrected')


if __name__ == '__main__':
    main()
