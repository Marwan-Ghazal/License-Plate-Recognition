import {
  Filter,
  Activity,
  Crop,
  Frame,
  Binary,
  Type as TypeIcon,
} from "lucide-react";

const steps = [
  {
    icon: Filter,
    title: "Preprocess",
    body:
      "Convert to grayscale and apply a bilateral filter to smooth noise while preserving plate edges.",
  },
  {
    icon: Activity,
    title: "Edge Detection",
    body: "Canny or Sobel highlights character boundaries against the plate background.",
  },
  {
    icon: Crop,
    title: "Localize",
    body:
      "Morphological closing with a wide horizontal kernel merges characters into one blob; contour filtering by aspect ratio and area keeps only plate-shaped candidates.",
  },
  {
    icon: Frame,
    title: "Rectify",
    body: "Four-point perspective transform warps the candidate to a clean, axis-aligned rectangle.",
  },
  {
    icon: Binary,
    title: "Binarize",
    body:
      "Otsu or adaptive threshold separates characters from background; auto-inverts so characters are white on black.",
  },
  {
    icon: TypeIcon,
    title: "Recognize",
    body:
      "Characters split via connected components or vertical projection, then read by Tesseract's legacy OCR engine.",
  },
];

export default function PipelineTimeline() {
  return (
    <section id="pipeline" className="container py-16 md:py-24">
      <div className="mb-12 max-w-2xl">
        <p className="font-mono text-xs uppercase tracking-wider text-primary mb-3">The Pipeline</p>
        <h2 className="text-3xl md:text-4xl font-semibold tracking-tight">Six deterministic stages</h2>
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
