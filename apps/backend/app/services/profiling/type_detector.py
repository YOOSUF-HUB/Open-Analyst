"""
Column logical type detection.

Logical types: numeric | categorical | text | boolean | datetime

Rules applied in order:
1. bool dtype → boolean
2. datetime64 dtype → datetime
3. numeric dtype → numeric (unless only contains 0/1 → still numeric)
4. object/string dtype:
   a. Try datetime parse; if >80% succeed → datetime
   b. Otherwise check cardinality:
      - unique count <= 50 OR unique% <= 10% → categorical
      - else → text
5. category dtype → categorical
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)

DATETIME_PARSE_THRESHOLD = 0.80  # fraction of non-null values that must parse as datetime
CATEGORICAL_MAX_UNIQUE = 50
CATEGORICAL_MAX_UNIQUE_PCT = 0.10  # 10%


def detect_logical_type(series: pd.Series) -> str:
    """Return the logical type for a single column."""
    dtype = series.dtype

    if pd.api.types.is_bool_dtype(dtype):
        return "boolean"

    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "datetime"

    if pd.api.types.is_numeric_dtype(dtype):
        return "numeric"

    if hasattr(dtype, "name") and dtype.name == "category":
        return "categorical"

    # object dtype — try date parse, then cardinality check
    non_null = series.dropna()
    if len(non_null) == 0:
        return "text"

    # Try datetime coercion on a sample to avoid slow parsing of large text cols
    sample = non_null.head(200)
    try:
        parsed = pd.to_datetime(sample, errors="coerce")
        success_rate = parsed.notna().sum() / len(sample)
        if success_rate >= DATETIME_PARSE_THRESHOLD:
            return "datetime"
    except Exception:
        pass

    unique_count = series.nunique(dropna=True)
    unique_pct = unique_count / len(series) if len(series) > 0 else 0.0

    if unique_count <= CATEGORICAL_MAX_UNIQUE or unique_pct <= CATEGORICAL_MAX_UNIQUE_PCT:
        return "categorical"

    return "text"


def detect_all_types(df: pd.DataFrame) -> dict[str, str]:
    """Return a mapping of column name → logical type for all columns."""
    return {col: detect_logical_type(df[col]) for col in df.columns}
