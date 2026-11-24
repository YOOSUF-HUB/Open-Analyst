export type DatasetStatus =
  | "UPLOADED"
  | "NEEDS_SHEET_SELECTION"
  | "PROFILED"
  | "FAILED";

export interface NumericStats {
  mean: number | null;
  median: number | null;
  std: number | null;
  min: number | null;
  max: number | null;
  q1: number | null;
  q3: number | null;
}

export interface TopValue {
  value: string | null;
  count: number;
}

export interface ColumnProfile {
  name: string;
  logical_type: "numeric" | "categorical" | "text" | "boolean" | "datetime";
  row_count: number;
  non_null_count: number;
  missing_count: number;
  missing_percentage: number;
  unique_count: number;
  unique_percentage: number;
  numeric_stats?: NumericStats | null;
  top_values?: TopValue[] | null;
  min_date?: string | null;
  max_date?: string | null;
  valid_datetime_count?: number | null;
  true_count?: number | null;
  false_count?: number | null;
}

export interface DatasetMetrics {
  name: string;
  file_type: string;
  row_count: number;
  column_count: number;
  total_missing: number;
  missing_percentage: number;
  duplicate_rows: number;
  duplicate_percentage: number;
  numeric_columns: number;
  categorical_columns: number;
  text_columns: number;
  boolean_columns: number;
  datetime_columns: number;
}

export interface QualityWarning {
  type: string;
  column: string | null;
  message: string;
  severity: "info" | "warning" | "error";
}

export interface ProfileSummary {
  dataset: DatasetMetrics;
  columns: ColumnProfile[];
  quality_warnings: QualityWarning[];
}

export interface DatasetUploadResponse {
  dataset_id: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  status: DatasetStatus;
  sheet_names?: string[] | null;
  profile?: ProfileSummary | null;
  created_at: string;
}

export interface DatasetMetadataResponse {
  dataset_id: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  status: DatasetStatus;
  selected_sheet?: string | null;
  sheet_names?: string[] | null;
  row_count?: number | null;
  column_count?: number | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PreviewResponse {
  dataset_id: string;
  columns: string[];
  rows: Record<string, unknown>[];
  total_rows: number;
  preview_rows: number;
}
