"""
DuckDB syntax compatibility tests for the Phase 2 query builder.

These tests execute the SQL produced by the query builder against a real
in-memory DuckDB instance to verify that generated SQL is syntactically
valid and semantically correct.

All tests are automatically skipped when DuckDB is not installed.
DuckDB will be added as a dependency in Milestone 4 (Execution Engine);
at that point these tests will activate and run as part of the CI suite.

Usage once DuckDB is installed:
    pip install duckdb>=1.1.0
    pytest tests/unit/test_query_builder_duckdb.py -v
"""

from __future__ import annotations

import pytest

duckdb = pytest.importorskip("duckdb", reason="duckdb not installed (added in M4)")

from app.schemas.analysis import (  # noqa: E402
    AggregateRequest,
    AggregationSpec,
    CorrelateRequest,
    DescribeRequest,
    FilterCondition,
    FilterRequest,
    SortColumn,
    SortRequest,
)
from app.services.analysis.query_builder import (  # noqa: E402
    build_aggregate_query,
    build_correlate_query,
    build_describe_query,
    build_filter_query,
    build_sort_query,
)
from tests.unit.test_query_builder import PROFILE, _make_profile  # noqa: E402

# ---------------------------------------------------------------------------
# DuckDB fixture — fresh in-memory connection with a 'dataset' table
# ---------------------------------------------------------------------------


@pytest.fixture
def conn():
    """Return a DuckDB in-memory connection with a pre-populated `dataset` table."""
    c = duckdb.connect()
    c.execute("""
        CREATE TABLE dataset (
            age     INTEGER,
            salary  DOUBLE,
            city    VARCHAR,
            bio     VARCHAR,
            active  BOOLEAN,
            joined_at TIMESTAMP
        )
    """)
    c.execute("""
        INSERT INTO dataset VALUES
            (25,  50000.0, 'London', 'Software engineer',  true,  '2023-01-15'),
            (30,  75000.0, 'Paris',  'Data analyst',       false, '2022-06-01'),
            (35,  90000.0, 'London', 'Manager',            true,  '2021-03-20'),
            (NULL, NULL,   NULL,     NULL,                 NULL,  NULL)
    """)
    return c


# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------


def test_duckdb_filter_eq(conn):
    req = FilterRequest(conditions=[FilterCondition(column="city", operator="eq", value="London")])
    q = build_filter_query(req, PROFILE)
    rows = conn.execute(q.sql, q.parameters).fetchall()
    assert len(rows) == 2


def test_duckdb_filter_gt(conn):
    req = FilterRequest(conditions=[FilterCondition(column="age", operator="gt", value=25)])
    q = build_filter_query(req, PROFILE)
    rows = conn.execute(q.sql, q.parameters).fetchall()
    assert len(rows) == 2  # age=30 and age=35


def test_duckdb_filter_contains(conn):
    req = FilterRequest(
        conditions=[FilterCondition(column="bio", operator="contains", value="engineer")]
    )
    q = build_filter_query(req, PROFILE)
    rows = conn.execute(q.sql, q.parameters).fetchall()
    assert len(rows) == 1


def test_duckdb_filter_contains_percent_wildcard_not_injected(conn):
    """A % in the value must match literally, not as a SQL wildcard."""
    # Insert a row containing a literal % character
    conn.execute(
        "INSERT INTO dataset VALUES (40, 60000.0, 'NYC', '100% effort', true, '2020-01-01')"
    )
    req = FilterRequest(
        conditions=[FilterCondition(column="bio", operator="contains", value="100%")]
    )
    q = build_filter_query(req, PROFILE)
    rows = conn.execute(q.sql, q.parameters).fetchall()
    # Must match only the row with literal "100%" — not all rows
    assert len(rows) == 1


def test_duckdb_filter_is_null(conn):
    req = FilterRequest(conditions=[FilterCondition(column="age", operator="is_null")])
    q = build_filter_query(req, PROFILE)
    rows = conn.execute(q.sql, q.parameters).fetchall()
    assert len(rows) == 1


def test_duckdb_filter_multiple_conditions(conn):
    req = FilterRequest(
        conditions=[
            FilterCondition(column="city", operator="eq", value="London"),
            FilterCondition(column="age", operator="gt", value=25),
        ]
    )
    q = build_filter_query(req, PROFILE)
    rows = conn.execute(q.sql, q.parameters).fetchall()
    assert len(rows) == 1  # only age=35, city=London


def test_duckdb_filter_limit(conn):
    req = FilterRequest(conditions=[FilterCondition(column="age", operator="is_not_null")])
    q = build_filter_query(req, PROFILE, max_result_rows=2)
    rows = conn.execute(q.sql, q.parameters).fetchall()
    assert len(rows) == 2


# ---------------------------------------------------------------------------
# Sort
# ---------------------------------------------------------------------------


def test_duckdb_sort_asc(conn):
    req = SortRequest(columns=[SortColumn(column="age", direction="asc")])
    q = build_sort_query(req, PROFILE)
    rows = conn.execute(q.sql, q.parameters).fetchall()
    ages = [r[0] for r in rows if r[0] is not None]
    assert ages == sorted(ages)


