import { AlertCircle } from "lucide-react";
import { ApiError } from "@/types/api";

interface Props {
  error: ApiError | Error;
}

function describe(error: ApiError | Error): { title: string; message: string } {
  if (error instanceof ApiError) {
    if (error.kind === "network") {
      return {
        title: "Network error",
        message: "Could not reach the backend. Make sure the API is running on port 8000.",
      };
    }
    if (error.status === 422 && (error.detail === "no_plate_detected" || /no_plate/i.test(error.detail || ""))) {
      return {
        title: "No plate found",
        message:
          "The pipeline could not locate a license plate in this image. Try a clearer photo with the plate visible and well-lit.",
      };
    }
    if (error.status === 400) {
      return { title: "Invalid file", message: error.detail || "The file could not be processed." };
    }
    if (error.kind === "server") {
      return {
        title: "Pipeline error",
        message: (error.detail || error.message) + " — try another image.",
      };
    }
    return { title: "Request failed", message: error.detail || error.message };
  }
  return { title: "Something went wrong", message: error.message };
}

export default function ErrorAlert({ error }: Props) {
  const { title, message } = describe(error);
  return (
    <div
      role="alert"
      className="ps-card border-destructive/40 flex gap-3 items-start animate-fade-in"
    >
      <AlertCircle className="h-5 w-5 text-destructive shrink-0 mt-0.5" strokeWidth={2} />
      <div className="min-w-0">
        <p className="font-medium">{title}</p>
        <p className="mt-1 text-sm text-muted-foreground break-words">{message}</p>
      </div>
    </div>
  );
}
