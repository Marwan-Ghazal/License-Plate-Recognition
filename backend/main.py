"""FastAPI app for the license plate recognition demo.

Endpoints:
    GET  /api/health              - liveness check
    POST /api/recognize           - upload an image, run pipeline, return stages
    GET  /api/plates              - list recent recognitions
    GET  /api/plates/{id}         - fetch a single recognition
    GET  /static/<file>           - intermediate stage images

Run dev server:
    uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend import db
from backend.pipeline_stub import run_pipeline_stub

# ----- Paths -----
BACKEND_DIR = Path(__file__).parent
STATIC_DIR = BACKEND_DIR / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
STAGES_DIR = STATIC_DIR / "stages"

for d in (STATIC_DIR, UPLOADS_DIR, STAGES_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ----- App -----
app = FastAPI(title="License Plate Recognition API", version="0.1.0")

# CORS — Vite dev server runs on 5173. Adjust for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # Lovable preview
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def _startup() -> None:
    db.init_db()


# ----- Endpoints -----
@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/recognize")
async def recognize(file: UploadFile = File(...)) -> dict:
    """Accept an image upload, run the pipeline, persist the result, return stage URLs."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Save upload with a unique stem so concurrent requests don't collide
    suffix = Path(file.filename or "upload.jpg").suffix or ".jpg"
    request_id = uuid.uuid4().hex[:12]
    upload_path = UPLOADS_DIR / f"{request_id}{suffix}"

    contents = await file.read()
    upload_path.write_bytes(contents)

    # Run pipeline (currently a stub; swap for real run_pipeline later)
    try:
        result = run_pipeline_stub(upload_path, STAGES_DIR)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}") from e

    if not result.get("recognized_text"):
        raise HTTPException(status_code=422, detail="no_plate_detected")

    # Persist to DB
    plate_id = db.insert_plate(
        image_filename=upload_path.name,
        recognized_text=result["recognized_text"],
        confidence=result.get("confidence"),
        bbox=result.get("bbox"),
    )

    # Convert filesystem paths to URLs the frontend can fetch
    stages = result["stage_paths"]
    response = {
        "id": plate_id,
        "recognized_text": result["recognized_text"],
        "confidence": result.get("confidence"),
        "bbox": list(result["bbox"]) if result.get("bbox") else None,
        "stages": {
            "original_with_bbox": _to_url(stages["original_with_bbox"]),
            "rectified": _to_url(stages["rectified"]),
            "binarized": _to_url(stages["binarized"]),
            "characters": [_to_url(p) for p in stages["characters"]],
        },
        "timestamp": db.get_plate(plate_id)["timestamp"],  # type: ignore[index]
    }
    return response


@app.get("/api/plates")
def list_plates(limit: int = 100, offset: int = 0) -> dict:
    return {"plates": db.list_plates(limit=limit, offset=offset)}


@app.get("/api/plates/{plate_id}")
def get_plate(plate_id: int) -> dict:
    plate = db.get_plate(plate_id)
    if plate is None:
        raise HTTPException(status_code=404, detail="Plate not found")
    return plate


# ----- Helpers -----
def _to_url(path_str: str) -> str:
    """Convert an absolute filesystem path under STATIC_DIR into a /static/... URL."""
    p = Path(path_str).resolve()
    try:
        rel = p.relative_to(STATIC_DIR.resolve())
    except ValueError:
        # Defensive: if a stage file isn't under static/, return its name only
        return f"/static/{p.name}"
    return f"/static/{rel.as_posix()}"
