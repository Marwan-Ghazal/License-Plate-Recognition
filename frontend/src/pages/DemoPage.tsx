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

const PRESETS = [
  { label: "Clear plate", path: "/samples/clear.jpg" },
  { label: "Angled plate", path: "/samples/angled.jpg" },
  { label: "Low light", path: "/samples/lowlight.jpg" },
  { label: "Multi-vehicle", path: "/samples/multi.jpg" },
];

export default function DemoPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RecognizeResponse | null>(null);
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [duration, setDuration] = useState<number | undefined>();
  const [presetFile, setPresetFile] = useState<File | null>(null);
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

  async function loadPreset(path: string, label: string) {
    try {
      const res = await fetch(path);
      if (!res.ok) throw new Error("Sample not found");
      const blob = await res.blob();
      const file = new File([blob], `${label}.jpg`, { type: blob.type || "image/jpeg" });
      setPresetFile(file);
      submit(file);
    } catch {
      toast.error(`Sample "${label}" not available. Place it in public${path}.`);
    }
  }

  function reset() {
    setResult(null);
    setError(null);
    setPresetFile(null);
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

          <UploadZone onSubmit={submit} loading={loading} externalFile={presetFile} />

          {/* Presets */}
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="font-mono text-xs text-muted-foreground self-center mr-1">
              Try a sample:
            </span>
            {PRESETS.map((p) => (
              <button
                key={p.label}
                onClick={() => loadPreset(p.path, p.label)}
                disabled={loading}
                className="text-xs font-mono px-3 py-1.5 rounded-md border border-border hover:border-primary hover:text-primary transition-colors disabled:opacity-50"
              >
                {p.label}
              </button>
            ))}
          </div>

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
            <StageCard
              index={1}
              title="Detected plate"
              caption="Localized via edge detection, morphological closing, and contour filtering by aspect ratio."
            >
              <img
                src={resolveAsset(result.stages.original_with_bbox)}
                alt="Detected plate"
                className="mx-auto max-w-full md:max-w-[800px] rounded-md border border-border"
              />
            </StageCard>

            <StageCard
              index={2}
              title="Rectified"
              caption="Perspective-corrected to a clean axis-aligned rectangle."
            >
              <img
                src={resolveAsset(result.stages.rectified)}
                alt="Rectified plate"
                className="mx-auto max-w-full md:max-w-[400px] rounded-md border border-border"
              />
            </StageCard>

            <StageCard
              index={3}
              title="Binarized"
              caption="Otsu or adaptive threshold; auto-inverted so characters are white on black."
            >
              <img
                src={resolveAsset(result.stages.binarized)}
                alt="Binarized plate"
                className="mx-auto max-w-full md:max-w-[400px] rounded-md border border-border"
              />
            </StageCard>

            <StageCard
              index={4}
              title="Segmented characters"
              caption="Split via connected components or vertical projection."
            >
              <div className="flex flex-wrap gap-2 justify-center">
                {result.stages.characters.map((c, i) => (
                  <img
                    key={i}
                    src={resolveAsset(c)}
                    alt={`Character ${i + 1}`}
                    className="h-[72px] w-auto rounded-md border border-border bg-background"
                  />
                ))}
              </div>
            </StageCard>

            <RecognizedTextCard
              text={result.recognized_text}
              confidence={result.confidence}
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
