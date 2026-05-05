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
def bilateral_smooth(gray, d=11, sigma_color=30, sigma_space=30):
    radius = d // 2
    padded = np.pad(gray, radius, mode='reflect')
    output = np.zeros_like(gray)

    x, y = np.meshgrid(np.arange(d), np.arange(d))
    center = radius
    spatial = np.exp(-((x - center) ** 2 + (y - center) ** 2) / (2 * sigma_space ** 2))

    for i in range(gray.shape[0]):
        for j in range(gray.shape[1]):

            region = padded[i:i + d, j:j + d]

            intensity = np.exp(-((region - gray[i, j]) ** 2) / (2 * sigma_color ** 2))

            weights = spatial * intensity
            weights_sum = np.sum(weights) + 1e-8  # avoid divide by zero

            output[i, j] = np.sum(weights * region) / weights_sum

    return output

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
    return (gray - g_min) / (g_max - g_min + 1e-8) * 255

# 4. EDGE DETECTION
def detect_edges(gray, method="canny"):
    grad = _sobel(gray)

    if method == "sobel":
        return grad.astype(np.uint8)

    # -------- FIXED CANNY --------
    med = np.median(gray)   # ✅ use original image

    low = 0.5 * med
    high = 1.2 * med

    strong = 255
    weak = 75

    edges = np.zeros_like(grad)

    strong_i, strong_j = np.where(grad >= high)
    weak_i, weak_j = np.where((grad >= low) & (grad < high))

    edges[strong_i, strong_j] = strong
    edges[weak_i, weak_j] = weak

    # hysteresis
    h, w = edges.shape
    for i in range(1, h - 1):
        for j in range(1, w - 1):
            if edges[i, j] == weak:
                if np.any(edges[i-1:i+2, j-1:j+2] == strong):
                    edges[i, j] = strong
                else:
                    edges[i, j] = 0

    # enforce binary
    edges[edges != 255] = 0
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    return edges.astype(np.uint8)

# 5. PREPROCESS PIPELINE
def preprocess(bgr):
    """
    grayscale → bilateral → edges
    Returns all intermediate outputs for debugging
    """
    gray = to_grayscale(bgr)
    gray = enhance_contrast(gray)
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

    # take up to 6 images
    files = files[:6]

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

    print("[DONE]Multi-image test completed")