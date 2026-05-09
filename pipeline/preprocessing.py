import os
from pathlib import Path
 
import cv2
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


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


KX = np.array([[-1, 0, 1],
               [-2, 0, 2],
               [-1, 0, 1]], dtype=np.float32)

KY = np.array([[-1, -2, -1],
               [ 0,  0,  0],
               [ 1,  2,  1]], dtype=np.float32)
 
# 3. SOBEL 
def _sobel(gray):
    padded  = np.pad(gray.astype(np.float32), 1, mode='reflect')
    windows = sliding_window_view(padded, (3, 3))   # shape (H, W, 3, 3)
 
    gx = np.einsum('ijkl,kl->ij', windows, KX)
    gy = np.einsum('ijkl,kl->ij', windows, KY)
 
    magnitude = np.sqrt(gx * gx + gy * gy)
    return (magnitude / (magnitude.max() + 1e-8)) * 255

def enhance_contrast(gray):
    g_min, g_max = gray.min(), gray.max()
    current_range = g_max - g_min

    # only stretch if image is genuinely low contrast (narrow tonal range)
    if current_range < 100:   # e.g. dark TH-52-73 image had range ~80
        return (gray - g_min) / (current_range + 1e-8) * 255
    else:
        return gray           # already wide range, don't touch it

# 4. EDGE DETECTION
def detect_edges(gray, method="canny"):
    grad = _sobel(gray)
 
    if method == "sobel":
        return grad.astype(np.uint8)
 
    # Adaptive thresholds from the gradient distribution of THIS image.
    low, high = 30.0, 70.0
 
    strong, weak = 255, 75
    edges = np.where(grad >= high, strong,
                     np.where(grad >= low, weak, 0)).astype(np.uint8)
 
    # Hysteresis (vectorized): a weak pixel survives iff any 3x3 neighbor
    # is strong. Iterate until no new promotions happen, so weak pixels
    # connected through a chain of weak-to-strong neighbors survive too.
    strong_mask = (edges == strong)
    weak_mask   = (edges == weak)
 
    while True:
        padded   = np.pad(strong_mask, 1, mode='constant', constant_values=False)
        nbr_view = sliding_window_view(padded, (3, 3))
        has_strong_neighbor = nbr_view.any(axis=(2, 3))
        promote = weak_mask & has_strong_neighbor
        if not promote.any():
            break
        strong_mask |= promote
        weak_mask   &= ~promote
 
    edges = np.where(strong_mask, 255, 0).astype(np.uint8)
 
    # Bridge tiny horizontal gaps so character strokes connect.
    kernel = np.ones((1, 2), np.uint8)
    edges  = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    return edges

# 5. PREPROCESS PIPELINE
def preprocess(bgr):
    gray = to_grayscale(bgr)
    gray = enhance_contrast(gray)
    
    # measure image contrast
    contrast = gray.std()
    
    if contrast > 40:
        # high contrast image — sharpening will over-fire, skip it
        smooth = gray.copy()
    else:
        # low contrast — apply gentle sharpening
        smooth = bilateral_smooth(gray)
    
    edges = detect_edges(smooth, method="canny")
    return gray, smooth, edges


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
 
        gray, smooth, edges = preprocess(bgr)
 
        try:
            assert smooth.shape == gray.shape, "Shape mismatch"
            assert smooth.dtype == gray.dtype, "Dtype mismatch"
            unique_vals = np.unique(edges)
            assert set(unique_vals).issubset({0, 255}), \
                f"Edge values invalid: {unique_vals}"
        except AssertionError as e:
            print(f"[{idx}] {fname}: assertion failed: {e}\n")
            continue
 
        save(gray,   fname, "gray")
        save(smooth, fname, "smooth")
        save(edges,  fname, "edges")
 
        print(f"[{idx}] {fname}")
        print(f"     gray   ({info(gray)})")
        print(f"     smooth ({info(smooth)})")
        print(f"     edges  ({info(edges)})\n")
 
    print("[DONE]")

