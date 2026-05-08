import sys

from .utils import load_image, save_debug

import cv2
import numpy as np

# Person 1
from .preprocessing import preprocess, detect_edges

# Person 2
from .localization import apply_morphological_closing, filter_candidates, find_contours, preprocess_edge_map

# Person 3
from .normalization import binarize, clean_binary, warp_plate

# Person 4
# from .recognition import segment_chars, recognize


def run_pipeline(image_path):
    results = {}
    plate_text = ""

    # 1. Load image
    try:
        bgr = load_image(image_path)
        results["input"] = bgr
    except Exception as e:
        print(f"[ERROR] load_image: {e}")
        return {"error": str(e), "plate_text": ""}

    # 2. Preprocessing (Grayscale + smoothing)
    try:
        gray, smooth, _ = preprocess(bgr)
        results["grayscale"] = gray
        results["bilateral"] = smooth
        save_debug(gray, "grayscale")
        save_debug(smooth, "bilateral")
    except Exception as e:
        print(f"[ERROR] preprocess: {e}")
        smooth = None
        gray = None

    # 3. Edge Detection
    try:
        edges = detect_edges(smooth)
        results["edges"] = edges
        save_debug(edges, "edges")
    except Exception as e:
        print(f"[ERROR] detect_edges: {e}")
        edges = None

    # 4. Morphology + contour filtering (Person 2)
    try:
        if edges is None:
            raise ValueError("edges is None")

        binary_edge = preprocess_edge_map(edges, threshold=200)
        mask = apply_morphological_closing(binary_edge, kw=25, kh=7)
        results["morphology"] = mask
        save_debug(mask, "morphology")

        contours = find_contours(mask)
        candidates = filter_candidates(contours, mask.shape)

        # Debug image: draw top candidates (up to 3) on a copy of the original.
        contour_vis = bgr.copy()
        for d in candidates[:3]:
            cv2.drawContours(contour_vis, [d["contour"]], -1, (0, 255, 0), 2)
        results["contours"] = contour_vis
        save_debug(contour_vis, "contours")
    except Exception as e:
        print(f"[ERROR] morphology: {e}")
        mask = None
        candidates = []

    # 5. Plate Detection -> pick best candidate and convert to a 4-point quad
    try:
        if not candidates:
            quad = None
        else:
            best = candidates[0]
            rect = cv2.minAreaRect(best["contour"])
            quad = cv2.boxPoints(rect).astype(np.float32)
    except Exception as e:
        print(f"[ERROR] plate detection: {e}")
        quad = None

    # 6. Warp Plate (Normalization - Stage 5)
    try:
        if quad is None:
            plate = None
        else:
            plate = warp_plate(bgr, quad, target_size=(300, 75))
            results["warped"] = plate
            save_debug(plate, "warped")
    except Exception as e:
        print(f"[ERROR] warp: {e}")
        plate = None

    # 7. Binarization (Normalization - Stage 6)
    try:
        if plate is None:
            binary = None
        else:
            binary = clean_binary(binarize(plate, method="otsu"))
            results["binary"] = binary
            save_debug(binary, "binary")
    except Exception as e:
        print(f"[ERROR] binarize: {e}")
        binary = None

    # 8. Segmentation
    try:
        # chars = segment_chars(binary)
        chars = []
    except Exception as e:
        print(f"[ERROR] segmentation: {e}")
        chars = []

    # 9. Recognition
    try:
        # plate_text = recognize(chars)
        plate_text = "TODO"
    except Exception as e:
        print(f"[ERROR] recognition: {e}")

    results["plate_text"] = plate_text

    return results

# CLI ENTRY
def main():
    if len(sys.argv) < 2:
        print("Usage: python -m lpr.pipeline path/to/image.jpg")
        sys.exit(1)

    path = sys.argv[1]

    results = run_pipeline(path)

    print("\n=== PIPELINE RESULT ===")
    for k, v in results.items():
        if k == "plate_text":
            print(f"{k}: {v}")
        else:
            print(f"{k}: [image]")


if __name__ == "__main__":
    main()