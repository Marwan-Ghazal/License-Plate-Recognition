import sys

from .utils import load_image, save_debug

# Person 1
from .preprocessing import preprocess, detect_edges

# Person 2
# from .localization import close_morphology, find_plate_candidates

# Person 3
# from .normalization import warp_plate, binarize

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

    # 2. Preprocessing

    try:
        gray, smooth, _ = preprocess(bgr)
        results["preprocess"] = smooth
        save_debug(smooth, "preprocess")
    except Exception as e:
        print(f"[ERROR] preprocess: {e}")
        smooth = None

    # 3. Edge Detection
    try:
        edges = detect_edges(smooth)
        results["edges"] = edges
        save_debug(edges, "edges")
    except Exception as e:
        print(f"[ERROR] detect_edges: {e}")
        edges = None

    # 4. Morphology (Person 2)
    try:
        # mask = close_morphology(edges)
        # results["morphology"] = mask
        # save_debug(mask, "morphology")
        mask = None
    except Exception as e:
        print(f"[ERROR] morphology: {e}")
        mask = None

    # 5. Plate Detection
    try:
        # candidates = find_plate_candidates(mask, bgr)
        # quad = candidates[0]
        quad = None
    except Exception as e:
        print(f"[ERROR] plate detection: {e}")
        quad = None

    # 6. Warp Plate
    try:
        # plate = warp_plate(bgr, quad)
        # results["plate"] = plate
        # save_debug(plate, "plate")
        plate = None
    except Exception as e:
        print(f"[ERROR] warp: {e}")
        plate = None

    # 7. Binarization
    try:
        # binary = binarize(plate)
        # results["binary"] = binary
        # save_debug(binary, "binary")
        binary = None
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