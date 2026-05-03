export interface HealthResponse {
  status: string;
}

export interface RecognizeStages {
  grayscale: string;
  bilateral: string;
  edges: string;
  morphology: string;
  contours: string;
  warped: string;
  binary: string;
  segmented: string;
}

export interface RecognizeResponse {
  run_id: string;
  plate_text: string;
  stages: RecognizeStages;
  timestamp: string;
}

export interface PlateRecord {
  id: number;
  run_id: string;
  plate_text: string | null;
  image_filename: string;
  timestamp: string;
}

export interface PlatesListResponse {
  plates: PlateRecord[];
}

export type ApiErrorKind = "network" | "client" | "server";

export class ApiError extends Error {
  kind: ApiErrorKind;
  status?: number;
  detail?: string;
  constructor(kind: ApiErrorKind, message: string, status?: number, detail?: string) {
    super(message);
    this.kind = kind;
    this.status = status;
    this.detail = detail;
  }
}
