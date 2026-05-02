import {
  ApiError,
  HealthResponse,
  PlateRecord,
  PlatesListResponse,
  RecognizeResponse,
} from "@/types/api";

const RAW_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() || "";
// In dev, prefer relative paths so the Vite proxy handles /api and /static.
// If a base URL is provided explicitly, use it (e.g. production).
const BASE = RAW_BASE.replace(/\/$/, "");

function url(path: string): string {
  if (!BASE) return path;
  return `${BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

/** Resolve a backend-served asset path (e.g. "/static/...") to a usable URL. */
export function resolveAsset(p: string): string {
  if (!p) return p;
  if (/^https?:\/\//i.test(p)) return p;
  return url(p);
}

async function parseError(res: Response): Promise<ApiError> {
  let detail: string | undefined;
  try {
    const data = await res.json();
    detail = typeof data?.detail === "string" ? data.detail : JSON.stringify(data?.detail ?? data);
  } catch {
    detail = await res.text().catch(() => undefined);
  }
  const kind = res.status >= 500 ? "server" : "client";
  return new ApiError(kind, detail || `Request failed (${res.status})`, res.status, detail);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(url(path), init);
  } catch (e) {
    throw new ApiError("network", "Could not reach the backend.");
  }
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as T;
}

export const api = {
  async health(): Promise<HealthResponse> {
    return request<HealthResponse>("/api/health");
  },

  async recognize(file: File): Promise<RecognizeResponse> {
    const fd = new FormData();
    fd.append("file", file);
    return request<RecognizeResponse>("/api/recognize", {
      method: "POST",
      body: fd,
    });
  },

  async listPlates(limit = 100, offset = 0): Promise<PlatesListResponse> {
    return request<PlatesListResponse>(`/api/plates?limit=${limit}&offset=${offset}`);
  },

  async getPlate(id: number): Promise<PlateRecord> {
    return request<PlateRecord>(`/api/plates/${id}`);
  },
};
