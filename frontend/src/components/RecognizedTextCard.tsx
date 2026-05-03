import { Copy, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import StageCard from "./StageCard";
import { toast } from "sonner";

interface Props {
  text: string;
  timestamp: string;
  durationMs?: number;
  onTryAnother: () => void;
}

function formatTimestamp(iso: string) {
  try {
    const d = new Date(iso);
    const pad = (n: number) => String(n).padStart(2, "0");
    return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} ${pad(
      d.getUTCHours()
    )}:${pad(d.getUTCMinutes())} UTC`;
  } catch {
    return iso;
  }
}

export default function RecognizedTextCard({ text, timestamp, durationMs, onTryAnother }: Props) {
  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Copied", { description: text });
    } catch {
      toast.error("Could not copy to clipboard");
    }
  }

  return (
    <StageCard
      index={9}
      title="Recognized text"
      caption="Final OCR output from Tesseract's legacy engine."
      accentBorder
    >
      <div className="py-8 md:py-10 flex items-center justify-center">
        <p className="font-mono text-4xl md:text-5xl font-medium tracking-[0.08em] text-center break-all">
          {text || "—"}
        </p>
      </div>

      <div className="font-mono text-xs text-muted-foreground text-center">
        {typeof durationMs === "number" && `Read in ${durationMs}ms · `}
        {formatTimestamp(timestamp)}
      </div>

      <div className="mt-6 flex flex-col sm:flex-row gap-2 justify-center">
        <Button variant="default" onClick={copy} className="gap-2">
          <Copy className="h-4 w-4" /> Copy text
        </Button>
        <Button variant="outline" onClick={onTryAnother} className="gap-2">
          <RotateCcw className="h-4 w-4" /> Try another
        </Button>
      </div>
    </StageCard>
  );
}
