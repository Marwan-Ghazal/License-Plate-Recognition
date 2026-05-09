import { useCallback, useRef, useState } from "react";
import { toast } from "sonner";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import UploadZone from "@/components/UploadZone";
import StageCard from "@/components/StageCard";
import RecognizedTextCard from "@/components/RecognizedTextCard";
import ErrorAlert from "@/components/ErrorAlert";
import { Skeleton } from "@/components/ui/skeleton";
import { api, resolveAsset } from "@/lib/api";
import { ApiError, RecognizeResponse } from "@/types/api";

const STAGE_CARDS = [
  { key: "grayscale",  title: "Grayscale",        caption: "Weighted RGB→gray conversion (0.114B + 0.587G + 0.299R), resized to 600px width.", wide: true },
  { key: "bilateral",  title: "Bilateral filter",  caption: "Edge-preserving bilateral smooth (d=5, σ_color=15, σ_space=15).", wide: true },
  { key: "edges",      title: "Edge detection",    caption: "BlackHat morph + Sobel-x gradient, normalized to 0–255.", wide: true },
  { key: "morphology", title: "Morphology",         caption: "Otsu threshold on edge map → morphological closing (15×5 kernel) to form plate regions.", wide: true },
  { key: "contours",   title: "Contours",           caption: "External contours extracted, filtered by aspect ratio 2.0–8.0 and minimum size 30×10px.", wide: true },
  { key: "warped",     title: "Warped",             caption: "Best candidate's min-area-rect → 4-point perspective transform → 300×75px.", wide: false },
  { key: "binary",     title: "Binary",             caption: "Otsu threshold + auto-invert (characters white, background black).", wide: false },
  { key: "segmented",  title: "Segmented + OCR",    caption: "Connected-component segmentation → Tesseract OCR (PSM 7, A-Z0-9 whitelist, 3× upscale).", wide: false },
] as const;


export default function DemoPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RecognizeResponse | null>(null);
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [duration, setDuration] = useState<number | undefined>();
  const uploadRef = useRef<HTMLDivElement>(null);

  const submit = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    setResult(null);
    const t0 = performance.now();
    try {
      const r = await api.recognize(file);
      setResult(r);
      setDuration(Math.round(performance.now() - t0));
    } catch (e) {
      const err = e as ApiError | Error;
      setError(err);
      if (err instanceof ApiError && err.kind === "network") {
        toast.error("Could not reach the backend. Make sure the API is running on port 8000.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  function reset() {
    setResult(null);
    setError(null);
    uploadRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 container py-10 md:py-16">
        <div className="max-w-3xl mx-auto" ref={uploadRef}>
          <div className="mb-8">
            <p className="font-mono text-xs uppercase tracking-wider text-primary mb-2">Live demo</p>
            <h1 className="text-3xl md:text-4xl font-semibold tracking-tight">Run the pipeline</h1>
            <p className="mt-2 text-muted-foreground">
              Upload a vehicle photo. We'll show you each stage of the recognition.
            </p>
          </div>

          <UploadZone onSubmit={submit} loading={loading} />

          {error && (
            <div className="mt-6">
              <ErrorAlert error={error} />
            </div>
          )}
        </div>

        {/* Loading skeletons */}
        {loading && !result && (
          <div className="max-w-3xl mx-auto mt-10 space-y-6">
            {[0, 1, 2].map((i) => (
              <div key={i} className="ps-card">
                <Skeleton className="h-4 w-12 mb-4" />
                <Skeleton className="h-5 w-40 mb-2" />
                <Skeleton className="h-4 w-72 mb-5" />
                <Skeleton className="h-48 w-full" />
              </div>
            ))}
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="max-w-3xl mx-auto mt-12 space-y-6">
            {STAGE_CARDS.map((s, i) =>
              result.stages[s.key] ? (
                <StageCard
                  key={s.key}
                  index={i + 1}
                  title={s.title}
                  caption={s.caption}
                >
                  <img
                    src={resolveAsset(result.stages[s.key])}
                    alt={s.title}
                    className={s.wide ? "mx-auto max-w-full md:max-w-[800px] rounded-md border border-border" : "mx-auto max-w-full md:max-w-[400px] rounded-md border border-border"}
                  />
                </StageCard>
              ) : null
            )}

            <RecognizedTextCard
              text={result.plate_text}
              timestamp={result.timestamp}
              durationMs={duration}
              onTryAnother={reset}
            />
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
