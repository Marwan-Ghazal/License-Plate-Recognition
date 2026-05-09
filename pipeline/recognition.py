import os
import sys
from pathlib import Path

import cv2
import numpy as np
import pytesseract


# Match the lab notebook: no --oem, let Tesseract pick its default engine.
_WHITELIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def _ocr(img, psm="7"):
    cfg = f"--psm {psm} -c tessedit_char_whitelist={_WHITELIST}"
    text = pytesseract.image_to_string(img, config=cfg)
    return "".join(c for c in text if c.isalnum()).upper()


def segment_chars(binary):
    n_labels, _, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    H, W = binary.shape
    chars = []
    for i in range(1, n_labels):
        x, y, w, h, area = stats[i]
        if h < H * 0.30 or h > H * 0.95: continue
        if w > W * 0.30 or area < 30:    continue
        ar = w / h if h else 0
        if ar > 1.2 or ar < 0.05:        continue
        chars.append((x, binary[y:y+h, x:x+w]))
    return [c for _, c in sorted(chars, key=lambda t: t[0])]


def recognize(binary_plate):
    # Tesseract wants black-on-white; we have white-on-black, so invert.
    inv = cv2.bitwise_not(binary_plate)

    # Strategy A: OCR the whole upscaled plate.
    big = cv2.resize(inv, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    whole = _ocr(big, psm="7")

    # Strategy B: OCR each segmented character, concatenate.
    chars = segment_chars(binary_plate)
    per_char = ""
    for c in chars:
        c_inv = cv2.bitwise_not(c)
        c_pad = cv2.copyMakeBorder(c_inv, 10, 10, 10, 10, cv2.BORDER_CONSTANT, 0)
        c_big = cv2.resize(c_pad, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        t = _ocr(c_big, psm="10")
        per_char += t[:1] if t else ""

    return whole if len(whole) >= len(per_char) else per_char


if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(PROJECT_ROOT))

    from pipeline.preprocessing import preprocess
    from pipeline.localization  import localize
    from pipeline.normalization import warp_plate, binarize

    SAMPLE_DIR = PROJECT_ROOT / "data" / "samples"
    SPLITS_DIR = PROJECT_ROOT / "data" / "splits"

    split = os.environ.get("LPR_SPLIT", "dev")
    files = [l.strip() for l in (SPLITS_DIR / f"{split}.txt").read_text().splitlines() if l.strip()]
    print(f"[INFO] Running on '{split}' split ({len(files)} images)\n")

    n_ok = 0
    for idx, fname in enumerate(files, start=1):
        bgr = cv2.imread(str(SAMPLE_DIR / fname))
        if bgr is None:
            print(f"[{idx}] {fname}: failed to load"); continue

        bgr_r, _, _, edges = preprocess(bgr)
        candidates = localize(edges)

        text, rank = "", None
        for r, c in enumerate(candidates, start=1):
            t = recognize(binarize(warp_plate(bgr_r, c["corners"])))
            if len(t) >= 3:
                text, rank = t, r
                break

        msg = f'"{text}" (rank #{rank})' if text else "no text"
        print(f"[{idx}] {fname}: {msg}")
        if text: n_ok += 1

    print(f"\n[DONE] {n_ok}/{len(files)} produced text")