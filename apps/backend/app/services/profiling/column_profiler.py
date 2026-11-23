"""
Per-column profiling calculations.

All results are JSON-safe (no NaN, Infinity, numpy scalar types).
"""

import logging
import math
from typing import Any

import pandas as pd

from app.schemas.dataset import ColumnProfile, NumericStats, TopValue

logger = logging.getLogger(__name__)


def _safe_float(value: Any) -> float | None:
    """Convert a value to a JSON-safe float, returning None for NaN/Inf."""
    if value is None:
        return None
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _safe_str(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return str(value)


def profile_column(series: pd.Series, logical_type: str) -> ColumnProfile:
    row_count = len(series)
    missing_count = int(series.isna().sum())
    non_null_count = row_count - missing_count
    missing_pct = round(missing_count / row_count * 100, 2) if row_count > 0 else 0.0
    unique_count = int(series.nunique(dropna=True))
    unique_pct = round(unique_count / row_count * 100, 2) if row_count > 0 else 0.0

    base = dict(
        name=series.name if series.name is not None else "",
        logical_type=logical_type,
        row_count=row_count,
        non_null_count=non_null_count,
        missing_count=missing_count,
        missing_percentage=missing_pct,
        unique_count=unique_count,
        unique_percentage=unique_pct,
    )

    if logical_type == "numeric":
        return _profile_numeric(series, base)
    if logical_type in ("categorical", "text"):
        return _profile_categorical(series, base)
    if logical_type == "datetime":
        return _profile_datetime(series, base)
    if logical_type == "boolean":
        return _profile_boolean(series, base)
    return ColumnProfile(**base)


def _profile_numeric(series: pd.Series, base: dict) -> ColumnProfile:
    non_null = pd.to_numeric(series, errors="coerce").dropna()
    if len(non_null) == 0:
        stats = NumericStats(mean=None, median=None, std=None, min=None, max=None, q1=None, q3=None)
    else:
        stats = NumericStats(
            mean=_safe_float(non_null.mean()),
            median=_safe_float(non_null.median()),
            std=_safe_float(non_null.std()),
            min=_safe_float(non_null.min()),
            max=_safe_float(non_null.max()),
            q1=_safe_float(non_null.quantile(0.25)),
            q3=_safe_float(non_null.quantile(0.75)),
        )
    return ColumnProfile(**base, numeric_stats=stats)


def _profile_categorical(series: pd.Series, base: dict) -> ColumnProfile:
    value_counts = series.value_counts(dropna=True).head(5)
    top_values = [
        TopValue(value=_safe_str(val), count=int(cnt)) for val, cnt in value_counts.items()
    ]
    return ColumnProfile(**base, top_values=top_values)


def _profile_datetime(series: pd.Series, base: dict) -> ColumnProfile:
    parsed = pd.to_datetime(series, errors="coerce")
    valid = parsed.dropna()
    valid_count = int(len(valid))
    min_date = valid.min().isoformat() if valid_count > 0 else None
    max_date = valid.max().isoformat() if valid_count > 0 else None
    return ColumnProfile(
        **base,
        min_date=min_date,
        max_date=max_date,
        valid_datetime_count=valid_count,
    )


def _profile_boolean(series: pd.Series, base: dict) -> ColumnProfile:
    non_null = series.dropna()
    # Coerce to bool if stored as object
    if series.dtype == object:
        bool_map = {"true": True, "false": False, "1": True, "0": False, "yes": True, "no": False}
        non_null = non_null.map(lambda v: bool_map.get(str(v).lower())).dropna()
    true_count = int((non_null == True).sum())  # noqa: E712
    false_count = int((non_null == False).sum())  # noqa: E712
    return ColumnProfile(**base, true_count=true_count, false_count=false_count)
