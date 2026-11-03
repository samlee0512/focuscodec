import numpy as np
import pytest

from focuscodec.roi_map import (TemporalSmoother, delta_qp, dilate, grid_shape, mask_to_grid,
                                read_roi_file, write_roi_file)


def test_grid_shape_720p():
    assert grid_shape(1280, 720) == (12, 20)


def test_mask_to_grid_coverage():
    mask = np.zeros((128, 128), bool)
    mask[:64, :32] = True  # half of the top-left block
    g = mask_to_grid(mask)
    assert g.shape == (2, 2)
    assert g[0, 0] == pytest.approx(0.5)
    assert g[1, 1] == 0


def test_mask_to_grid_partial_edge_block():
    mask = np.ones((70, 70), bool)  # edge blocks are only partly inside the frame
    assert np.allclose(mask_to_grid(mask), 1.0)


def test_dilate_one_step():
    g = np.zeros((5, 5), bool)
    g[2, 2] = True
    assert dilate(g).sum() == 9


def test_smoother_hysteresis():
    s = TemporalSmoother(alpha=1.0, on=0.5, off=0.3)
    assert s(np.array([0.6]))[0]
    assert s(np.array([0.4]))[0]       # stays on between thresholds
    assert not s(np.array([0.2]))[0]


def test_roi_file_round_trip(tmp_path):
    frames = [delta_qp(np.eye(3, 4, dtype=bool), 6), delta_qp(np.zeros((3, 4), bool), 2)]
    p = tmp_path / "roi.bin"
    write_roi_file(p, frames)
    back = read_roi_file(p)
    assert len(back) == 2 and all(np.array_equal(a, b) for a, b in zip(frames, back))
    assert p.stat().st_size == 2 * (8 + 12)
