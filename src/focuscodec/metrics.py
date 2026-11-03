"""Quality metrics on 8-bit luma planes, optionally restricted to a region."""
from __future__ import annotations

import math

import numpy as np


def mse(ref: np.ndarray, dist: np.ndarray, mask: np.ndarray | None = None) -> float:
    diff = ref.astype(np.float64) - dist.astype(np.float64)
    sq = diff * diff
    if mask is None:
        return float(sq.mean())
    mask = mask.astype(bool)
    if not mask.any():
        return float("nan")
    return float(sq[mask].mean())


def psnr(ref: np.ndarray, dist: np.ndarray, mask: np.ndarray | None = None, peak: float = 255.0) -> float:
    """PSNR in dB. Identical inputs give inf; an empty mask gives nan."""
    e = mse(ref, dist, mask)
    if math.isnan(e):
        return e
    return math.inf if e == 0 else 10 * math.log10(peak * peak / e)
