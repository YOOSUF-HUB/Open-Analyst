import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { DataExplorer } from "@/pages/DataExplorer";

// Mock ECharts-based chart components — jsdom has no canvas support
vi.mock("@/components/ColumnTypeChart", () => ({
  ColumnTypeChart: () => <div data-testid="mock-column-type-chart" />,
}));
vi.mock("@/components/MissingValuesChart", () => ({
  MissingValuesChart: () => <div data-testid="mock-missing-values-chart" />,
}));

// Mock the API module
vi.mock("@/services/api", () => ({
  uploadDataset: vi.fn(),
  selectSheet: vi.fn(),
  getDatasetPreview: vi.fn(),
  deleteDataset: vi.fn(),
}));

import { uploadDataset, getDatasetPreview, deleteDataset } from "@/services/api";

const mockUpload = uploadDataset as ReturnType<typeof vi.fn>;
const mockPreview = getDatasetPreview as ReturnType<typeof vi.fn>;
const mockDelete = deleteDataset as ReturnType<typeof vi.fn>;

const fakeUploadResponse = {
  dataset_id: "abc-123",
  original_filename: "test.csv",
  file_type: "csv",
  file_size: 100,
  status: "PROFILED" as const,
  created_at: "2024-01-01T00:00:00Z",
  profile: {
    dataset: {
      name: "test.csv",
      file_type: "csv",
      row_count: 2,
      column_count: 2,
      total_missing: 0,
      missing_percentage: 0,
      duplicate_rows: 0,
      duplicate_percentage: 0,
      numeric_columns: 2,
      categorical_columns: 0,
      text_columns: 0,
      boolean_columns: 0,
      datetime_columns: 0,
    },
    columns: [],
    quality_warnings: [],
  },
};

const fakePreviewResponse = {
  dataset_id: "abc-123",
  columns: ["a", "b"],
  rows: [{ a: 1, b: 2 }],
  total_rows: 1,
  preview_rows: 1,
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("DataExplorer — delete error handling", () => {
  it("shows delete error and preserves state when deletion fails", async () => {
    mockUpload.mockResolvedValueOnce(fakeUploadResponse);
    mockPreview.mockResolvedValueOnce(fakePreviewResponse);
    mockDelete.mockRejectedValueOnce(new Error("Server error"));

    render(<DataExplorer />);

    // Trigger upload
    const uploadZone = screen.getByRole("button", { name: /upload dataset/i });
    const input = uploadZone.querySelector("input[type=file]")!;
    const file = new File(["a,b\n1,2"], "test.csv", { type: "text/csv" });
    fireEvent.change(input, { target: { files: [file] } });

    // Wait for the ready state (profile + preview loaded)
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /delete dataset/i })).toBeInTheDocument();
    });

    // Click delete
    fireEvent.click(screen.getByRole("button", { name: /delete dataset/i }));

    // Error message should appear
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
      expect(screen.getByRole("alert")).toHaveTextContent("Server error");
    });

    // Dashboard should still be visible (not reset to idle)
    expect(screen.getByRole("button", { name: /delete dataset/i })).toBeInTheDocument();
  });

  it("transitions to idle on successful deletion", async () => {
    mockUpload.mockResolvedValueOnce(fakeUploadResponse);
    mockPreview.mockResolvedValueOnce(fakePreviewResponse);
    mockDelete.mockResolvedValueOnce(undefined);

    render(<DataExplorer />);

    const uploadZone = screen.getByRole("button", { name: /upload dataset/i });
    const input = uploadZone.querySelector("input[type=file]")!;
    const file = new File(["a,b\n1,2"], "test.csv", { type: "text/csv" });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /delete dataset/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /delete dataset/i }));

    await waitFor(() => {
      expect(screen.getByText(/drag & drop/i)).toBeInTheDocument();
    });
  });
});