def test_duckdb_sort_desc(conn):
    req = SortRequest(columns=[SortColumn(column="salary", direction="desc")])
    q = build_sort_query(req, PROFILE)
    rows = conn.execute(q.sql, q.parameters).fetchall()
    salaries = [r[1] for r in rows if r[1] is not None]
    assert salaries == sorted(salaries, reverse=True)


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------


def test_duckdb_aggregate_sum(conn):
    req = AggregateRequest(aggregations=[AggregationSpec(function="SUM", column="salary")])
    q = build_aggregate_query(req, PROFILE)
    rows = conn.execute(q.sql, q.parameters).fetchall()
    assert rows[0][0] == pytest.approx(215000.0)


def test_duckdb_aggregate_count(conn):
    req = AggregateRequest(aggregations=[AggregationSpec(function="COUNT", column="age")])
    q = build_aggregate_query(req, PROFILE)
    rows = conn.execute(q.sql, q.parameters).fetchall()
    assert rows[0][0] == 3  # NULL excluded from COUNT


def test_duckdb_aggregate_distinct_count(conn):
    req = AggregateRequest(aggregations=[AggregationSpec(function="DISTINCT_COUNT", column="city")])
    q = build_aggregate_query(req, PROFILE)
    rows = conn.execute(q.sql, q.parameters).fetchall()
    assert rows[0][0] == 2  # London, Paris


def test_duckdb_aggregate_group_by(conn):
    req = AggregateRequest(
        group_by=["city"],
        aggregations=[AggregationSpec(function="COUNT", column="age")],
    )
    q = build_aggregate_query(req, PROFILE)
    rows = conn.execute(q.sql, q.parameters).fetchall()
    # city=London (2 rows), city=Paris (1 row), city=NULL (excluded from count)
    result = {r[0]: r[1] for r in rows if r[0] is not None}
    assert result["London"] == 2
    assert result["Paris"] == 1


def test_duckdb_aggregate_stddev(conn):
    req = AggregateRequest(aggregations=[AggregationSpec(function="STDDEV", column="salary")])
    q = build_aggregate_query(req, PROFILE)
    rows = conn.execute(q.sql, q.parameters).fetchall()
    # Just verify it executes without error and returns a numeric result
    assert rows[0][0] is not None


def test_duckdb_aggregate_median(conn):
    req = AggregateRequest(aggregations=[AggregationSpec(function="MEDIAN", column="age")])
    q = build_aggregate_query(req, PROFILE)
    rows = conn.execute(q.sql, q.parameters).fetchall()
    assert rows[0][0] == 30.0


# ---------------------------------------------------------------------------
# Describe
# ---------------------------------------------------------------------------


def test_duckdb_describe_executes(conn):
    req = DescribeRequest(columns=["age"])
    q = build_describe_query(req, PROFILE)
    rows = conn.execute(q.sql, q.parameters).fetchall()
    assert len(rows) == 1  # single-row result


def test_duckdb_describe_percentile_cont(conn):
    """Verify PERCENTILE_CONT WITHIN GROUP syntax is accepted by DuckDB."""
    req = DescribeRequest(columns=["salary"])
    q = build_describe_query(req, PROFILE)
    # If DuckDB doesn't support WITHIN GROUP, this raises
    rows = conn.execute(q.sql, q.parameters).fetchall()
    assert len(rows) == 1


def test_duckdb_describe_all_numeric(conn):
    req = DescribeRequest()
    q = build_describe_query(req, PROFILE)
    rows = conn.execute(q.sql, q.parameters).fetchall()
    assert len(rows) == 1


# ---------------------------------------------------------------------------
# Correlate
# ---------------------------------------------------------------------------


def test_duckdb_correlate_basic(conn):
    req = CorrelateRequest(columns=["age", "salary"])
    q = build_correlate_query(req, PROFILE)
    rows = conn.execute(q.sql, q.parameters).fetchall()
    assert len(rows) == 1
    # Correlation between age and salary (positive relationship in test data)
    corr_value = rows[0][0]
    assert corr_value is not None
    assert -1.0 <= corr_value <= 1.0


def test_duckdb_correlate_all_numeric(conn):
    req = CorrelateRequest()
    q = build_correlate_query(req, PROFILE)
    rows = conn.execute(q.sql, q.parameters).fetchall()
    assert len(rows) == 1


# ---------------------------------------------------------------------------
# Identifier quoting — DuckDB round-trip
# ---------------------------------------------------------------------------


def test_duckdb_quoted_column_with_space(conn):
    """Column names with spaces must be correctly quoted for DuckDB."""
    conn.execute('CREATE TABLE spaces_test ("first name" VARCHAR, "last name" VARCHAR)')
    conn.execute("INSERT INTO spaces_test VALUES ('Alice', 'Smith'), ('Bob', 'Jones')")

    profile = _make_profile(("first name", "categorical"), ("last name", "categorical"))
    req = SortRequest(columns=[SortColumn(column="first name", direction="asc")])
    q = build_sort_query(req, profile)
    # Replace table name for this test
    sql = q.sql.replace("FROM dataset", "FROM spaces_test")
    rows = conn.execute(sql, q.parameters).fetchall()
    assert [r[0] for r in rows] == ["Alice", "Bob"]
