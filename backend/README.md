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
- Health check: <http://localhost:8000/health>
- Interactive docs: <http://localhost:8000/docs>
- Stage images: <http://localhost:8000/stages/{run_id}/{stage_name}>

## Endpoints

| Method | Path                          | Description                             |
| ------ | ----------------------------- | --------------------------------------- |
| GET    | `/health`                     | Liveness check                          |
| POST   | `/recognize`                  | Upload image, run pipeline, return stages |
| GET    | `/plates`                     | List recent recognitions (newest first) |
| GET    | `/plates/{id}`                | Fetch a single recognition              |
| GET    | `/stages/{run_id}/{stage}`    | Serve a pipeline debug image (PNG)      |

### `POST /recognize`

**Request:** `multipart/form-data` with field `file` containing the image.

**Response 200:**

```json
{
  "run_id": "abc123def456",
  "plate_text": "ABC1234",
  "stages": {
    "grayscale":  "/stages/abc123def456/grayscale",
    "bilateral":  "/stages/abc123def456/bilateral",
    "edges":      "/stages/abc123def456/edges",
    "morphology": "/stages/abc123def456/morphology",
    "contours":   "/stages/abc123def456/contours",
    "warped":     "/stages/abc123def456/warped",
    "binary":     "/stages/abc123def456/binary",
    "segmented":  "/stages/abc123def456/segmented"
  },
  "timestamp": "2026-05-03T12:00:00+00:00"
}
```

**Response 422:** `{ "detail": "no_plate_detected" }`
**Response 400:** `{ "detail": "File must be an image" }`

### `GET /stages/{run_id}/{stage_name}`

Serves the PNG debug image for a given pipeline run and stage. Valid stage
names: `grayscale`, `bilateral`, `edges`, `morphology`, `contours`, `warped`,
`binary`, `segmented`. Returns 404 for unknown stages or missing images, 400
for path-traversal attempts.

## Database

SQLite at `backend/plates.db` (auto-created on first run). Override with
`LPR_DB_PATH` env var. Schema:

```sql
CREATE TABLE plates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          TEXT NOT NULL UNIQUE,
    plate_text      TEXT,
    image_filename  TEXT NOT NULL,
    timestamp       TEXT NOT NULL -- ISO 8601 UTC
);
CREATE INDEX idx_plates_timestamp ON plates(timestamp);
CREATE INDEX idx_plates_run_id    ON plates(run_id);
```

## Swapping the stub for the real pipeline

When Person 1 has `pipeline.pipeline.run_pipeline` ready, edit `backend/main.py`:

```python
# Remove:
from backend.pipeline_stub import run_pipeline_stub

# Add:
import cv2
from pipeline.pipeline import run_pipeline
```

Then in the `recognize` handler, replace:

```python
result = run_pipeline_stub(upload_path, run_id, OUTPUTS_DIR)
```

with:

```python
bgr = cv2.imread(str(upload_path))
result = run_pipeline(bgr, run_id=run_id, outputs_dir=OUTPUTS_DIR)
```

The real `run_pipeline` returns the same flat-dict shape (`{stage_name: path_str, "plate_text": str}`),
so the rest of the handler is unchanged.

## CORS

Configured for `localhost:5173`, `127.0.0.1:5173`, `localhost:8080`,
`127.0.0.1:8080` (Vite dev), and `localhost:3000` (Lovable preview). Add your
deployed frontend origin to `allow_origins` in `main.py` before deploying.

## Project layout

```
backend/
├── __init__.py
├── main.py              FastAPI app, routes, CORS
├── db.py                SQLite layer (init, insert, get, list)
├── pipeline_stub.py     Temporary fake pipeline, swap for real one later
├── plates.db            (auto-created at runtime)
└── static/
    └── uploads/         (saved user uploads)

data/                    (project root, not inside backend/)
└── outputs/
    └── <run_id>/        (pipeline debug images per run)
        ├── grayscale.png
        ├── bilateral.png
        ├── edges.png
        ├── morphology.png
        ├── contours.png
        ├── warped.png
        ├── binary.png
        └── segmented.png
```
