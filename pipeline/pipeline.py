from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

from .utils import load_image, save_debug
from .preprocessing import preprocess, detect_edges
from .localization import localize, preprocess_edge_map, apply_morphological_closing
from .normalization import binarize, clean_binary, warp_plate
from .recognition import recognize


def run_pipeline(image_bgr: np.ndarray, run_id: str, outputs_dir: Path) -> dict:
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

    # 4–5. Localization (morphology + contour filtering)
    try:
        if edges is None:
            raise ValueError("edges is None")

        candidates = localize(edges)

        # Debug: morphology mask (from first internal step)
        binary_edge = preprocess_edge_map(edges)
        mask = apply_morphological_closing(binary_edge)
        save_debug(mask, "morphology", run_dir)
        result["morphology"] = str(run_dir / "morphology.png")

        contour_vis = bgr.copy()
        for d in candidates[:3]:
            cv2.drawContours(contour_vis, [d["contour"]], -1, (0, 255, 0), 2)
        save_debug(contour_vis, "contours", run_dir)
        result["contours"] = str(run_dir / "contours.png")
    except Exception as e:
        print(f"[ERROR] localization: {e}")
        candidates = []

    # 5b–8. Try each candidate: warp → binarize → OCR, keep first with text ≥ 3 chars
    plate = None
    binary = None
    for cand in (candidates or []):
        try:
            trial_plate = warp_plate(bgr, cand["corners"], target_size=(300, 75))
            trial_binary = binarize(trial_plate, method="otsu")
            trial_text = recognize(trial_binary)
            if len(trial_text) >= 3:
                plate = trial_plate
                binary = trial_binary
                plate_text = trial_text
                break
        except Exception:
            continue

    # Save the winning warp/binary (or blank placeholders if none found)
    try:
        if plate is not None:
            save_debug(plate, "warped", run_dir)
        else:
            save_debug(np.zeros((75, 300, 3), dtype=np.uint8), "warped", run_dir)
        result["warped"] = str(run_dir / "warped.png")
    except Exception as e:
        print(f"[ERROR] save warped: {e}")

    try:
        if binary is not None:
            save_debug(binary, "binary", run_dir)
        else:
            save_debug(np.zeros((75, 300), dtype=np.uint8), "binary", run_dir)
        result["binary"] = str(run_dir / "binary.png")
    except Exception as e:
        print(f"[ERROR] save binary: {e}")

    try:
        if binary is not None:
            save_debug(binary, "segmented", run_dir)
        else:
            save_debug(np.zeros((75, 300), dtype=np.uint8), "segmented", run_dir)
        result["segmented"] = str(run_dir / "segmented.png")
    except Exception as e:
        print(f"[ERROR] save segmented: {e}")

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