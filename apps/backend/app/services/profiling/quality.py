"""
Deterministic data quality warning rules.

No AI/LLM-generated text. All messages are templated.
"""

import pandas as pd

from app.schemas.dataset import QualityWarning

MISSING_WARNING_THRESHOLD = 0.05  # 5% missing triggers a warning
MISSING_ERROR_THRESHOLD = 0.50  # 50% missing triggers an error
HIGH_CARDINALITY_THRESHOLD = 0.90  # 90% unique values
HIGH_CARDINALITY_MIN_ROWS = 50  # Only flag if at least 50 rows


def generate_warnings(
    df: pd.DataFrame,
    column_types: dict[str, str],
    dup_rows: int,
) -> list[QualityWarning]:
    warnings: list[QualityWarning] = []
    total_rows = len(df)

    # Dataset-level: duplicate rows (count pre-computed by the caller)
    dup_count = dup_rows
    if dup_count > 0:
        warnings.append(
            QualityWarning(
                type="duplicate_rows",
                column=None,
                message=f"This dataset contains {dup_count} duplicate row{'s' if dup_count != 1 else ''}.",
                severity="warning",
            )
        )

    for col in df.columns:
        series = df[col]
        missing_count = int(series.isna().sum())
        missing_pct = missing_count / total_rows if total_rows > 0 else 0.0
        unique_count = series.nunique(dropna=True)

        # Missing value warnings
        if missing_count > 0:
            pct_display = round(missing_pct * 100, 1)
            if missing_pct >= MISSING_ERROR_THRESHOLD:
                warnings.append(
                    QualityWarning(
                        type="high_missing",
                        column=col,
                        message=f"{col} contains {pct_display}% missing values.",
                        severity="error",
                    )
                )
            elif missing_pct >= MISSING_WARNING_THRESHOLD:
                warnings.append(
                    QualityWarning(
                        type="missing_values",
                        column=col,
                        message=f"{col} contains {missing_count} missing value{'s' if missing_count != 1 else ''} ({pct_display}%).",
                        severity="warning",
                    )
                )

        # Empty column
        if missing_count == total_rows:
            warnings.append(
                QualityWarning(
                    type="empty_column",
                    column=col,
                    message=f"{col} contains only missing values.",
                    severity="error",
                )
            )
            continue

        # Constant column (single unique value, non-null)
        non_null = series.dropna()
        if len(non_null) > 0 and unique_count == 1:
            warnings.append(
                QualityWarning(
                    type="constant_column",
                    column=col,
                    message=f"{col} has only one unique value.",
                    severity="info",
                )
            )

        # High-cardinality categorical
        if (
            column_types.get(col) == "categorical"
            and total_rows >= HIGH_CARDINALITY_MIN_ROWS
            and unique_count / total_rows >= HIGH_CARDINALITY_THRESHOLD
        ):
            warnings.append(
                QualityWarning(
                    type="high_cardinality",
                    column=col,
                    message=f"{col} appears to be a high-cardinality column ({unique_count} unique values).",
                    severity="info",
                )
            )

    return warnings
