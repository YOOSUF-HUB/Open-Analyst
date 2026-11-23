import { describe, it, expect, vi, beforeEach } from "vitest";
import { fetchHealth, uploadDataset, selectSheet, deleteDataset, ApiError } from "@/services/api";

const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

function mockResponse(body: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: () => Promise.resolve(body),
  } as Response;
}

beforeEach(() => {
  mockFetch.mockReset();
});

describe("fetchHealth", () => {
  it("returns health data on success", async () => {
    const data = { status: "ok", version: "0.1.0", timestamp: "2024-01-01T00:00:00Z" };
    mockFetch.mockResolvedValueOnce(mockResponse(data));
    const result = await fetchHealth();
    expect(result.status).toBe("ok");
    expect(result.version).toBe("0.1.0");
  });

  it("throws ApiError on non-ok response", async () => {
    mockFetch.mockResolvedValueOnce(mockResponse({ detail: "Not found" }, false, 404));
    await expect(fetchHealth()).rejects.toBeInstanceOf(ApiError);
  });
});

describe("uploadDataset", () => {
  it("sends POST with FormData", async () => {
    const data = {
      dataset_id: "abc-123",
      original_filename: "test.csv",
      file_type: "csv",
      file_size: 100,
      status: "PROFILED",
      created_at: "2024-01-01T00:00:00Z",
    };
    mockFetch.mockResolvedValueOnce(mockResponse(data, true, 201));
    const file = new File(["a,b\n1,2"], "test.csv", { type: "text/csv" });
    const result = await uploadDataset(file);
    expect(result.dataset_id).toBe("abc-123");
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/datasets/upload"),
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("throws ApiError on 413", async () => {
    mockFetch.mockResolvedValueOnce(mockResponse({ detail: "File too large" }, false, 413));
    const file = new File(["x"], "big.csv");
    await expect(uploadDataset(file)).rejects.toBeInstanceOf(ApiError);
  });
});

describe("selectSheet", () => {
  it("sends POST with sheet_name", async () => {
    const data = {
      dataset_id: "abc-123",
      original_filename: "book.xlsx",
      file_type: "xlsx",
      file_size: 100,
      status: "PROFILED",
      created_at: "2024-01-01T00:00:00Z",
    };
    mockFetch.mockResolvedValueOnce(mockResponse(data));
    await selectSheet("abc-123", "Sheet1");
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/datasets/abc-123/profile"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ sheet_name: "Sheet1" }),
      }),
    );
  });
});

describe("deleteDataset", () => {
  it("sends DELETE request", async () => {
    mockFetch.mockResolvedValueOnce(mockResponse({ message: "Deleted.", dataset_id: "abc-123" }));
    await deleteDataset("abc-123");
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/datasets/abc-123"),
      expect.objectContaining({ method: "DELETE" }),
    );
  });
});

describe("ApiError", () => {
  it("carries the HTTP status", async () => {
    mockFetch.mockResolvedValueOnce(mockResponse({ detail: "Not found" }, false, 404));
    try {
      await fetchHealth();
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      expect((e as ApiError).status).toBe(404);
    }
  });
});
