# Backend — License Plate Recognition

FastAPI + SQLite backend for the LPR demo. Currently runs on a pipeline stub
that returns fake data, so the frontend can be built and tested before the
pipeline integration is finished.

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run dev server

From the **project root** (one level above `backend/`):

```bash
uvicorn backend.main:app --reload --port 8000
```

Then:
- Health check: <http://localhost:8000/api/health>
- Interactive docs: <http://localhost:8000/docs>
- Static files: <http://localhost:8000/static/...>

## Endpoints

| Method | Path                  | Description                             |
| ------ | --------------------- | --------------------------------------- |
| GET    | `/api/health`         | Liveness check                          |
| POST   | `/api/recognize`      | Upload image, run pipeline, return stages |
| GET    | `/api/plates`         | List recent recognitions (newest first) |
| GET    | `/api/plates/{id}`    | Fetch a single recognition              |

### `POST /api/recognize`

**Request:** `multipart/form-data` with field `file` containing the image.

**Response 200:**

```json
{
  "id": 42,
  "recognized_text": "ABC1234",
  "confidence": 0.87,
  "bbox": [120, 340, 180, 60],
  "stages": {
    "original_with_bbox": "/static/stages/abc123_original.jpg",
    "rectified":          "/static/stages/abc123_rectified.jpg",
    "binarized":          "/static/stages/abc123_binarized.jpg",
    "characters": [
      "/static/stages/abc123_char_0.jpg",
      "/static/stages/abc123_char_1.jpg"
    ]
  },
  "timestamp": "2026-05-02T14:30:00+00:00"
}
```

**Response 422:** `{ "detail": "no_plate_detected" }`
**Response 400:** `{ "detail": "File must be an image" }`

## Database

SQLite at `backend/plates.db` (auto-created on first run). Override with
`LPR_DB_PATH` env var. Schema:

```sql
CREATE TABLE plates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    image_filename  TEXT NOT NULL,
    recognized_text TEXT,
    confidence      REAL,
    bbox            TEXT,         -- JSON [x, y, w, h]
    timestamp       TEXT NOT NULL -- ISO 8601 UTC
);
```

## Swapping the stub for the real pipeline

When Person 1 has `pipeline.run_pipeline` ready, edit `backend/main.py`:

```python
# Remove:
from backend.pipeline_stub import run_pipeline_stub

# Add:
import cv2
from pipeline import run_pipeline
```

Then in the `recognize` handler, replace:

```python
result = run_pipeline_stub(upload_path, STAGES_DIR)
```

with:

```python
image_bgr = cv2.imread(str(upload_path))
result = run_pipeline(image_bgr, save_stages_to=STAGES_DIR)
```

The response shape is identical, so the frontend needs no changes.

## CORS

Configured for `localhost:5173` (Vite dev), `127.0.0.1:5173`, and
`localhost:3000` (Lovable preview). Add your deployed frontend origin to
`allow_origins` in `main.py` before deploying.

## Project layout

```
backend/
├── __init__.py
├── main.py              FastAPI app, routes, CORS, static mount
├── db.py                SQLite layer (init, insert, get, list)
├── pipeline_stub.py     Temporary fake pipeline, swap for real one later
├── requirements.txt
├── plates.db            (auto-created at runtime)
└── static/
    ├── uploads/         (saved user uploads)
    └── stages/          (intermediate pipeline images)
```
