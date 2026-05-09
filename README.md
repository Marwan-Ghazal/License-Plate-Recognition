# License-Plate-Recognition

License plate detection and OCR — OpenCV pipeline + FastAPI backend + React/Vite frontend.

## Quick start

### 1. Install Tesseract OCR

The recognition stage uses [Tesseract OCR](https://github.com/tesseract-ocr/tesseract).

- **Windows**: download the installer from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) and add it to your `PATH`.
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt install tesseract-ocr`

### 2. Install Python & Node dependencies

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt

cd frontend
npm install
cd ..

npm install
```

### 3. Run both servers

```bash
# Activate the Python venv first (see above for your OS)
npm run dev
```

- Frontend: http://localhost:8080
- Backend:  http://localhost:8000
- API docs: http://localhost:8000/docs

## Project layout

```
├── backend/                  FastAPI app + SQLite
│   ├── main.py               Routes, CORS, image serving
│   ├── db.py                 SQLite schema & queries
│   └── static/uploads/       Saved user uploads
├── pipeline/                 Computer-vision pipeline (OpenCV + Tesseract)
│   ├── pipeline.py           Orchestrator — runs all 8 stages
│   ├── preprocessing.py      Stages 1–2: grayscale, bilateral filter
│   ├── localization.py       Stages 3–4: edge detection, morphology, contours
│   ├── normalization.py      Stages 5–6: perspective warp, binarization
│   ├── recognition.py        Stages 7–8: segmentation, OCR
│   └── utils.py              load_image, save_debug helpers
├── data/
│   ├── samples/              Test vehicle images
│   └── outputs/              Per-run debug images (<run_id>/<stage>.png)
├── frontend/                 React + Vite + Tailwind + shadcn/ui
│   └── src/
│       ├── lib/api.ts        API client (auto-proxied in dev)
│       ├── types/api.ts      TypeScript interfaces
│       └── pages/DemoPage.tsx Upload form + 8-stage gallery
└── requirements.txt          Python deps (fastapi, opencv-python, pytesseract, …)
```

## API endpoints

| Method | Path                          | Description                              |
| ------ | ----------------------------- | ---------------------------------------- |
| GET    | `/health`                     | Liveness check                           |
| POST   | `/recognize`                  | Upload image → run pipeline → return stages + plate text |
| GET    | `/plates`                     | List recent recognitions (newest first)  |
| GET    | `/plates/{id}`                | Fetch a single recognition               |
| GET    | `/stages/{run_id}/{stage}`    | Serve a pipeline debug image (PNG)       |

### `POST /recognize` response

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
  "timestamp": "2026-05-09T20:09:28+00:00"
}
```

## Pipeline stages

| # | Stage        | Module            | Description                                    |
|---|-------------|-------------------|------------------------------------------------|
| 1 | Grayscale   | preprocessing.py  | Weighted RGB→gray conversion                   |
| 2 | Bilateral   | preprocessing.py  | Edge-preserving smooth (bilateral filter)      |
| 3 | Edges       | localization.py   | BlackHat + Sobel-x edge map                    |
| 4 | Morphology  | localization.py   | Morphological closing + contour extraction     |
| 5 | Contours    | localization.py   | Aspect-ratio filtering of plate candidates     |
| 6 | Warped      | normalization.py  | Perspective correction to fixed-size rectangle |
| 7 | Binary      | normalization.py  | Otsu threshold + auto-invert + cleanup         |
| 8 | Segmented   | recognition.py    | Connected-component segmentation + Tesseract OCR |