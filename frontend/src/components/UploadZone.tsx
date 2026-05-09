import { useCallback, useEffect, useRef, useState } from "react";
import { Upload, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const MAX_BYTES = 10 * 1024 * 1024;

interface Props {
  onSubmit: (file: File) => void;
  loading: boolean;
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export default function UploadZone({ onSubmit, loading }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [drag, setDrag] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!file) {
      setPreview(null);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const handleFile = useCallback((f: File) => {
    setError(null);
    if (!f.type.startsWith("image/")) {
      setError("File must be an image (JPEG or PNG).");
      return;
    }
    if (f.size > MAX_BYTES) {
      setError("File is larger than 10 MB.");
      return;
    }
    setFile(f);
  }, []);

  function clear() {
    setFile(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDrag(false);
    const f = e.dataTransfer.files?.[0];
    if (f) handleFile(f);
  }

  return (
    <div className="w-full">
      <div
        onClick={() => !file && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={onDrop}
        className={cn(
          "relative w-full rounded-xl border-2 border-dashed transition-colors",
          "flex flex-col items-center justify-center text-center p-6",
          file ? "min-h-[220px]" : "min-h-[280px] cursor-pointer",
          drag
            ? "border-primary bg-primary/5"
            : "border-border bg-card hover:border-foreground/30"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
          }}
        />

        {!file ? (
          <>
            <Upload className="h-8 w-8 text-muted-foreground mb-3" strokeWidth={1.5} />
            <p className="text-base font-medium">Drop a vehicle photo here, or click to browse</p>
            <p className="mt-1 font-mono text-xs text-muted-foreground">JPEG or PNG · max 10MB</p>
          </>
        ) : (
          <div className="flex flex-col items-center gap-4 w-full">
            {preview && (
              <img
                src={preview}
                alt={file.name}
                className="max-h-[200px] max-w-full rounded-md border border-border object-contain"
              />
            )}
            <div className="flex flex-col items-center">
              <p className="text-sm font-medium break-all max-w-md">{file.name}</p>
              <p className="font-mono text-xs text-muted-foreground mt-0.5">{formatSize(file.size)}</p>
            </div>
            <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
              <Button
                onClick={(e) => {
                  e.stopPropagation();
                  if (file) onSubmit(file);
                }}
                disabled={loading}
                className="gap-2 min-w-[160px]"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" /> Recognizing…
                  </>
                ) : (
                  "Recognize"
                )}
              </Button>
              <Button
                variant="ghost"
                onClick={(e) => {
                  e.stopPropagation();
                  clear();
                }}
                disabled={loading}
                className="gap-2"
              >
                <X className="h-4 w-4" /> Clear
              </Button>
            </div>
          </div>
        )}
      </div>

      {error && (
        <p className="mt-3 text-sm text-destructive font-mono">{error}</p>
      )}
    </div>
  );
}
