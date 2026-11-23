import type {
  DatasetMetadataResponse,
  DatasetUploadResponse,
  PreviewResponse,
  ProfileSummary,
} from "@/types/dataset";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
}

export type ConnectionStatus = "loading" | "connected" | "disconnected";

class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      // ignore parse failure
    }
    throw new ApiError(response.status, detail);
  }
  return response.json() as Promise<T>;
}

async function get<T>(path: string): Promise<T> {
  return request<T>(path);
}

export async function fetchHealth(): Promise<HealthResponse> {
  return get<HealthResponse>("/api/v1/health");
}

export async function uploadDataset(file: File): Promise<DatasetUploadResponse> {
  const form = new FormData();
  form.append("file", file);
  return request<DatasetUploadResponse>("/api/v1/datasets/upload", {
    method: "POST",
    body: form,
  });
}

export async function selectSheet(
  datasetId: string,
  sheetName: string,
): Promise<DatasetUploadResponse> {
  return request<DatasetUploadResponse>(`/api/v1/datasets/${datasetId}/profile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sheet_name: sheetName }),
  });
}

export async function getDatasetMetadata(datasetId: string): Promise<DatasetMetadataResponse> {
  return get<DatasetMetadataResponse>(`/api/v1/datasets/${datasetId}`);
}

export async function getDatasetProfile(datasetId: string): Promise<ProfileSummary> {
  return get<ProfileSummary>(`/api/v1/datasets/${datasetId}/profile`);
}

export async function getDatasetPreview(
  datasetId: string,
  limit = 100,
): Promise<PreviewResponse> {
  return get<PreviewResponse>(`/api/v1/datasets/${datasetId}/preview?limit=${limit}`);
}

export async function deleteDataset(datasetId: string): Promise<void> {
  await request(`/api/v1/datasets/${datasetId}`, { method: "DELETE" });
}

export { ApiError };
