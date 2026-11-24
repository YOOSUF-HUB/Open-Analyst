import io
import logging

import pandas as pd

logger = logging.getLogger(__name__)

MAX_SHEET_NAME_LENGTH = 255


def get_sheet_names(data: bytes) -> list[str]:
    """Return worksheet names from an XLSX workbook."""
    try:
        xl = pd.ExcelFile(io.BytesIO(data), engine="openpyxl")
        return list(xl.sheet_names)
    except Exception as exc:
        raise ValueError(f"Could not open workbook: {exc}") from exc


def read_excel(
    data: bytes,
    sheet_name: str,
    max_rows: int,
    max_columns: int,
) -> pd.DataFrame:
    """
    Parse a single XLSX worksheet into a DataFrame.

    Raises ValueError for structural problems. Does NOT evaluate macros or formulas.
    Uses cached (data_only=True) cell values via openpyxl.
    """
    try:
        df = pd.read_excel(
            io.BytesIO(data),
            sheet_name=sheet_name,
            engine="openpyxl",
        )
    except ValueError as exc:
        raise ValueError(f"Worksheet '{sheet_name}' not found in workbook.") from exc
    except Exception as exc:
        raise ValueError(f"Could not read worksheet '{sheet_name}': {exc}") from exc

    # Deduplicate column names
    seen: dict[str, int] = {}
    new_cols = []
    for col in df.columns:
        col_str = str(col)
        if col_str in seen:
            seen[col_str] += 1
            new_cols.append(f"{col_str}.{seen[col_str]}")
        else:
            seen[col_str] = 0
            new_cols.append(col_str)
    df.columns = pd.Index(new_cols)

    # Drop completely empty rows
    df = df.dropna(how="all")

    if df.empty and len(df.columns) == 0:
        raise ValueError(f"Worksheet '{sheet_name}' is empty.")

    if len(df.columns) > max_columns:
        raise ValueError(
            f"Worksheet has {len(df.columns)} columns, exceeding the limit of {max_columns}."
        )

    if len(df) > max_rows:
        raise ValueError(f"Worksheet has {len(df)} rows, exceeding the limit of {max_rows}.")

    return df


def validate_sheet_name(sheet_name: str, available_sheets: list[str]) -> None:
    if not sheet_name:
        raise ValueError("Sheet name must not be empty.")
    if len(sheet_name) > MAX_SHEET_NAME_LENGTH:
        raise ValueError("Sheet name is too long.")
    if sheet_name not in available_sheets:
        raise ValueError(
            f"Sheet '{sheet_name}' not found. Available: {', '.join(available_sheets)}."
        )
