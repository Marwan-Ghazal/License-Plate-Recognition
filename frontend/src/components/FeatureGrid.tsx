import { Boxes, Layers, ShieldAlert, Database } from "lucide-react";

const features = [
  {
    icon: Boxes,
    title: "Pure Classical CV",
    body: "No deep learning, no black boxes — every stage is inspectable and documented.",
  },
  {
    icon: Layers,
    title: "Stage-by-Stage Visualization",
    body:
      "See the original, the localized plate, the rectified crop, the binary image, and each segmented character.",
  },
  {
    icon: ShieldAlert,
    title: "Robust Edge-Case Handling",
    body: "Graceful failure with clear errors when no plate is detected or the image is unreadable.",
  },
  {
    icon: Database,
    title: "Persistent History",
    body: "Every recognition is stored in SQLite with timestamp, confidence, and bounding box.",
  },
];

export default function FeatureGrid() {
  return (
    <section className="container py-16 md:py-24 border-t border-border">
      <div className="mb-12 max-w-2xl">
        <p className="font-mono text-xs uppercase tracking-wider text-primary mb-3">Key features</p>
        <h2 className="text-3xl md:text-4xl font-semibold tracking-tight">Designed to be inspected</h2>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {features.map((f) => {
          const Icon = f.icon;
          return (
            <div key={f.title} className="ps-card flex flex-col">
              <Icon className="h-5 w-5 text-primary mb-4" strokeWidth={2} />
              <h3 className="text-base font-medium mb-1.5">{f.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{f.body}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
