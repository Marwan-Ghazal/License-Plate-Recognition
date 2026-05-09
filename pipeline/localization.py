import os
from pathlib import Path
 
import cv2
import numpy as np

_RECT_KERN = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 5))



# 1. THRESHOLD EDGE MAP
def preprocess_edge_map(edge_map_gray):

    closed = cv2.morphologyEx(edge_map_gray, cv2.MORPH_CLOSE, _RECT_KERN)
    _, binary = cv2.threshold(closed, 0, 255,
                              cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    return binary

# 2. MORPHOLOGICAL CLOSING
def apply_morphological_closing(binary, kw=13, kh=5):
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kw, kh))
    return cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
 

# 3. CONTOUR EXTRACTION
def find_contours(binary):
    contours, _ = cv2.findContours(binary,
                                   cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    return list(contours)


# 4. GEOMETRY HELPERS
def order_points(pts):
    pts  = np.array(pts, dtype=np.float32)
    s    = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmin(diff)]
    bl = pts[np.argmax(diff)]
    return np.array([tl, tr, br, bl], dtype=np.float32)



def contour_to_corners(contour):

    rect = cv2.minAreaRect(contour)
    box  = cv2.boxPoints(rect)
    return order_points(box)


# 5. CANDIDATE FILTERING
def filter_candidates(contours, image_shape):
    h_img, w_img = image_shape[:2]
    total = h_img * w_img
 
    # Sort by area, take top 30 — keeps work bounded on noisy images.
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:30]
 
    AR_MIN  = 2.0
    AR_MAX  = 8.0
    W_MIN   = 30
    H_MIN   = 10
 
    candidates = []
    for c in contours:
        area = cv2.contourArea(c)
        if area <= 0:
            continue
 
        x, y, bw, bh = cv2.boundingRect(c)
        if bw < W_MIN or bh < H_MIN:
            continue
 
        aspect = bw / float(bh)
        if not (AR_MIN <= aspect <= AR_MAX):
            continue
 
        candidates.append({
            "contour" : c,
            "bbox"    : (x, y, bw, bh),
            "aspect"  : aspect,
            "area"    : area,
            "area_pct": area / total,
        })
 
    # Keep insertion order (which is largest-area first), no scoring needed.
    # Person 4 will OCR each candidate and accept whichever returns text.
    return candidates

# 6. LOCALIZATION PIPELINE
def find_plate_candidates(binary_mask, top_n=5):
    contours   = find_contours(binary_mask)
    candidates = filter_candidates(contours, binary_mask.shape)
    top        = candidates[:top_n]
 
    for d in top:
        d["corners"] = contour_to_corners(d["contour"])
 
    return top
 


def localize(edge_map, top_n=5):
    binary     = preprocess_edge_map(edge_map)
    binary     = apply_morphological_closing(binary, kw=15, kh=5)  # extra pass
    candidates = find_plate_candidates(binary, top_n=top_n)
    return candidates

if __name__ == "__main__":
    import sys
 
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(PROJECT_ROOT))
    from pipeline.preprocessing import preprocess
 
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
 
    n_with_candidates = 0
 
    for idx, fname in enumerate(files, start=1):
        path = SAMPLE_DIR / fname
        bgr = cv2.imread(str(path))
        if bgr is None:
            print(f"[{idx}] {fname}: failed to load\n")
            continue
 
        bgr_r, gray, edges = preprocess(bgr)
        candidates = localize(edges)
 
        # Visualization: draw candidates on the resized BGR
        vis = bgr_r.copy()
        colors = [(0, 255, 0), (0, 200, 255), (255, 0, 200),
                  (255, 255, 0), (0, 100, 255)]
        for i, d in enumerate(candidates):
            x, y, w, h = d["bbox"]
            color = colors[i % len(colors)]
            cv2.rectangle(vis, (x, y), (x + w, y + h), color, 2)
            cv2.putText(vis, f"#{i+1}", (x, max(15, y - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
 
        out_name = f"{Path(fname).stem}_localized.png"
        cv2.imwrite(str(OUTPUT_DIR / out_name), vis)
 
        if candidates:
            n_with_candidates += 1
 
        print(f"[{idx}] {fname}: {len(candidates)} candidate(s)")
        for i, d in enumerate(candidates):
            print(f"     #{i+1}: bbox={d['bbox']}  aspect={d['aspect']:.2f}  "
                  f"area_pct={d['area_pct']*100:.2f}%")
        print()
 
    print(f"[DONE] {n_with_candidates}/{len(files)} images had at least one candidate")
 