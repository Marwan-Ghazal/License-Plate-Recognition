import numpy as np
import os
import cv2


# 1. THRESHOLD EDGE MAP
def preprocess_edge_map(edge_map_gray, threshold=180):
    norm = cv2.normalize(edge_map_gray, None, 0, 255, cv2.NORM_MINMAX)
    blur = cv2.medianBlur(norm, 3)

    _, binary = cv2.threshold(blur, threshold, 255, cv2.THRESH_BINARY_INV)

    white_ratio = binary.mean() / 255

    # fallback to Otsu if threshold produces a degenerate binary map
    if white_ratio < 0.01 or white_ratio > 0.55:
        _, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    # small pre-dilation reconnects broken character strokes before wide closing
    pre_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    binary = cv2.dilate(binary, pre_kernel, iterations=1)

    return binary


# 2. MORPHOLOGICAL CLOSING
def apply_morphological_closing(binary, kw=25, kh=7):
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kw, kh))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    return closed


# 3. CONTOUR EXTRACTION
def find_contours(closed_mask):
    contours, _ = cv2.findContours(
        closed_mask,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_SIMPLE
    )
    return list(contours)


# 4. GEOMETRY HELPERS
def order_points(pts):
    pts = np.array(pts, dtype=np.float32)
    s    = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmin(diff)]
    bl = pts[np.argmax(diff)]
    return np.array([tl, tr, br, bl], dtype=np.float32)


def perspective_correct(src_img, contour, target_w=400, target_h=100):
    """Warp a contour region from src_img (gray or BGR) to a fixed rectangle."""
    rect = cv2.minAreaRect(contour)
    box  = cv2.boxPoints(rect)
    box  = order_points(box)

    dst = np.array([
        [0,            0           ],
        [target_w - 1, 0           ],
        [target_w - 1, target_h - 1],
        [0,            target_h - 1],
    ], dtype=np.float32)

    M      = cv2.getPerspectiveTransform(box, dst)
    warped = cv2.warpPerspective(src_img, M, (target_w, target_h))
    return warped


# 5. CANDIDATE FILTERING
def filter_candidates(contours, image_shape):
    h, w  = image_shape[:2]
    total = h * w

    AREA_MIN_PCT  = 0.0008
    AREA_MAX_PCT  = 0.15
    RATIO_MIN     = 2.0
    RATIO_MAX     = 7.5
    EXTENT_MIN    = 0.45
    SOLIDITY_MIN  = 0.35

    candidates = []

    for c in contours:
        area = cv2.contourArea(c)
        if area <= 0:
            continue

        area_pct = area / total
        if not (AREA_MIN_PCT <= area_pct <= AREA_MAX_PCT):
            continue

        rect = cv2.minAreaRect(c)
        (cx, cy), (rw, rh), angle = rect
        if rw == 0 or rh == 0:
            continue

        ratio = max(rw, rh) / max(1.0, min(rw, rh))
        if not (RATIO_MIN <= ratio <= RATIO_MAX):
            continue

        x, y, bw, bh = cv2.boundingRect(c)
        rect_area    = bw * bh
        extent       = area / rect_area if rect_area > 0 else 0
        if extent < EXTENT_MIN:
            continue

        hull      = cv2.convexHull(c)
        hull_area = cv2.contourArea(hull)
        solidity  = area / hull_area if hull_area > 0 else 0
        if solidity < SOLIDITY_MIN:
            continue

        peri   = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.03 * peri, True)

        score = (
            area_pct * 2.0  +
            solidity * 0.8  +
            extent   * 0.8  +
            min(ratio / 4.0, 1.5)
        )

        candidates.append({
            "contour" : c,
            "approx"  : approx,
            "area"    : area,
            "area_pct": area_pct,
            "ratio"   : ratio,
            "extent"  : extent,
            "solidity": solidity,
            "score"   : score,
            "n_pts"   : len(approx),
        })

    candidates.sort(key=lambda d: d["score"], reverse=True)
    return candidates


