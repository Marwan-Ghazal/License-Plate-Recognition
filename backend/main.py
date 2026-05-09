"""FastAPI app for the license plate recognition demo.

Endpoints:
    GET  /health                  - liveness check
    POST /recognize               - upload an image, run pipeline, return stages
    GET  /plates                  - list recent recognitions
    GET  /plates/{id}             - fetch a single recognition
    GET  /stages/{run_id}/{stage} - serve a pipeline debug image

Run dev server:
    uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend import db
import cv2
from pipeline.pipeline import run_pipeline

# ----- Paths -----
BACKEND_DIR = Path(__file__).parent
PROJECT_ROOT = BACKEND_DIR.parent
STATIC_DIR = BACKEND_DIR / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
OUTPUTS_DIR = PROJECT_ROOT / "data" / "outputs"

for d in (STATIC_DIR, UPLOADS_DIR, OUTPUTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ----- Stage image route config -----
ALLOWED_STAGES = {
    "grayscale", "bilateral", "edges", "morphology",
    "contours", "warped", "binary", "segmented",
}

# ----- App -----
app = FastAPI(title="License Plate Recognition API", version="0.1.0")

# CORS — Vite dev server runs on 8080 (5173 is default). Adjust for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",  # Lovable preview
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    db.init_db()


# ----- Endpoints -----
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/recognize")
async def recognize(file: UploadFile = File(...)) -> dict:
    """Accept an image upload, run the pipeline, persist the result, return stage URLs."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Save upload with a unique stem so concurrent requests don't collide
    suffix = Path(file.filename or "upload.jpg").suffix or ".jpg"
    run_id = uuid.uuid4().hex[:12]
    upload_path = UPLOADS_DIR / f"{run_id}{suffix}"

    contents = await file.read()
    upload_path.write_bytes(contents)

    # Run pipeline
    try:
        bgr = cv2.imread(str(upload_path))
        if bgr is None:
            raise ValueError("Could not read uploaded image")
        result = run_pipeline(bgr, run_id, OUTPUTS_DIR)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}") from e

    # Persist to DB (even if plate_text is empty — stages may still be useful)
    plate_id = db.insert_plate(
        run_id=run_id,
        plate_text=result["plate_text"],
        image_filename=upload_path.name,
    )

    # Build stage URLs from the flat dict returned by the pipeline
    stages: dict[str, str] = {}
    for name in ALLOWED_STAGES:
        if name in result:
            stages[name] = f"/stages/{run_id}/{name}"

    response = {
        "run_id": run_id,
        "plate_text": result["plate_text"],
        "stages": stages,
        "timestamp": db.get_plate(plate_id)["timestamp"],  # type: ignore[index]
    }
    return response


@app.get("/plates")
def list_plates(limit: int = 100, offset: int = 0) -> dict:
    return {"plates": db.list_plates(limit=limit, offset=offset)}


@app.get("/plates/{plate_id}")
def get_plate(plate_id: int) -> dict:
    plate = db.get_plate(plate_id)
    if plate is None:
        raise HTTPException(status_code=404, detail="Plate not found")
    return plate


@app.get("/stages/{run_id}/{stage_name}")
def get_stage(run_id: str, stage_name: str):
    if stage_name not in ALLOWED_STAGES:
        raise HTTPException(status_code=404, detail="Unknown stage")
    # Reject path traversal
    if "/" in run_id or ".." in run_id:
        raise HTTPException(status_code=400, detail="Invalid run_id")
    path = OUTPUTS_DIR / run_id / f"{stage_name}.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Stage image not found")
    return FileResponse(path, media_type="image/png")
