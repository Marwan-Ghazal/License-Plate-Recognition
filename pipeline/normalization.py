from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

import cv2
import numpy as np


Point = Tuple[float, float]


def order_quad_points(pts: Iterable[Point]) -> np.ndarray:

    pts_arr = np.array(list(pts), dtype=np.float32)
    if pts_arr.shape != (4, 2):
        raise ValueError(f"Expected 4 points of shape (4,2), got {pts_arr.shape}")

    s    = pts_arr.sum(axis=1)
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

    # Auto-invert toward characters-white. Plates are mostly background, so
    # if more than half the image is white, the threshold produced
    # background-white / characters-black — flip it.
    white_ratio = float(np.mean(binary == 255))
    if white_ratio > 0.5:
        binary = cv2.bitwise_not(binary)

    return binary


def clean_binary(binary: np.ndarray, *, clear_border: bool = False) -> np.ndarray:

    if binary.dtype != np.uint8:
        binary = binary.astype(np.uint8)

    kernel  = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    if clear_border:
        # Border pixels are now characters (white) so we paint them BLACK
        # to remove the plate frame. (In the old polarity this was 255.)
        h, w = cleaned.shape[:2]
        pad  = max(1, min(h, w) // 50)
        cleaned[:pad,  :]   = 0
        cleaned[-pad:, :]   = 0
        cleaned[:,  :pad]   = 0
        cleaned[:, -pad:]   = 0

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
    clear_border: bool = False,
) -> NormalizationResult:

    warped = warp_plate(bgr, quad, target_size=target_size)
    binary = clean_binary(binarize(warped, method=binarize_method),
                          clear_border=clear_border)
    return NormalizationResult(warped=warped, binary=binary)


# ---------------------------------------------------------------------------
# Self-verification: run on real plates from the split files
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    import sys

    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(PROJECT_ROOT))

    from pipeline.preprocessing import preprocess
    from pipeline.localization  import localize

    SAMPLE_DIR = PROJECT_ROOT / "data" / "samples"
    OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"
    SPLITS_DIR = PROJECT_ROOT / "data" / "splits"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    split = os.environ.get("LPR_SPLIT", "dev")
    split_file = SPLITS_DIR / f"{split}.txt"
    if not split_file.exists():
        raise RuntimeError(f"Split file not found: {split_file}. "
                           "Run scripts/generate_splits.py first.")

    files = [l.strip() for l in split_file.read_text().splitlines() if l.strip()]
    print(f"[INFO] Running on '{split}' split ({len(files)} images)\n")

    n_processed     = 0
    n_no_candidates = 0

    for idx, fname in enumerate(files, start=1):
        path = SAMPLE_DIR / fname
        bgr  = cv2.imread(str(path))
        if bgr is None:
            print(f"[{idx}] {fname}: failed to load\n")
            continue

        # Run the upstream pipeline
        bgr_r, _, edges = preprocess(bgr)
        candidates      = localize(edges)

        if not candidates:
            print(f"[{idx}] {fname}: no candidates from localizer")
            n_no_candidates += 1
            continue

        # Normalize each candidate. Saving multiple per image helps with
        # ranking diagnosis: even when the plate is rank #2 or #3, you can
        # still see what its warped+binary version looks like.
        top1_white_pct = None
        for rank, cand in enumerate(candidates, start=1):
            corners = cand["corners"]
            try:
                result = normalize_plate(bgr_r, corners, binarize_method="otsu")
            except Exception as e:
                print(f"[{idx}] {fname} candidate #{rank}: warp failed ({e})")
                continue

            # Sanity assertions
            assert result.warped.shape[:2] == (75, 300), \
                f"warp shape wrong: {result.warped.shape}"
            assert result.binary.shape == (75, 300), \
                f"binary shape wrong: {result.binary.shape}"
            unique = set(np.unique(result.binary).tolist())
            assert unique.issubset({0, 255}), f"binary not strict: {unique}"

            if rank == 1:
                top1_white_pct = 100 * (result.binary == 255).mean()

            stem = Path(fname).stem
            cv2.imwrite(str(OUTPUT_DIR / f"{stem}_warp{rank}.png"),   result.warped)
            cv2.imwrite(str(OUTPUT_DIR / f"{stem}_binary{rank}.png"), result.binary)

        msg = f"[{idx}] {fname}: {len(candidates)} candidate(s) normalized"
        if top1_white_pct is not None:
            msg += f" (top1 binary white={top1_white_pct:.1f}%)"
        print(msg)
        n_processed += 1

    print(f"\n[DONE] {n_processed}/{len(files)} images normalized, "
          f"{n_no_candidates} with no candidates")