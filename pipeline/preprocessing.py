import numpy as np
import os
import  cv2


# 1. GRAYSCALE 
def to_grayscale(bgr):
    b = bgr[:, :, 0].astype(np.float32)
    g = bgr[:, :, 1].astype(np.float32)
    r = bgr[:, :, 2].astype(np.float32)

    gray = 0.114 * b + 0.587 * g + 0.299 * r
    return gray  # keep float32


# 2. BILATERAL FILTER
def bilateral_smooth(gray, d=11, sigma_color=50, sigma_space=50):
    """
    Replaced heavy bilateral with: light Gaussian noise removal + unsharp mask.
    Parameters kept for API compatibility but ignored internally.
    """
    # Step 1 — light 3x3 Gaussian (removes pixel noise only)
    k = np.array([[1, 2, 1],
                  [2, 4, 2],
                  [1, 2, 1]], dtype=np.float32) / 16

    padded = np.pad(gray, 1, mode='reflect')
    blurred = np.zeros_like(gray)
    for i in range(gray.shape[0]):
        for j in range(gray.shape[1]):
            blurred[i, j] = np.sum(k * padded[i:i+3, j:j+3])

    # Step 2 — unsharp mask (sharpen edges)
    # sharpened = original + alpha * (original - blurred)
    alpha = 1.5
    sharpened = gray + alpha * (gray - blurred)

    return np.clip(sharpened, 0, 255).astype(np.float32)

# 3. SOBEL 
def _sobel(gray):
    Kx = np.array([[-1, 0, 1],
                   [-2, 0, 2],
                   [-1, 0, 1]])

    Ky = np.array([[-1, -2, -1],
                   [0,  0,  0],
                   [1,  2,  1]])

    padded = np.pad(gray, 1, mode='reflect')
    gx = np.zeros_like(gray)
    gy = np.zeros_like(gray)

    for i in range(gray.shape[0]):
        for j in range(gray.shape[1]):
            region = padded[i:i+3, j:j+3]

            gx[i, j] = np.sum(Kx * region)
            gy[i, j] = np.sum(Ky * region)

    magnitude = np.sqrt(gx**2 + gy**2)

    # normalize safely
    max_val = np.max(magnitude) + 1e-8
    magnitude = (magnitude / max_val) * 255

    return magnitude

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

    med = np.median(gray)

    # ADAPTIVE: if image is very dark, median is too low to use as base
    # use gradient percentiles instead of median of gray
    nonzero = grad[grad > 10]   # ignore flat regions
    if len(nonzero) == 0:
        low, high = 30, 60      # safe fallback
    else:
        p_low  = float(np.percentile(nonzero, 30))
        p_high = float(np.percentile(nonzero, 70))

        # blend: trust gradient percentiles more than median
        low  = 50
        high = 100
    strong = 255
    weak   = 75

    edges = np.zeros_like(grad)
    strong_i, strong_j = np.where(grad >= high)
    weak_i,   weak_j   = np.where((grad >= low) & (grad < high))
    edges[strong_i, strong_j] = strong
    edges[weak_i,   weak_j]   = weak

    # hysteresis
    h, w = edges.shape
    for i in range(1, h - 1):
        for j in range(1, w - 1):
            if edges[i, j] == weak:
                if np.any(edges[i-1:i+2, j-1:j+2] == strong):
                    edges[i, j] = strong
                else:
                    edges[i, j] = 0

    edges[edges != 255] = 0
    kernel = np.ones((3, 5), np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    return edges.astype(np.uint8)

# 5. PREPROCESS PIPELINE
def preprocess(bgr):
    gray = to_grayscale(bgr)
    gray = enhance_contrast(gray)
    
    # measure image contrast
    contrast = gray.std()
    
    if contrast > 60:
        # high contrast image — sharpening will over-fire, skip it
        smooth = gray.copy()
    else:
        # low contrast — apply gentle sharpening
        smooth = bilateral_smooth(gray)
    
    edges = detect_edges(smooth, method="canny")
    return gray, smooth, edges


if __name__ == "__main__":
    SAMPLE_DIR = "data/samples"
    OUTPUT_DIR = "data/outputs"

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Collect images
    files = [f for f in os.listdir(SAMPLE_DIR)
             if f.lower().endswith((".jpg", ".png", ".jpeg"))]

    if len(files) == 0:
        raise RuntimeError("No images found in data/samples/")

    import random
    files = random.sample(files, min(1000, len(files)))

    print(f"[INFO] Testing on {len(files)} images\n")

    # 2. Process each image
    for idx, fname in enumerate(files):
        path = os.path.join(SAMPLE_DIR, fname)
        print(f"[{idx+1}] Processing: {fname}")

        bgr = cv2.imread(path)
        if bgr is None:
            print("Failed to load image\n")
            continue

        # run pipeline
        gray, smooth, edges = preprocess(bgr)

        # 3. Assertions
        try:
            assert smooth.shape == gray.shape, "Shape mismatch"
            assert smooth.dtype == gray.dtype, "Dtype mismatch"

            unique_vals = np.unique(edges)
            assert set(unique_vals).issubset({0, 255}), \
                f"Edge values invalid: {unique_vals}"

        except AssertionError as e:
            print(f"Assertion failed: {e}")
            continue

        # 4. Save outputs
        def save(img, name):
            if img.dtype != np.uint8:
                img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
                img = img.astype(np.uint8)

            out_name = f"{os.path.splitext(fname)[0]}_{name}.png"
            cv2.imwrite(os.path.join(OUTPUT_DIR, out_name), img)

        save(gray, "gray")
        save(smooth, "smooth")
        save(edges, "edges")

        # 5. Summary per image
        def info(img):
            return f"shape={img.shape}, min={img.min():.1f}, max={img.max():.1f}"

        print(
            f"gray({info(gray)}) | "
            f"smooth({info(smooth)}) | "
            f"edges({info(edges)})\n"
        )

    print("[DONE] Multi-image test completed")

