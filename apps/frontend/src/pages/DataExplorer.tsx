import { useEffect, useState } from "react";
import { Trash2, Loader2, AlertCircle } from "lucide-react";
import { DatasetUpload } from "@/components/DatasetUpload";
import { ExcelSheetSelector } from "@/components/ExcelSheetSelector";
import { DatasetOverview } from "@/components/DatasetOverview";
import { ColumnTypeChart } from "@/components/ColumnTypeChart";
import { MissingValuesChart } from "@/components/MissingValuesChart";
import { ColumnProfileTable } from "@/components/ColumnProfileTable";
import { DatasetPreview } from "@/components/DatasetPreview";
import { DataQualityWarnings } from "@/components/DataQualityWarnings";
import {
  uploadDataset,
  selectSheet,
  getDatasetPreview,
  deleteDataset,
} from "@/services/api";
import type { DatasetUploadResponse, PreviewResponse } from "@/types/dataset";

type ExplorerState =
  | { phase: "idle" }
  | { phase: "uploading" }
  | { phase: "sheet_selection"; response: DatasetUploadResponse }
  | { phase: "loading_preview"; response: DatasetUploadResponse }
  | { phase: "ready"; response: DatasetUploadResponse; preview: PreviewResponse }
  | { phase: "error"; message: string };

export function DataExplorer() {
  const [state, setState] = useState<ExplorerState>({ phase: "idle" });
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const handleUploadStart = () => setState({ phase: "uploading" });

  const handleUploadSuccess = async (file: File) => {
    try {
      const response = await uploadDataset(file);
      if (response.status === "NEEDS_SHEET_SELECTION") {
        setState({ phase: "sheet_selection", response });
      } else if (response.status === "PROFILED") {
        setState({ phase: "loading_preview", response });
      } else if (response.status === "FAILED") {
        setState({ phase: "error", message: "Dataset processing failed." });
      }
    } catch (err) {
      setState({
        phase: "error",
        message: err instanceof Error ? err.message : "Upload failed.",
      });
    }
  };

  const handleUploadError = (message: string) => {
    setState({ phase: "error", message });
  };

  const handleSheetSelect = async (sheetName: string) => {
    if (state.phase !== "sheet_selection") return;
    try {
      const response = await selectSheet(state.response.dataset_id, sheetName);
      setState({ phase: "loading_preview", response });
    } catch (err) {
      setState({
        phase: "error",
        message: err instanceof Error ? err.message : "Sheet profiling failed.",
      });
    }
  };

  const handleDelete = async () => {
    if (state.phase !== "ready" && state.phase !== "loading_preview") return;
    const id = state.response.dataset_id;
    setDeleteError(null);
    try {
      await deleteDataset(id);
      setState({ phase: "idle" });
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Failed to delete dataset.");
    }
  };

  // Load preview after profiling
  useEffect(() => {
    if (state.phase !== "loading_preview") return;
    let cancelled = false;
    getDatasetPreview(state.response.dataset_id, 100)
      .then((preview) => {
        if (!cancelled) setState({ phase: "ready", response: state.response, preview });
      })
      .catch(() => {
        if (!cancelled)
          setState({ phase: "error", message: "Failed to load dataset preview." });
      });
    return () => {
      cancelled = true;
    };
  }, [state]);

  if (state.phase === "idle" || state.phase === "uploading" || state.phase === "error") {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-6 py-16 px-4">
        <div className="text-center max-w-md">
          <h1 className="text-2xl font-bold tracking-tight">Data Explorer</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Upload a CSV or Excel file to generate an automatic data profile.
          </p>
        </div>

        {state.phase === "error" && (
          <div
            role="alert"
            className="flex items-start gap-2 rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive max-w-md w-full"
          >
            <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" aria-hidden="true" />
            <span>{state.message}</span>
          </div>
        )}

        <DatasetUpload
          onUploadStart={handleUploadStart}
          onUploadSuccess={(file) => void handleUploadSuccess(file)}
          onUploadError={handleUploadError}
          isUploading={state.phase === "uploading"}
        />
      </div>
    );
  }

  if (state.phase === "sheet_selection") {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-6 py-16 px-4">
        <ExcelSheetSelector
          sheetNames={state.response.sheet_names ?? []}
          onSelect={(name) => void handleSheetSelect(name)}
          isLoading={false}
        />
      </div>
    );
  }

  if (state.phase === "loading_preview") {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 py-16">
        <Loader2 className="h-8 w-8 animate-spin text-primary" aria-hidden="true" />
        <p className="text-sm text-muted-foreground">Loading preview…</p>
      </div>
    );
  }

  // ready
  const { response, preview } = state;
  const profile = response.profile!;

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="container py-8 space-y-8">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <DatasetOverview metrics={profile.dataset} filename={response.original_filename} />
          <div className="flex flex-col items-end gap-2 shrink-0">
            <button
              onClick={() => void handleDelete()}
              aria-label="Delete dataset"
              className="flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs text-muted-foreground hover:text-destructive hover:border-destructive transition-colors"
            >
              <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
              Delete
            </button>
            {deleteError && (
              <div
                role="alert"
                className="flex items-start gap-1.5 rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive max-w-xs"
              >
                <AlertCircle className="h-3.5 w-3.5 mt-0.5 shrink-0" aria-hidden="true" />
                <span>{deleteError}</span>
              </div>
            )}
          </div>
        </div>

        {/* Charts row */}
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-lg border bg-card p-5">
            <ColumnTypeChart metrics={profile.dataset} />
          </div>
          <div className="rounded-lg border bg-card p-5">
            <MissingValuesChart columns={profile.columns} />
          </div>
        </div>

        {/* Quality warnings */}
        {profile.quality_warnings.length > 0 && (
          <div className="rounded-lg border bg-card p-5">
            <DataQualityWarnings warnings={profile.quality_warnings} />
          </div>
        )}

        {/* Column profile table */}
        <div className="rounded-lg border bg-card p-5">
          <ColumnProfileTable columns={profile.columns} />
        </div>

        {/* Preview */}
        <div className="rounded-lg border bg-card p-5">
          <DatasetPreview preview={preview} />
        </div>
      </div>
    </div>
  );
}
