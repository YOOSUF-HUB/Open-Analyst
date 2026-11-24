import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Column-level profiling
# ---------------------------------------------------------------------------


class NumericStats(BaseModel):
    mean: float | None
    median: float | None
    std: float | None
    min: float | None
    max: float | None
    q1: float | None
    q3: float | None


class TopValue(BaseModel):
    value: str | None
    count: int


class ColumnProfile(BaseModel):
    name: str
    logical_type: str  # numeric | categorical | text | boolean | datetime
    row_count: int
    non_null_count: int
    missing_count: int
    missing_percentage: float
    unique_count: int
    unique_percentage: float
    # Optional by type
    numeric_stats: NumericStats | None = None
    top_values: list[TopValue] | None = None
    # Datetime range
    min_date: str | None = None
    max_date: str | None = None
    valid_datetime_count: int | None = None
    # Boolean
    true_count: int | None = None
    false_count: int | None = None


# ---------------------------------------------------------------------------
# Dataset-level metrics
# ---------------------------------------------------------------------------


class DatasetMetrics(BaseModel):
    name: str
    file_type: str
    row_count: int
    column_count: int
    total_missing: int
    missing_percentage: float
    duplicate_rows: int
    duplicate_percentage: float
    numeric_columns: int
    categorical_columns: int
    text_columns: int
    boolean_columns: int
    datetime_columns: int


class QualityWarning(BaseModel):
    type: str
    column: str | None
    message: str
    severity: str  # info | warning | error


class ProfileSummary(BaseModel):
    dataset: DatasetMetrics
    columns: list[ColumnProfile]
    quality_warnings: list[QualityWarning]


# ---------------------------------------------------------------------------
# API request / response schemas
# ---------------------------------------------------------------------------


class DatasetUploadResponse(BaseModel):
    dataset_id: uuid.UUID
    original_filename: str
    file_type: str
    file_size: int
    status: str
    sheet_names: list[str] | None = None
    profile: ProfileSummary | None = None
    created_at: datetime


class DatasetMetadataResponse(BaseModel):
    dataset_id: uuid.UUID
    original_filename: str
    file_type: str
    file_size: int
    status: str
    selected_sheet: str | None = None
    sheet_names: list[str] | None = None
    row_count: int | None = None
    column_count: int | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class SheetSelectionRequest(BaseModel):
    sheet_name: str = Field(min_length=1)


class PreviewResponse(BaseModel):
    dataset_id: uuid.UUID
    columns: list[str]
    rows: list[dict[str, Any]]
    total_rows: int
    preview_rows: int


class DeleteResponse(BaseModel):
    message: str
    dataset_id: uuid.UUID