# 6. LOCALIZATION PIPELINE
def find_plate_candidates(closed_mask, orig_img=None, top_n=3):
    """
    Detect plate contours from closed_mask; warp crops from orig_img.
    orig_img can be grayscale or BGR — warped_plate will match its format.
    """
    contours   = find_contours(closed_mask)
    candidates = filter_candidates(contours, closed_mask.shape)
    top        = candidates[:top_n]

    if orig_img is not None:
        for d in top:
            try:
                d["warped_plate"] = perspective_correct(orig_img, d["contour"])
            except Exception:
                d["warped_plate"] = None

    return top


def localize(edge_map_gray, orig_img, kw=25, kh=7, threshold=200, top_n=3):
    """
    Detect plates using the edge map; crop warped regions from orig_img.

    Args:
        edge_map_gray : grayscale edge map (output of preprocessing.py)
        orig_img      : original BGR image to crop from
        kw, kh        : morphological closing kernel size (width, height)
        threshold     : binarization threshold for the edge map
        top_n         : number of top candidates to return

    Returns:
        list of candidate dicts, each containing:
            'warped_plate' -- BGR crop warped from orig_img
            'score', 'ratio', 'area_pct', 'approx', ...
    """
    binary     = preprocess_edge_map(edge_map_gray, threshold=threshold)
    closed     = apply_morphological_closing(binary, kw=kw, kh=kh)
    candidates = find_plate_candidates(closed, orig_img=orig_img, top_n=top_n)
    return candidates


if __name__ == "__main__":
    EDGE_DIR   = "data/outputs"   # edge maps produced by preprocessing.py
    SAMPLE_DIR = "data/samples"   # original BGR images
    OUTPUT_DIR = "data/outputs2"

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # collect edge maps and pair each with its original image
    edge_files = [f for f in os.listdir(EDGE_DIR)
                  if f.lower().endswith("_edges.png")]

    if len(edge_files) == 0:
        raise RuntimeError("No edge maps found in data/outputs/")

    import random
    edge_files = random.sample(edge_files, min(300, len(edge_files)))

    print(f"[INFO] Testing on {len(edge_files)} edge maps\n")

    for idx, fname in enumerate(edge_files):
        edge_path = os.path.join(EDGE_DIR, fname)
        print(f"[{idx+1}] Processing: {fname}")

        # derive original filename: strip the "_edges" suffix
        stem      = fname.replace("_edges.png", "")
        orig_path = None
        for ext in (".jpg", ".jpeg", ".png"):
            candidate_path = os.path.join(SAMPLE_DIR, stem + ext)
            if os.path.exists(candidate_path):
                orig_path = candidate_path
                break

        if orig_path is None:
            print(f"  Original image not found for {stem}, skipping\n")
            continue

        edge_gray = cv2.imread(edge_path, cv2.IMREAD_GRAYSCALE)
        orig_bgr  = cv2.imread(orig_path)

        if edge_gray is None or orig_bgr is None:
            print("  Failed to load image pair\n")
            continue

        candidates = localize(edge_gray, orig_bgr)

        # assertions
        try:
            assert isinstance(candidates, list), "candidates must be a list"
            assert len(candidates) <= 3, "too many candidates returned"
            for d in candidates:
                for key in ("contour", "approx", "area_pct", "ratio", "score", "warped_plate"):
                    assert key in d, f"missing key: {key}"
                assert 0.0 < d["area_pct"] < 1.0, "area_pct out of range"
                assert d["score"] >= 0, "negative score"

        except AssertionError as e:
            print(f"  Assertion failed: {e}")
            continue

        # save warped BGR crops from the original image
        saved = 0
        for i, d in enumerate(candidates):
            wp = d.get("warped_plate")
            if wp is not None:
                out_name = f"{stem}_warp{i+1}.png"
                cv2.imwrite(os.path.join(OUTPUT_DIR, out_name), wp)
                saved += 1

        def info(d):
            return (f"area={d['area_pct']*100:.1f}%  "
                    f"ratio={d['ratio']:.2f}  "
                    f"score={d['score']:.4f}  "
                    f"pts={d['n_pts']}")

        print(f"  {len(candidates)} candidate(s)  |  {saved} crop(s) saved")
        for i, d in enumerate(candidates):
            print(f"  #{i+1}: {info(d)}")
        print()

    print("[DONE] Localization test completed")
