"""Bjontegaard delta rate (BD-rate) with piecewise-cubic (PCHIP) interpolation.

BD-rate = average % bitrate change of the test codec vs the anchor at equal quality,
over the overlapping quality range. Negative = test needs fewer bits.
"""
from __future__ import annotations

import numpy as np
from scipy.interpolate import PchipInterpolator


def _log_rate_integral(rate, quality, lo, hi):
    q = np.asarray(quality, dtype=float)
    r = np.log(np.asarray(rate, dtype=float))
    order = np.argsort(q)
    f = PchipInterpolator(q[order], r[order])
    return f.integrate(lo, hi)


def bd_rate(anchor_rate, anchor_quality, test_rate, test_quality) -> float:
    lo = max(min(anchor_quality), min(test_quality))
    hi = min(max(anchor_quality), max(test_quality))
    if hi <= lo:
        raise ValueError("quality ranges do not overlap")
    a = _log_rate_integral(anchor_rate, anchor_quality, lo, hi)
    t = _log_rate_integral(test_rate, test_quality, lo, hi)
    return float((np.exp((t - a) / (hi - lo)) - 1) * 100)
