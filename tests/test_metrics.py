import math

import numpy as np
import pytest

from focuscodec.metrics import psnr


def test_psnr_identical_is_inf():
    x = np.random.default_rng(0).integers(0, 256, (16, 16), dtype=np.uint8)
    assert psnr(x, x) == math.inf


def test_psnr_known_value_and_mask():
    a = np.zeros((4, 4), np.uint8)
    b = np.ones((4, 4), np.uint8)
    assert psnr(a, b) == pytest.approx(10 * math.log10(255 ** 2))  # MSE = 1 -> 48.13 dB
    mask = np.zeros((4, 4), bool)
    mask[0, 0] = True
    b2 = a.copy()
    b2[0, 0] = 1
    assert psnr(a, b2, mask) == pytest.approx(48.1308, abs=1e-3)
