"""Diagnostics: assess whether correction is needed without applying it."""

from math import exp, log

import numpy as np

from .profiles import Profile


def assess(profile: Profile, transmission: float) -> dict:
    """
    Return a dict of diagnostic quantities for the given profile and transmission.
    Does not run any correction.
    """
    mu = -log(float(transmission))
    P1 = exp(-mu) * mu

    advice_map = [
        (0.90, "Correction probably not needed (T > 0.90)."),
        (0.70, "Consider running correction (0.70 ≤ T ≤ 0.90); run diagnose first."),
        (0.40, "Correction recommended (0.40 ≤ T < 0.70)."),
        (0.10, "Correction important (0.10 ≤ T < 0.40); review results carefully."),
        (0.00, "Strong multiple scattering (T < 0.10); consult instrument scientist."),
    ]
    advice = next(msg for threshold, msg in advice_map if transmission >= threshold)

    return {
        "n_points":     profile.n_points,
        "q_min":        float(profile.q.min()),
        "q_max":        float(profile.q.max()),
        "I_min":        float(profile.I.min()),
        "I_max":        float(profile.I.max()),
        "transmission": float(transmission),
        "mu":           float(mu),
        "P1":           float(P1),
        "advice":       advice,
    }
