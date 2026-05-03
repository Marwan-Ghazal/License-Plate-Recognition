"""Temporary stand-in for the real pipeline.

Person 1 will replace this with a real import from ``pipeline.pipeline``
once integration is done. Keep this file's signature identical to the real one
so swapping is a one-line change in main.py.

Real signature (from the team plan):

    def run_pipeline(image_bgr: np.ndarray,
                     run_id: str,
                     outputs_dir: Path) -> dict:
        return {
            'grayscale':  str,   # path to PNG
            'bilateral':  str,
            'edges':      str,
            'morphology': str,
            'contours':   str,
            'warped':     str,
            'binary':     str,
            'segmented':  str,
            'plate_text': str,
        }

This stub takes a saved image path instead of a numpy array so we don't need
OpenCV in the backend skeleton. We'll switch to the array signature when the
real pipeline lands.
"""

from __future__ import annotations

import shutil
from pathlib import Path

STAGE_NAMES = [
    "grayscale", "bilateral", "edges", "morphology",
    "contours", "warped", "binary", "segmented",
]


def run_pipeline_stub(image_path: Path, run_id: str, outputs_dir: Path) -> dict:
    """Fake recognition that copies the input image to each stage slot.

    Returns the same flat-dict shape as the real pipeline so the frontend
    can render against it today.
    """
    run_dir = outputs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, str] = {}
    for stage in STAGE_NAMES:
        dest = run_dir / f"{stage}.png"
        shutil.copy(image_path, dest)
        result[stage] = str(dest)

    result["plate_text"] = "ABC1234"
    return result
