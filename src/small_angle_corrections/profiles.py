"""Profile data container."""

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class Profile:
    """A reduced small-angle scattering (SANS/SAXS/USANS) intensity profile."""

    q: np.ndarray
    I: np.ndarray
    dI: Optional[np.ndarray] = None

    @property
    def n_points(self) -> int:
        return len(self.q)

    @property
    def q_range(self):
        return (float(self.q.min()), float(self.q.max()))
