import io
import logging

import pandas as pd

logger = logging.getLogger(__name__)

# Delimiters to try in order when sniffing
_CANDIDATE_DELIMITERS = [",", ";", "\t", "|"]


def _sniff_delimiter(sample: str) -> str:
    """Return the most likely delimiter based on occurrence counts."""
    counts = {d: sample.count(d) for d in _CANDIDATE_DELIMITERS}
    best = max(counts, key=lambda d: counts[d])
    return best if counts[best] > 0 else ","


def read_csv(
    data: bytes,
    max_rows: int,
    max_columns: int,
) -> pd.DataFrame:
    """
    Parse CSV bytes into a DataFrame.

    Raises ValueError for structural problems (empty, too many rows/columns,
    malformed content). The caller is responsible for file-level validation.
    """
    # Handle UTF-8 BOM
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]

    # Try UTF-8 first, fall back to latin-1
    for encoding in ("utf-8", "latin-1"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Could not decode file. Only UTF-8 and Latin-1 encodings are supported.")

    if not text.strip():
        raise ValueError("CSV file is empty or contains only whitespace.")

    # Sniff delimiter from first 4096 chars
    delimiter = _sniff_delimiter(text[:4096])

    try:
        df = pd.read_csv(
            io.StringIO(text),
            sep=delimiter,
            low_memory=False,
            on_bad_lines="warn",
        )
    except Exception as exc:
        raise ValueError(f"Could not parse CSV: {exc}") from exc

    if df.empty and len(df.columns) == 0:
        raise ValueError("CSV file has no data.")

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

    if len(df) == 0:
        raise ValueError("CSV file contains no non-empty rows.")

    if len(df.columns) > max_columns:
        raise ValueError(
            f"Dataset has {len(df.columns)} columns, exceeding the limit of {max_columns}."
        )

    if len(df) > max_rows:
        raise ValueError(f"Dataset has {len(df)} rows, exceeding the limit of {max_rows}.")

    return df
