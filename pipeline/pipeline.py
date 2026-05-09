"""Pipeline orchestrator — runs all stages and returns a flat dict.

Contract (same shape as the stub in backend/pipeline_stub.py):

    run_pipeline(image_bgr, run_id, outputs_dir) -> dict
        keys: grayscale, bilateral, edges, morphology, contours,
              warped, binary, segmented, plate_text
        Each stage key maps to the absolute path of its saved PNG.
        plate_text is the recognised plate string (empty if not found).
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

from .utils import load_image, save_debug

# Person 1
from .preprocessing import preprocess, detect_edges

# Person 2
from .localization import apply_morphological_closing, filter_candidates, find_contours, preprocess_edge_map

# Person 3
from .normalization import binarize, clean_binary, warp_plate

# Person 4
from .recognition import recognize


def run_pipeline(image_bgr: np.ndarray, run_id: str, outputs_dir: Path) -> dict:
    """Run the full LPR pipeline on a BGR image.

    Saves 8 debug PNGs to ``outputs_dir / run_id / <stage>.png`` and returns
    a flat dict mapping each stage name to its absolute path string, plus
    ``plate_text`` with the OCR result.
    """
    run_dir = outputs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, str] = {}
    plate_text = ""

    # 1–2. Preprocessing (grayscale + bilateral smoothing)
    try:
        bgr, gray, smooth, edges = preprocess(image_bgr)
        save_debug(gray, "grayscale", run_dir)
        save_debug(smooth, "bilateral", run_dir)
        result["grayscale"] = str(run_dir / "grayscale.png")
        result["bilateral"] = str(run_dir / "bilateral.png")
    except Exception as e:
        print(f"[ERROR] preprocess: {e}")
        smooth = None
        edges = None

    # 3. Edge detection (already done inside preprocess, but keep explicit)
    try:
        if edges is None:
            edges = detect_edges(smooth)
        save_debug(edges, "edges", run_dir)
        result["edges"] = str(run_dir / "edges.png")
    except Exception as e:
        print(f"[ERROR] detect_edges: {e}")
        edges = None

    # 4. Morphology + contour filtering
    try:
        if edges is None:
            raise ValueError("edges is None")

        binary_edge = preprocess_edge_map(edges)
        mask = apply_morphological_closing(binary_edge, kw=25, kh=7)
        save_debug(mask, "morphology", run_dir)
        result["morphology"] = str(run_dir / "morphology.png")

        contours = find_contours(mask)
        candidates = filter_candidates(contours, mask.shape)

        contour_vis = bgr.copy()
        for d in candidates[:3]:
            cv2.drawContours(contour_vis, [d["contour"]], -1, (0, 255, 0), 2)
        save_debug(contour_vis, "contours", run_dir)
        result["contours"] = str(run_dir / "contours.png")
    except Exception as e:
        print(f"[ERROR] morphology: {e}")
        candidates = []

    # 5. Plate detection — pick best candidate
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

    # 6. Warp plate
    try:
        if quad is None:
            plate = None
        else:
            plate = warp_plate(bgr, quad, target_size=(300, 75))
            save_debug(plate, "warped", run_dir)
            result["warped"] = str(run_dir / "warped.png")
    except Exception as e:
        print(f"[ERROR] warp: {e}")
        plate = None

    # 7. Binarization
    try:
        if plate is None:
            binary = None
        else:
            binary = clean_binary(binarize(plate, method="otsu"))
            save_debug(binary, "binary", run_dir)
            result["binary"] = str(run_dir / "binary.png")
    except Exception as e:
        print(f"[ERROR] binarize: {e}")
        binary = None

    # 8. Segmentation + recognition
    try:
        if binary is not None:
            plate_text = recognize(binary)
        save_debug(binary if binary is not None else np.zeros((75, 300), dtype=np.uint8),
                    "segmented", run_dir)
        result["segmented"] = str(run_dir / "segmented.png")
    except Exception as e:
        print(f"[ERROR] recognition: {e}")

    result["plate_text"] = plate_text
    return result


# CLI ENTRY
def main():
    if len(sys.argv) < 2:
        print("Usage: python -m pipeline.pipeline path/to/image.jpg")
        sys.exit(1)

    path = sys.argv[1]
    import uuid
    run_id = uuid.uuid4().hex[:12]
    outputs_dir = Path(__file__).resolve().parents[1] / "data" / "outputs"

    bgr = load_image(path)
    result = run_pipeline(bgr, run_id, outputs_dir)

    print(f"\nrun_id: {run_id}")
    print("=== PIPELINE RESULT ===")
    for k, v in result.items():
        if k == "plate_text":
            print(f"plate_text: {v}")
        else:
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()