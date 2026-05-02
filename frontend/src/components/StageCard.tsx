import { ReactNode } from "react";

interface Props {
  index: number;
  title: string;
  caption: string;
  children: ReactNode;
  accentBorder?: boolean;
}

export default function StageCard({ index, title, caption, children, accentBorder }: Props) {
  return (
    <div
      className={
        "relative rounded-xl bg-card p-6 md:p-8 animate-fade-in " +
        (accentBorder ? "border-2 border-primary" : "border border-border")
      }
    >
      <span className="ps-stage-badge absolute top-4 left-4">
        {String(index).padStart(2, "0")}
      </span>
      <div className="pt-6">
        <h3 className="text-lg font-medium tracking-tight">{title}</h3>
        <p className="mt-1 text-sm text-muted-foreground">{caption}</p>
        <div className="mt-5">{children}</div>
      </div>
    </div>
  );
}
