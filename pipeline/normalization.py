import os
import sys
from pathlib import Path

import cv2
import numpy as np


def order_quad_points(pts):
    pts = np.array(list(pts), dtype=np.float32)
    if pts.shape != (4, 2):
        raise ValueError(f"Expected (4, 2), got {pts.shape}")
    s, d = pts.sum(axis=1), np.diff(pts, axis=1).reshape(-1)
    return np.array([pts[s.argmin()], pts[d.argmin()],
                     pts[s.argmax()], pts[d.argmax()]], dtype=np.float32)


def warp_plate(bgr, quad, target_size=(300, 75)):
    w, h = target_size
    src = order_quad_points(quad)
    dst = np.array([[0, 0], [w-1, 0], [w-1, h-1], [0, h-1]], dtype=np.float32)
    M = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(bgr, M, (w, h))


def binarize(plate, method="otsu"):
    gray = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY) if plate.ndim == 3 else plate
    if gray.dtype != np.uint8:
        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    if method == "otsu":
        _, b = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    elif method in ("adaptive", "adaptive_mean"):
        b = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                  cv2.THRESH_BINARY, 31, 10)
    else:
        raise ValueError(f"Unknown method: {method}")

    # Auto-invert so characters end up white (background should be the majority).
    if (b == 255).mean() > 0.5:
        b = cv2.bitwise_not(b)
    return b


def clean_binary(binary):
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    return cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)


# ----- Self-verification -----
if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(PROJECT_ROOT))

    from pipeline.preprocessing import preprocess
    from pipeline.localization  import localize

    SAMPLE_DIR = PROJECT_ROOT / "data" / "samples"
    OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"
    SPLITS_DIR = PROJECT_ROOT / "data" / "splits"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    split = os.environ.get("LPR_SPLIT", "dev")
    files = (SPLITS_DIR / f"{split}.txt").read_text().splitlines()
    files = [f.strip() for f in files if f.strip()]
    print(f"[INFO] Running on '{split}' split ({len(files)} images)\n")

    for idx, fname in enumerate(files, start=1):
        bgr = cv2.imread(str(SAMPLE_DIR / fname))
        if bgr is None:
            print(f"[{idx}] {fname}: failed to load")
            continue

        bgr_r, _, _, edges = preprocess(bgr)
        candidates = localize(edges)

        if not candidates:
            print(f"[{idx}] {fname}: no candidates")
            continue

        for rank, cand in enumerate(candidates, start=1):
            warped = warp_plate(bgr_r, cand["corners"])
            binary = binarize(warped)
            stem = Path(fname).stem
            cv2.imwrite(str(OUTPUT_DIR / f"{stem}_warp{rank}.png"), warped)
            cv2.imwrite(str(OUTPUT_DIR / f"{stem}_binary{rank}.png"), binary)

        print(f"[{idx}] {fname}: {len(candidates)} candidate(s) normalized")

    print("[DONE]")