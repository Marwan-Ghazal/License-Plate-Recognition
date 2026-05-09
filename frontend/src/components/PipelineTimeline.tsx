import {
  Filter,
  Activity,
  Scan,
  Grid3X3,
  BoxSelect,
  Frame,
  Binary,
  Type as TypeIcon,
} from "lucide-react";

const steps = [
  {
    icon: Filter,
    title: "Grayscale",
    body:
      "Weighted RGB→gray conversion (0.114B + 0.587G + 0.299R), resized to 600px width.",
  },
  {
    icon: Filter,
    title: "Bilateral Filter",
    body:
      "Edge-preserving bilateral smooth (d=5, σ_color=15, σ_space=15) removes noise while keeping plate edges sharp.",
  },
  {
    icon: Activity,
    title: "Edge Detection",
    body: "BlackHat morph + Sobel-x gradient highlights horizontal plate boundaries, normalized to 0–255.",
  },
  {
    icon: Scan,
    title: "Morphology",
    body:
      "Otsu threshold on edge map → morphological closing with a 15×5 kernel connects edge fragments into plate-shaped regions.",
  },
  {
    icon: Grid3X3,
    title: "Contours",
    body:
      "External contours extracted, filtered by aspect ratio 2.0–8.0 and minimum size 30×10px. Up to 5 candidates ranked by area.",
  },
  {
    icon: BoxSelect,
    title: "Warp",
    body: "Best candidate's min-area-rect → 4-point perspective transform → 300×75px axis-aligned rectangle.",
  },
  {
    icon: Binary,
    title: "Binarize",
    body:
      "Otsu threshold + auto-invert so characters are white on black background.",
  },
  {
    icon: TypeIcon,
    title: "Segment + OCR",
    body:
      "Connected-component segmentation → Tesseract OCR (PSM 7, A-Z0-9 whitelist, 3× upscale). Candidates tried sequentially; first producing ≥3 chars wins.",
  },
];

export default function PipelineTimeline() {
  return (
    <section id="pipeline" className="container py-16 md:py-24">
      <div className="mb-12 max-w-2xl">
        <p className="font-mono text-xs uppercase tracking-wider text-primary mb-3">The Pipeline</p>
        <h2 className="text-3xl md:text-4xl font-semibold tracking-tight">Eight deterministic stages</h2>
        <p className="mt-3 text-muted-foreground">
          Every stage is inspectable and documented. No neural networks, no black boxes — just classical
          computer vision composed end to end.
        </p>
      </div>

      <ol className="relative border-l border-border ml-3 space-y-8">
        {steps.map((s, i) => {
          const Icon = s.icon;
          return (
            <li key={s.title} className="pl-8 relative">
              <span className="absolute -left-[17px] top-0 flex h-8 w-8 items-center justify-center rounded-full border border-border bg-background">
                <Icon className="h-4 w-4 text-primary" strokeWidth={2} />
              </span>
              <div className="flex items-baseline gap-3">
                <span className="font-mono text-xs font-medium text-primary tracking-wider">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <h3 className="text-lg font-medium">{s.title}</h3>
              </div>
              <p className="mt-1.5 text-muted-foreground max-w-2xl leading-relaxed">{s.body}</p>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
