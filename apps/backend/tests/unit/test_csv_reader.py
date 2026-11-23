import pytest

from app.services.ingestion.csv_reader import read_csv

MAX_ROWS = 1000
MAX_COLS = 50


def _csv(text: str) -> bytes:
    return text.encode("utf-8")


def test_valid_csv():
    data = _csv("a,b,c\n1,2,3\n4,5,6\n")
    df = read_csv(data, MAX_ROWS, MAX_COLS)
    assert list(df.columns) == ["a", "b", "c"]
    assert len(df) == 2


def test_utf8_bom():
    data = b"\xef\xbb\xbfa,b\n1,2\n"
    df = read_csv(data, MAX_ROWS, MAX_COLS)
    assert "a" in df.columns


def test_semicolon_delimiter():
    data = _csv("x;y\n10;20\n30;40\n")
    df = read_csv(data, MAX_ROWS, MAX_COLS)
    assert list(df.columns) == ["x", "y"]


def test_tab_delimiter():
    data = _csv("col1\tcol2\n1\t2\n")
    df = read_csv(data, MAX_ROWS, MAX_COLS)
    assert len(df.columns) == 2


def test_missing_values():
    data = _csv("a,b\n1,\n,3\n")
    df = read_csv(data, MAX_ROWS, MAX_COLS)
    assert df["b"].isna().sum() == 1
    assert df["a"].isna().sum() == 1


def test_empty_csv_raises():
    with pytest.raises(ValueError, match="empty"):
        read_csv(b"", MAX_ROWS, MAX_COLS)


def test_whitespace_only_raises():
    with pytest.raises(ValueError):
        read_csv(b"   \n\n", MAX_ROWS, MAX_COLS)


def test_duplicate_column_names():
    data = _csv("a,a,b\n1,2,3\n")
    df = read_csv(data, MAX_ROWS, MAX_COLS)
    assert "a" in df.columns
    assert "a.1" in df.columns


def test_empty_rows_dropped():
    data = _csv("a,b\n1,2\n,,\n3,4\n")
    df = read_csv(data, MAX_ROWS, MAX_COLS)
    assert len(df) == 2


def test_row_limit_exceeded():
    rows = "a,b\n" + "1,2\n" * 101
    with pytest.raises(ValueError, match="rows"):
        read_csv(_csv(rows), 100, MAX_COLS)


def test_column_limit_exceeded():
    header = ",".join(f"col{i}" for i in range(10))
    row = ",".join(str(i) for i in range(10))
    with pytest.raises(ValueError, match="columns"):
        read_csv(_csv(f"{header}\n{row}\n"), MAX_ROWS, 5)


def test_invalid_extension_check_is_separate():
    # csv_reader does not check extension; it reads content
    data = _csv("a,b\n1,2\n")
    df = read_csv(data, MAX_ROWS, MAX_COLS)
    assert len(df) == 1
