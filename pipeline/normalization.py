from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

import cv2
import numpy as np


Point = Tuple[float, float]


def order_quad_points(pts: Iterable[Point]) -> np.ndarray:
	"""Arrange 4 corner points in this order:
	top-left, top-right, bottom-right, bottom-left.
	"""
	pts_arr = np.array(list(pts), dtype=np.float32)
	if pts_arr.shape != (4, 2):
		raise ValueError(f"Expected 4 points of shape (4,2), got {pts_arr.shape}")

	s = pts_arr.sum(axis=1)
	diff = np.diff(pts_arr, axis=1).reshape(-1)

	tl = pts_arr[np.argmin(s)]
	br = pts_arr[np.argmax(s)]
	tr = pts_arr[np.argmin(diff)]
	bl = pts_arr[np.argmax(diff)]

	return np.array([tl, tr, br, bl], dtype=np.float32)


def warp_plate(
	bgr: np.ndarray,
	quad: Iterable[Point],
	target_size: tuple[int, int] = (300, 75),
) -> np.ndarray:
	"""Apply perspective transform to straighten the plate.

	Args:
		bgr: Original BGR image
		quad: 4 plate corner points in the original image
		target_size: Output size as (width, height)
	"""
	if bgr is None or not hasattr(bgr, "shape"):
		raise ValueError("bgr must be a numpy image array")

	w, h = int(target_size[0]), int(target_size[1])
	if w <= 0 or h <= 0:
		raise ValueError(f"Invalid target_size={target_size}")

	src = order_quad_points(quad)
	dst = np.array(
		[[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]],
		dtype=np.float32,
	)
	M = cv2.getPerspectiveTransform(src, dst)
	warped = cv2.warpPerspective(bgr, M, (w, h))
	return warped


def _to_gray_u8(img: np.ndarray) -> np.ndarray:
	if img.ndim == 3:
		gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	else:
		gray = img

	if gray.dtype != np.uint8:
		gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
	return gray


def binarize(
	plate_bgr: np.ndarray,
	method: str = "otsu",
) -> np.ndarray:
	"""Convert the plate image into black and white.

	Output format:
	- Background = white (255)
	- Characters = black (0)

	This format is usually easier for OCR systems.
	"""
	gray = _to_gray_u8(plate_bgr)

	m = (method or "otsu").lower().strip()
	if m == "otsu":
		_, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
	elif m in {"adaptive", "adapt", "adaptive_mean"}:
		# blockSize must be odd and > 1
		binary = cv2.adaptiveThreshold(
			gray,
			255,
			cv2.ADAPTIVE_THRESH_MEAN_C,
			cv2.THRESH_BINARY,
			31,
			10,
		)
	else:
		raise ValueError('method must be "otsu" or "adaptive"')

	# Auto-invert if needed so background is mostly white.
	white_ratio = float(np.mean(binary == 255))
	if white_ratio < 0.5:
		binary = cv2.bitwise_not(binary)

	return binary


def clean_binary(binary: np.ndarray, *, clear_border: bool = False) -> np.ndarray:
	"""Apply small cleanup operations to the binary plate image.

	- Opening removes tiny noise dots
	- Border clearing can remove strong plate borders
	"""
	if binary.dtype != np.uint8:
		binary = binary.astype(np.uint8)

	kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
	cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

	if clear_border:
		h, w = cleaned.shape[:2]
		pad = max(1, min(h, w) // 50)  # small, size-dependent
		cleaned[:pad, :] = 255
		cleaned[-pad:, :] = 255
		cleaned[:, :pad] = 255
		cleaned[:, -pad:] = 255

	# Ensure strict binary output
	cleaned = np.where(cleaned >= 128, 255, 0).astype(np.uint8)
	return cleaned


@dataclass(frozen=True)
class NormalizationResult:
	warped: np.ndarray
	binary: np.ndarray


def normalize_plate(
	bgr: np.ndarray,
	quad: Iterable[Point],
	*,
	target_size: tuple[int, int] = (300, 75),
	binarize_method: str = "otsu",
) -> NormalizationResult:
	"""Full normalization pipeline:
	1. Warp the plate
	2. Convert to binary
	3. Clean the binary image
	"""
	warped = warp_plate(bgr, quad, target_size=target_size)
	binary = clean_binary(binarize(warped, method=binarize_method))
	return NormalizationResult(warped=warped, binary=binary)


def _save(out_dir: Path, name: str, img: np.ndarray) -> None:
	out_dir.mkdir(parents=True, exist_ok=True)
	path = out_dir / f"{name}.png"
	if img.ndim == 2:
		cv2.imwrite(str(path), img)
	else:
		cv2.imwrite(str(path), img)


if __name__ == "__main__":
	# Simple self-check you can run with:
	#   python3 pipeline/normalization.py
	project_root = Path(__file__).resolve().parents[1]
	out_dir = project_root / "data" / "outputs" / "_normalization_selfcheck"

	# 1) Synthetic test for warp_plate():
	canvas = np.zeros((240, 420, 3), dtype=np.uint8)
	quad = np.array([[60, 80], [360, 60], [380, 140], [80, 160]], dtype=np.float32)
	cv2.polylines(canvas, [quad.astype(np.int32)], True, (255, 255, 255), 3)
	cv2.fillConvexPoly(canvas, quad.astype(np.int32), (220, 220, 220))
	cv2.putText(canvas, "ABC123", (110, 135), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)

	warped = warp_plate(canvas, quad, target_size=(300, 75))
	assert warped.shape[0] == 75 and warped.shape[1] == 300
	_save(out_dir, "synthetic_input", canvas)
	_save(out_dir, "warped", warped)

	# 2) Binarize + cleanup check
	binary = clean_binary(binarize(warped, method="otsu"))
	uniq = set(np.unique(binary).tolist())
	assert uniq.issubset({0, 255}) and len(uniq) <= 2
	_save(out_dir, "binary", binary)

	print(f"[OK] Wrote normalization self-check images to: {out_dir}")
