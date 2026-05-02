# PlateScan — Frontend

A React + Vite + TypeScript frontend for the PlateScan License Plate Recognition demo. Pairs with the FastAPI + OpenCV + Tesseract backend.

## Run

```bash
npm install
cp .env.example .env   # optionally edit VITE_API_BASE_URL
npm run dev
```

The dev server runs on port 8080. In development, `/api/*` and `/static/*` are proxied to `http://localhost:8000` (configured in `vite.config.ts`). Start the backend on port 8000 alongside this app.

## Environment

- `VITE_API_BASE_URL` — only needed in production builds where the frontend is hosted separately from the API. In dev, leave empty to use the Vite proxy.

## Sample images (optional)

The demo's "Try a sample" buttons load images from `/public/samples/`:

- `public/samples/clear.jpg`
- `public/samples/angled.jpg`
- `public/samples/lowlight.jpg`
- `public/samples/multi.jpg`

Add your own to enable the preset buttons.

## Routes

- `/` — landing page (hero, pipeline timeline, features)
- `/demo` — upload + stage-by-stage results
