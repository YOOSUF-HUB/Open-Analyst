import json

import pandas as pd
import pytest

from app.services.profiling.profiler import build_preview, profile_dataframe


def _make_df(**cols):
    return pd.DataFrame(cols)


def test_basic_dataset_metrics():
    df = _make_df(age=[25, 30, None], city=["A", "B", "A"])
    summary = profile_dataframe(df, "test.csv", "csv")
    assert summary.dataset.row_count == 3
    assert summary.dataset.column_count == 2
    assert summary.dataset.total_missing == 1


def test_numeric_stats_correctness():
    df = _make_df(val=[1.0, 2.0, 3.0, 4.0, 5.0])
    summary = profile_dataframe(df, "t.csv", "csv")
    col = next(c for c in summary.columns if c.name == "val")
    assert col.logical_type == "numeric"
    assert col.numeric_stats is not None
    assert col.numeric_stats.mean == pytest.approx(3.0)
    assert col.numeric_stats.min == pytest.approx(1.0)
    assert col.numeric_stats.max == pytest.approx(5.0)


def test_categorical_top_values():
    df = _make_df(color=["red", "red", "blue", "green"])
    summary = profile_dataframe(df, "t.csv", "csv")
    col = summary.columns[0]
    assert col.logical_type == "categorical"
    assert col.top_values is not None
    assert col.top_values[0].value == "red"
    assert col.top_values[0].count == 2


def test_boolean_profiling():
    df = _make_df(active=[True, False, True, True])
    summary = profile_dataframe(df, "t.csv", "csv")
    col = summary.columns[0]
    assert col.logical_type == "boolean"
    assert col.true_count == 3
    assert col.false_count == 1


def test_datetime_profiling():
    df = _make_df(ts=pd.to_datetime(["2024-01-01", "2024-06-15", "2024-12-31"]))
    summary = profile_dataframe(df, "t.csv", "csv")
    col = summary.columns[0]
    assert col.logical_type == "datetime"
    assert col.min_date is not None
    assert col.max_date is not None
    assert col.valid_datetime_count == 3


def test_missing_value_calculation():
    df = _make_df(x=[1, None, None, 4])
    summary = profile_dataframe(df, "t.csv", "csv")
    col = summary.columns[0]
    assert col.missing_count == 2
    assert col.missing_percentage == pytest.approx(50.0)


def test_duplicate_rows():
    df = _make_df(a=[1, 1, 2], b=["x", "x", "y"])
    summary = profile_dataframe(df, "t.csv", "csv")
    assert summary.dataset.duplicate_rows == 1


def test_constant_column_warning():
    df = _make_df(const=["same"] * 10)
    summary = profile_dataframe(df, "t.csv", "csv")
    types = [w.type for w in summary.quality_warnings]
    assert "constant_column" in types


def test_no_nan_in_json_output():
    df = _make_df(val=[float("nan"), 1.0, 2.0])
    summary = profile_dataframe(df, "t.csv", "csv")
    # Serializing must not raise and must not contain NaN
    raw = json.dumps(summary.model_dump())
    assert "NaN" not in raw
    assert "Infinity" not in raw


def test_empty_column():
    df = _make_df(empty=[None, None, None], real=[1, 2, 3])
    summary = profile_dataframe(df, "t.csv", "csv")
    empty_col = next(c for c in summary.columns if c.name == "empty")
    assert empty_col.missing_count == 3
    warnings = [w.type for w in summary.quality_warnings]
    assert "empty_column" in warnings


def test_build_preview_limit():
    df = pd.DataFrame({"a": range(200)})
    rows = build_preview(df, 50)
    assert len(rows) == 50


def test_build_preview_json_safe():
    df = _make_df(val=[1, float("nan"), 3])
    rows = build_preview(df, 10)
    assert rows[1]["val"] is None


def test_empty_dataframe_raises():
    with pytest.raises(ValueError):
        profile_dataframe(pd.DataFrame(), "empty.csv", "csv")
