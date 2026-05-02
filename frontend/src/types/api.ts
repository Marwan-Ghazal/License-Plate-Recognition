export type BBox = [number, number, number, number];

export interface HealthResponse {
  status: string;
}

export interface RecognizeStages {
  original_with_bbox: string;
  rectified: string;
  binarized: string;
  characters: string[];
}

export interface RecognizeResponse {
  id: number;
  recognized_text: string;
  confidence: number;
  bbox: BBox | null;
  stages: RecognizeStages;
  timestamp: string;
}

export interface PlateRecord {
  id: number;
  image_filename: string;
  recognized_text: string | null;
  confidence: number | null;
  bbox: BBox | null;
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
