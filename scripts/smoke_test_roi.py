"""W1 smoke test: does Kvazaar apply a *different* ROI map to each frame, with the expected sign?

Synthetic video of independent textured frames (so inter prediction can't carry quality over).
ROI maps alternate per frame: even frames favour the LEFT half (-D left, +D right),
odd frames favour the RIGHT half. If per-frame ROI works, (PSNR_left - PSNR_right)
must be positive on even frames and negative on odd frames. A no-ROI encode should show ~0 gap.

Usage: python scripts/smoke_test_roi.py   (needs kvazaar + ffmpeg on PATH)
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np

from focuscodec.metrics import psnr
from focuscodec.roi_map import grid_shape, write_roi_file
from focuscodec.video_io import decode_to_yuv, kvazaar_encode, read_luma, write_yuv

W, H, N, QP, D = 640, 384, 16, 32, 10


def textured_frames(rng: np.random.Generator) -> np.ndarray:
    """Smoothed noise: real texture for the encoder to spend bits on."""
    noise = rng.normal(0, 1, (N, H // 4, W // 4))
    up = np.kron(noise, np.ones((4, 4)))           # blocky upsample
    k = np.ones(5) / 5                              # light blur along both axes
    up = np.apply_along_axis(lambda r: np.convolve(r, k, "same"), 2, up)
    up = np.apply_along_axis(lambda c: np.convolve(c, k, "same"), 1, up)
    return np.clip(128 + 40 * up, 0, 255).astype(np.uint8)


def side_gaps(ref: np.ndarray, dec: np.ndarray) -> list[float]:
    left = np.zeros((H, W), bool)
    left[:, : W // 2] = True
    return [psnr(r, d, left) - psnr(r, d, ~left) for r, d in zip(ref, dec)]


def main() -> int:
    rng = np.random.default_rng(0)
    ref = textured_frames(rng)
    rows, cols = grid_shape(W, H)
    left_cols = np.arange(cols) < cols // 2
    maps = []
    for i in range(N):
        favour_left = i % 2 == 0
        roi = np.broadcast_to(left_cols if favour_left else ~left_cols, (rows, cols))
        maps.append(np.where(roi, -D, D).astype(np.int8))

    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        src, roi_file = t / "src.yuv", t / "roi.bin"
        write_yuv(src, ref)
        write_roi_file(roi_file, maps)

        results = {}
        for name, roi in [("no_roi", None), ("roi", roi_file)]:
            hevc, dec = t / f"{name}.hevc", t / f"{name}.yuv"
            size = kvazaar_encode(src, hevc, W, H, QP, roi=roi, frames=N)
            decode_to_yuv(hevc, dec)
            results[name] = (size, side_gaps(ref, read_luma(dec, W, H)))

    print(f"{'frame':>5} {'expected':>9} {'no_roi gap':>11} {'roi gap':>9}")
    ok = True
    for i in range(N):
        exp = "+" if i % 2 == 0 else "-"
        g0, g1 = results["no_roi"][1][i], results["roi"][1][i]
        good = (g1 > 1.0) if exp == "+" else (g1 < -1.0)
        ok &= good
        print(f"{i:>5} {exp:>9} {g0:>11.2f} {g1:>9.2f} {'' if good else '  <-- FAIL'}")
    print(f"bytes: no_roi={results['no_roi'][0]}  roi={results['roi'][0]}")
    print("PASS: per-frame ROI and sign convention confirmed" if ok else
          "FAIL: see plan's fallback (FFmpeg addroi + x265, then background blur)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
