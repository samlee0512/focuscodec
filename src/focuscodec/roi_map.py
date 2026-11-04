"""Turn person masks into per-frame delta-QP maps in Kvazaar's --roi format.

Kvazaar binary ROI format (one block per frame, repeated):
    int32 width, int32 height, then width*height int8 delta-QP values in raster order.
Negative delta-QP = finer quantization = higher quality.
Kvazaar consumes one map per frame in *coding* order, so encode with a low-delay GOP
(see video_io.kvazaar_encode) to keep map i on display frame i.
"""
from __future__ import annotations

import math
import struct
from pathlib import Path

import numpy as np

CTU = 64  # HEVC coding tree unit size used by Kvazaar


def grid_shape(width: int, height: int, block: int = CTU) -> tuple[int, int]:
    """(rows, cols) of the block grid covering a width x height frame."""
    return math.ceil(height / block), math.ceil(width / block)


def mask_to_grid(mask: np.ndarray, block: int = CTU) -> np.ndarray:
    """Fraction of ROI pixels in each block. mask: (H, W) bool or [0, 1] float."""
    h, w = mask.shape
    rows, cols = grid_shape(w, h, block)
    padded = np.zeros((rows * block, cols * block), dtype=np.float32)
    padded[:h, :w] = mask
    # count only pixels inside the frame when averaging edge blocks
    valid = np.zeros_like(padded)
    valid[:h, :w] = 1.0
    sums = padded.reshape(rows, block, cols, block).sum(axis=(1, 3))
    counts = valid.reshape(rows, block, cols, block).sum(axis=(1, 3))
    return sums / counts


def dilate(grid: np.ndarray, steps: int = 1) -> np.ndarray:
    """Grow a boolean block grid by `steps` blocks (3x3 neighbourhood)."""
    out = grid.astype(bool)
    for _ in range(steps):
        p = np.pad(out, 1)
        out = np.zeros_like(out)
        for dy in range(3):
            for dx in range(3):
                out |= p[dy:dy + grid.shape[0], dx:dx + grid.shape[1]]
    return out


class TemporalSmoother:
    """Exponential moving average + hysteresis, so blocks don't flicker in/out of the ROI."""

    def __init__(self, alpha: float = 0.6, on: float = 0.5, off: float = 0.3):
        self.alpha, self.on, self.off = alpha, on, off
        self.avg: np.ndarray | None = None
        self.state: np.ndarray | None = None

    def __call__(self, coverage: np.ndarray) -> np.ndarray:
        if self.avg is None:
            self.avg = coverage.astype(np.float32)
            self.state = self.avg >= self.on
        else:
            self.avg = self.alpha * coverage + (1 - self.alpha) * self.avg
            self.state = np.where(self.state, self.avg >= self.off, self.avg >= self.on)
        return self.state.copy()


def delta_qp(roi: np.ndarray, d: int) -> np.ndarray:
    """-d inside the ROI, +d outside."""
    return np.where(roi, -d, d).astype(np.int8)


def write_roi_file(path: str | Path, frames: list[np.ndarray]) -> None:
    with open(path, "wb") as f:
        for m in frames:
            m = np.ascontiguousarray(m, dtype=np.int8)
            rows, cols = m.shape
            f.write(struct.pack("<ii", cols, rows))
            f.write(m.tobytes())


def read_roi_file(path: str | Path) -> list[np.ndarray]:
    data = Path(path).read_bytes()
    frames, pos = [], 0
    while pos < len(data):
        cols, rows = struct.unpack_from("<ii", data, pos)
        pos += 8
        frames.append(np.frombuffer(data, np.int8, rows * cols, pos).reshape(rows, cols).copy())
        pos += rows * cols
    return frames
