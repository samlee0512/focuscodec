import pytest

from focuscodec.bdrate import bd_rate


def test_bd_rate_identical_is_zero():
    r, q = [100, 200, 400, 800], [30, 33, 36, 39]
    assert bd_rate(r, q, r, q) == pytest.approx(0, abs=1e-9)


def test_bd_rate_half_bits_is_minus_50():
    r, q = [100, 200, 400, 800], [30, 33, 36, 39]
    assert bd_rate(r, q, [x / 2 for x in r], q) == pytest.approx(-50, abs=1e-6)
