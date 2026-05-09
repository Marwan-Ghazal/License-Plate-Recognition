import os
from pathlib import Path
 
import cv2
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

TARGET_WIDTH = 600

def resize_to_width(bgr, width=TARGET_WIDTH):
    """Resize so the image has the given width, preserving aspect ratio."""
    h, w = bgr.shape[:2]
    if w == width:
        return bgr
    new_h = int(h * (width / w))
    return cv2.resize(bgr, (width, new_h), interpolation=cv2.INTER_AREA)
# 1. GRAYSCALE 
def to_grayscale(bgr):
    b = bgr[:, :, 0].astype(np.float32)
    g = bgr[:, :, 1].astype(np.float32)
    r = bgr[:, :, 2].astype(np.float32)

    gray = 0.114 * b + 0.587 * g + 0.299 * r
    return gray  # keep float32


# 2. BILATERAL FILTER
def bilateral_smooth(gray, d=5, sigma_color=15, sigma_space=15):
    return cv2.bilateralFilter(gray.astype(np.float32),
                               d=d,
                               sigmaColor=sigma_color,
                               sigmaSpace=sigma_space)

_RECT_KERN = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 5))

KX = np.array([[-1, 0, 1],
               [-2, 0, 2],
               [-1, 0, 1]], dtype=np.float32)


def sobelx(gray):

    padded  = np.pad(gray.astype(np.float32), 1, mode='reflect')
    windows = sliding_window_view(padded, (3, 3))
    return np.einsum('ijkl,kl->ij', windows, KX)


# 4. EDGE DETECTION
def detect_edges(gray, method="canny"):
    g = gray.astype(np.uint8) if gray.dtype != np.uint8 else gray

    # 1) BlackHat
    blackhat = cv2.morphologyEx(g, cv2.MORPH_BLACKHAT, _RECT_KERN)

    # 2) Sobel-x — manual implementation (vectorized for speed)
    grad_x = sobelx(blackhat)
    grad_x = np.absolute(grad_x)

    # 3) Normalize to [0, 255] uint8
    g_min, g_max = grad_x.min(), grad_x.max()
    if g_max - g_min < 1e-6:
        return np.zeros_like(g, dtype=np.uint8)
    norm = ((grad_x - g_min) / (g_max - g_min) * 255).astype(np.uint8)
    return norm
 
# 5. PREPROCESS PIPELINE
def preprocess(bgr):

    bgr_resized = resize_to_width(bgr, TARGET_WIDTH)
    gray        = to_grayscale(bgr_resized)
    smooth      = bilateral_smooth(gray)
    edges       = detect_edges(smooth)
    return bgr_resized, gray, smooth, edges


if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    SAMPLE_DIR   = PROJECT_ROOT / "data" / "samples"
    OUTPUT_DIR   = PROJECT_ROOT / "data" / "outputs"
    SPLITS_DIR   = PROJECT_ROOT / "data" / "splits"
 
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
 
    split = os.environ.get("LPR_SPLIT", "dev")
    split_file = SPLITS_DIR / f"{split}.txt"
    if not split_file.exists():
        raise RuntimeError(f"Split file not found: {split_file}. "
                           "Run scripts/generate_splits.py first.")
 
    files = [line.strip() for line in split_file.read_text().splitlines()
             if line.strip()]
    print(f"[INFO] Running on '{split}' split ({len(files)} images)\n")
 
    def save(img, fname, suffix):
        out = img
        if out.dtype != np.uint8:
            out = cv2.normalize(out, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        out_name = f"{Path(fname).stem}_{suffix}.png"
        cv2.imwrite(str(OUTPUT_DIR / out_name), out)
 
    def info(img):
        return f"shape={img.shape}, min={img.min():.1f}, max={img.max():.1f}"
 
    for idx, fname in enumerate(files, start=1):
        path = SAMPLE_DIR / fname
        bgr = cv2.imread(str(path))
        if bgr is None:
            print(f"[{idx}] {fname}: failed to load\n")
            continue
 
        bgr_r, gray, smooth, edges = preprocess(bgr)
 
        # Sanity assertions
        assert bgr_r.shape[1] == TARGET_WIDTH, "resize failed"
        assert gray.shape == bgr_r.shape[:2], "gray/bgr shape mismatch"
        assert edges.shape == bgr_r.shape[:2], "edges/bgr shape mismatch"
        assert edges.dtype == np.uint8, "edges must be uint8"
 
        save(gray,  fname, "gray")
        save(edges, fname, "edges")
 
        print(f"[{idx}] {fname}")
        print(f"     gray   ({info(gray)})")
        print(f"     edges  ({info(edges)})\n")
 
    print("[DONE]")