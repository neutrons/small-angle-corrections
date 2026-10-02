"""CSV read / write helpers."""

from pathlib import Path

import click
import numpy as np

from .profiles import Profile


def load_profile(path, q_col: str = "Q", i_col: str = "I",
                 di_col: str = "dI") -> Profile:
    """Load a comma-separated CSV with a header row into a Profile."""
    raw = np.genfromtxt(path, delimiter=",", names=True, dtype=float)
    lo = [n.lower() for n in raw.dtype.names]

    def _col(key, required=True):
        k = key.lower()
        if k in lo:
            return raw[raw.dtype.names[lo.index(k)]]
        if required:
            raise click.BadParameter(
                f"Column '{key}' not found in {path}. "
                f"Available: {raw.dtype.names}"
            )
        return None

    q  = _col(q_col)
    I  = _col(i_col)
    dI = _col(di_col, required=False)
    return Profile(q=q, I=I, dI=dI)


def save_csv(path, col_names: list[str], arrays: list[np.ndarray]) -> None:
    """Save columns to a comma-separated CSV with a header row."""
    np.savetxt(path, np.column_stack(arrays),
               delimiter=",", header=",".join(col_names), comments="")
