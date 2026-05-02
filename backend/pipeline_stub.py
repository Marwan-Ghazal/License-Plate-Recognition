"""Temporary stand-in for the real pipeline.

Person 1 will replace this with a real import from ``pipeline.run_pipeline``
once integration is done. Keep this file's signature identical to the real one
so swapping is a one-line change in main.py.

Real signature (from the team plan):

    def run_pipeline(image_bgr: np.ndarray,
                     save_stages_to: Path | None = None) -> dict:
        return {
            'recognized_text': str,
            'confidence': float,
            'bbox': tuple[int, int, int, int] | None,
            'stage_paths': dict[str, str | list[str]],
        }

This stub takes a saved image path instead of a numpy array so we don't need
OpenCV in the backend skeleton. We'll switch to the array signature when the
real pipeline lands.
"""

from __future__ import annotations

import shutil
from pathlib import Path


def run_pipeline_stub(image_path: Path, save_stages_to: Path) -> dict:
    """Fake recognition that copies the input image to each stage slot.

    Returns the same shape as the real pipeline so the frontend can render
    against it today.
    """
    save_stages_to.mkdir(parents=True, exist_ok=True)
    stem = image_path.stem

    # Copy the input into each "stage" so the UI has something to show.
    stage_files = {
        "original_with_bbox": save_stages_to / f"{stem}_original.jpg",
        "rectified": save_stages_to / f"{stem}_rectified.jpg",
        "binarized": save_stages_to / f"{stem}_binarized.jpg",
    }
    for dest in stage_files.values():
        shutil.copy(image_path, dest)

    char_files = []
    for i in range(7):  # fake 7-character plate
        char_path = save_stages_to / f"{stem}_char_{i}.jpg"
        shutil.copy(image_path, char_path)
        char_files.append(char_path)

    return {
        "recognized_text": "ABC1234",
        "confidence": 0.87,
        "bbox": (120, 340, 180, 60),
        "stage_paths": {
            "original_with_bbox": str(stage_files["original_with_bbox"]),
            "rectified": str(stage_files["rectified"]),
            "binarized": str(stage_files["binarized"]),
            "characters": [str(p) for p in char_files],
        },
    }
