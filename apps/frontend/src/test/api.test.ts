import { describe, it, expect, vi, beforeEach } from "vitest";
import { fetchHealth } from "@/services/api";

describe("fetchHealth", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("returns health data on success", async () => {
    const mockData = { status: "ok", version: "0.1.0", timestamp: "2024-01-01T00:00:00Z" };
    globalThis.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    } as Response);

    const result = await fetchHealth();
    expect(result).toEqual(mockData);
  });

  it("throws on non-ok response", async () => {
    globalThis.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      status: 503,
      statusText: "Service Unavailable",
    } as Response);

    await expect(fetchHealth()).rejects.toThrow("HTTP 503");
  });
});
