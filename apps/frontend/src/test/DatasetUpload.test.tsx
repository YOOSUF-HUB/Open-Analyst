import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { DatasetUpload } from "@/components/DatasetUpload";

function makeFile(name: string, size: number, type = "text/csv"): File {
  const content = "a".repeat(size);
  return new File([content], name, { type });
}

describe("DatasetUpload", () => {
  const onUploadStart = vi.fn();
  const onUploadSuccess = vi.fn();
  const onUploadError = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  function renderComponent(isUploading = false) {
    return render(
      <DatasetUpload
        onUploadStart={onUploadStart}
        onUploadSuccess={onUploadSuccess}
        onUploadError={onUploadError}
        isUploading={isUploading}
      />,
    );
  }

  it("renders the upload zone", () => {
    renderComponent();
    expect(screen.getByRole("button")).toBeInTheDocument();
    expect(screen.getByText(/drag & drop/i)).toBeInTheDocument();
  });

  it("shows accepted formats", () => {
    renderComponent();
    expect(screen.getByText(/CSV, XLSX/i)).toBeInTheDocument();
  });

  it("shows uploading state", () => {
    renderComponent(true);
    expect(screen.getByText(/uploading/i)).toBeInTheDocument();
  });

  it("validates unsupported file extension", () => {
    renderComponent();
    const input = screen.getByRole("button").querySelector("input[type=file]")!;
    const file = makeFile("data.txt", 100);
    fireEvent.change(input, { target: { files: [file] } });
    expect(onUploadError).toHaveBeenCalledWith(expect.stringMatching(/unsupported/i));
    expect(onUploadStart).not.toHaveBeenCalled();
  });

  it("accepts valid CSV file", () => {
    renderComponent();
    const input = screen.getByRole("button").querySelector("input[type=file]")!;
    const file = makeFile("data.csv", 100);
    fireEvent.change(input, { target: { files: [file] } });
    expect(onUploadStart).toHaveBeenCalled();
    expect(onUploadSuccess).toHaveBeenCalledWith(file);
  });

  it("accepts valid XLSX file", () => {
    renderComponent();
    const input = screen.getByRole("button").querySelector("input[type=file]")!;
    const file = makeFile("book.xlsx", 100, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
    fireEvent.change(input, { target: { files: [file] } });
    expect(onUploadStart).toHaveBeenCalled();
    expect(onUploadSuccess).toHaveBeenCalledWith(file);
  });

  it("validates empty file", () => {
    renderComponent();
    const input = screen.getByRole("button").querySelector("input[type=file]")!;
    const file = makeFile("empty.csv", 0);
    fireEvent.change(input, { target: { files: [file] } });
    expect(onUploadError).toHaveBeenCalledWith(expect.stringMatching(/empty/i));
  });

  it("shows validation error message", () => {
    renderComponent();
    const input = screen.getByRole("button").querySelector("input[type=file]")!;
    const file = makeFile("data.pdf", 100, "application/pdf");
    fireEvent.change(input, { target: { files: [file] } });
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
