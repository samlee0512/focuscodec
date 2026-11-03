"""Raw YUV 4:2:0 (8-bit) file I/O and FFmpeg/Kvazaar wrappers."""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np


def frame_size(width: int, height: int) -> int:
    return width * height * 3 // 2


def read_luma(path: str | Path, width: int, height: int) -> np.ndarray:
    """All Y planes of a yuv420p file as (N, H, W) uint8."""
    raw = np.fromfile(path, dtype=np.uint8)
    n = raw.size // frame_size(width, height)
    frames = raw[: n * frame_size(width, height)].reshape(n, -1)
    return frames[:, : width * height].reshape(n, height, width)


def write_yuv(path: str | Path, luma: np.ndarray) -> None:
    """Write (N, H, W) luma frames as yuv420p with neutral (128) chroma."""
    n, h, w = luma.shape
    chroma = np.full((n, h * w // 2), 128, dtype=np.uint8)
    np.concatenate([luma.reshape(n, -1).astype(np.uint8), chroma], axis=1).tofile(path)


def kvazaar_encode(src: Path, out: Path, width: int, height: int, qp: int, fps: int = 30,
                   roi: Path | None = None, preset: str = "medium", frames: int | None = None) -> int:
    """Encode raw yuv420p with constant QP; returns the bitstream size in bytes."""
    cmd = ["kvazaar", "-i", str(src), "--input-res", f"{width}x{height}", "--input-fps", str(fps),
           "--qp", str(qp), "--preset", preset, "-o", str(out)]
    if frames:
        cmd += ["-n", str(frames)]
    if roi:
        cmd += ["--roi", str(roi)]
    subprocess.run(cmd, check=True, capture_output=True)
    return out.stat().st_size


def decode_to_yuv(bitstream: Path, out: Path) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(bitstream),
                    "-f", "rawvideo", "-pix_fmt", "yuv420p", str(out)], check=True)
