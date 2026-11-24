"""
Main profiling entry point.

profile_dataframe() is the only public function; it is independent of FastAPI
and can be called directly in tests or scripts.
"""

import logging
from typing import Any

import pandas as pd

from app.schemas.dataset import DatasetMetrics, ProfileSummary
from app.services.profiling.column_profiler import profile_column
from app.services.profiling.quality import generate_warnings
from app.services.profiling.type_detector import detect_all_types

logger = logging.getLogger(__name__)


def profile_dataframe(df: pd.DataFrame, name: str, file_type: str) -> ProfileSummary:
    """
    Compute a full ProfileSummary for the given DataFrame.

    Safe to call without a database connection.
    """
    if df.empty and len(df.columns) == 0:
        raise ValueError("Cannot profile an empty DataFrame with no columns.")

    column_types = detect_all_types(df)

    # Dataset-level metrics
    total_rows = len(df)
    total_cols = len(df.columns)
    total_missing = int(df.isna().sum().sum())
    missing_pct = (
        round(total_missing / (total_rows * total_cols) * 100, 2)
        if total_rows * total_cols > 0
        else 0.0
    )
    dup_rows = int(df.duplicated().sum())
    dup_pct = round(dup_rows / total_rows * 100, 2) if total_rows > 0 else 0.0

    type_counts: dict[str, int] = {
        "numeric": 0,
        "categorical": 0,
        "text": 0,
        "boolean": 0,
        "datetime": 0,
    }
    for t in column_types.values():
        if t in type_counts:
            type_counts[t] += 1

    dataset_metrics = DatasetMetrics(
        name=name,
        file_type=file_type,
        row_count=total_rows,
        column_count=total_cols,
        total_missing=total_missing,
        missing_percentage=missing_pct,
        duplicate_rows=dup_rows,
        duplicate_percentage=dup_pct,
        numeric_columns=type_counts["numeric"],
        categorical_columns=type_counts["categorical"],
        text_columns=type_counts["text"],
        boolean_columns=type_counts["boolean"],
        datetime_columns=type_counts["datetime"],
    )

    # Column-level profiles
    column_profiles = []
    for col in df.columns:
        try:
            cp = profile_column(df[col], column_types[col])
            column_profiles.append(cp)
        except Exception:
            logger.exception("Failed to profile column %r", col)

    # Quality warnings — pass the already-computed dup_rows to avoid a second full scan
    warnings = generate_warnings(df, column_types, dup_rows)

    return ProfileSummary(
        dataset=dataset_metrics,
        columns=column_profiles,
        quality_warnings=warnings,
    )


def build_preview(df: pd.DataFrame, limit: int) -> list[dict[str, Any]]:
    """Return up to `limit` rows as JSON-safe dicts."""
    preview_df = df.head(limit)
    rows = []
    for _, row in preview_df.iterrows():
        safe_row: dict[str, Any] = {}
        for col, val in row.items():
            safe_row[str(col)] = _json_safe(val)
        rows.append(safe_row)
    return rows


def _json_safe(val: Any) -> Any:
    import math

    import numpy as np

    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        f = float(val)
        return None if (math.isnan(f) or math.isinf(f)) else f
    if isinstance(val, (np.bool_,)):
        return bool(val)
    if isinstance(val, pd.Timestamp):
        return val.isoformat()
    if hasattr(val, "item"):  # generic numpy scalar
        return val.item()
    if pd.isna(val):
        return None
    return val
