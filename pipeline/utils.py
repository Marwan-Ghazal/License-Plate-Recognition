"""Shared helpers for the pipeline modules."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def load_image(path: str | Path) -> np.ndarray:
    """Read an image from *path* and return a BGR ndarray.

    Raises FileNotFoundError if the file cannot be read.
    """
    bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if bgr is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return bgr


def save_debug(img: np.ndarray, name: str, out_dir: Path) -> None:
    """Write a debug image as PNG to *out_dir*/*name*.png.

    Handles float / non-uint8 arrays by normalising to 0-255 first.
    """
    out = img
    if out.dtype != np.uint8:
        out = cv2.normalize(out, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    cv2.imwrite(str(out_dir / f"{name}.png"), out)
