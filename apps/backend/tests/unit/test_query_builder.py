"""
Unit tests for app/services/analysis/query_builder.py

Security focus: every test involving user-supplied values verifies that those
values appear in the parameters list, NOT in the SQL string.

Coverage:
- Filter: all 9 operators, parameter binding, LIKE escaping, type validation
- Sort: asc/desc, multi-column, identifier quoting
- Aggregate: all 8 functions, group_by, alias management, DISTINCT_COUNT
- Describe: auto-detect numeric, explicit columns, type gate
- Correlate: pair generation, minimum-columns check, type gate
- Security: SQL injection in values, SQL keywords in column names, wildcard injection
- Resource limits: max_result_rows in LIMIT clause
"""

from __future__ import annotations

import pytest

from app.schemas.analysis import (
    AggregateRequest,
    AggregationSpec,
    CorrelateRequest,
    DescribeRequest,
    FilterCondition,
    FilterRequest,
    SortColumn,
    SortRequest,
)
from app.schemas.dataset import ColumnProfile, DatasetMetrics, ProfileSummary
from app.services.analysis.exceptions import (
    ColumnTypeError,
    DuplicateAliasError,
    InvalidAliasError,
    MissingValueError,
    QueryBuilderError,
    ResourceLimitError,
    UnknownColumnError,
)
from app.services.analysis.query_builder import (
    BuiltQuery,
    _escape_like_pattern,
    _quote_identifier,
    build_aggregate_query,
    build_correlate_query,
    build_describe_query,
    build_filter_query,
    build_sort_query,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_profile(*cols: tuple[str, str]) -> ProfileSummary:
    """Build a minimal ProfileSummary from (name, logical_type) pairs."""
    columns = [
        ColumnProfile(
            name=name,
            logical_type=lt,
            row_count=100,
            non_null_count=100,
            missing_count=0,
            missing_percentage=0.0,
            unique_count=10,
            unique_percentage=10.0,
        )
        for name, lt in cols
    ]
    metrics = DatasetMetrics(
        name="test.csv",
        file_type="csv",
        row_count=100,
        column_count=len(cols),
        total_missing=0,
        missing_percentage=0.0,
        duplicate_rows=0,
        duplicate_percentage=0.0,
        numeric_columns=sum(1 for _, lt in cols if lt == "numeric"),
        categorical_columns=sum(1 for _, lt in cols if lt == "categorical"),
        text_columns=sum(1 for _, lt in cols if lt == "text"),
        boolean_columns=sum(1 for _, lt in cols if lt == "boolean"),
        datetime_columns=sum(1 for _, lt in cols if lt == "datetime"),
    )
    return ProfileSummary(dataset=metrics, columns=columns, quality_warnings=[])


# Standard test profile used across most tests
PROFILE = _make_profile(
    ("age", "numeric"),
    ("salary", "numeric"),
    ("city", "categorical"),
    ("bio", "text"),
    ("active", "boolean"),
    ("joined_at", "datetime"),
)


# ---------------------------------------------------------------------------
# _quote_identifier
# ---------------------------------------------------------------------------


def test_quote_simple_identifier():
    assert _quote_identifier("age") == '"age"'


def test_quote_identifier_with_space():
    assert _quote_identifier("my column") == '"my column"'


def test_quote_identifier_with_double_quote():
    assert _quote_identifier('col"name') == '"col""name"'


def test_quote_identifier_sql_keyword():
    assert _quote_identifier("select") == '"select"'


def test_quote_identifier_empty_string():
    assert _quote_identifier("") == '""'


# ---------------------------------------------------------------------------
# _escape_like_pattern
# ---------------------------------------------------------------------------


def test_escape_like_no_metacharacters():
    assert _escape_like_pattern("hello") == "%hello%"


def test_escape_like_percent():
    result = _escape_like_pattern("50% off")
    assert "\\%" in result
    assert result.startswith("%")
    assert result.endswith("%")
    # literal % in input must not appear unescaped in output
    # (after wrapping the only % chars should be the leading/trailing wildcards)
    inner = result[1:-1]
    assert "\\%" in inner


def test_escape_like_underscore():
    result = _escape_like_pattern("col_name")
    assert "\\_" in result


def test_escape_like_backslash():
    result = _escape_like_pattern("C:\\path")
    assert "\\\\" in result


def test_escape_like_all_metacharacters():
    result = _escape_like_pattern("a%b_c\\d")
    inner = result[1:-1]
    assert "\\%" in inner
    assert "\\_" in inner
    assert "\\\\" in inner


# ---------------------------------------------------------------------------
# Filter — eq
# ---------------------------------------------------------------------------


def test_filter_eq_numeric():
    req = FilterRequest(conditions=[FilterCondition(column="age", operator="eq", value=30)])
    q = build_filter_query(req, PROFILE)
    assert '"age" = ?' in q.sql
    assert q.parameters == [30]
    assert q.is_limited is True


def test_filter_eq_string():
    req = FilterRequest(conditions=[FilterCondition(column="city", operator="eq", value="London")])
    q = build_filter_query(req, PROFILE)
    assert '"city" = ?' in q.sql
    assert q.parameters == ["London"]


def test_filter_eq_bool():
    req = FilterRequest(conditions=[FilterCondition(column="active", operator="eq", value=True)])
    q = build_filter_query(req, PROFILE)
    assert q.parameters == [True]


# ---------------------------------------------------------------------------
# Filter — neq
# ---------------------------------------------------------------------------


def test_filter_neq():
    req = FilterRequest(conditions=[FilterCondition(column="age", operator="neq", value=0)])
    q = build_filter_query(req, PROFILE)
    assert '"age" != ?' in q.sql
    assert q.parameters == [0]


# ---------------------------------------------------------------------------
# Filter — comparison operators
# ---------------------------------------------------------------------------


def test_filter_gt():
    req = FilterRequest(conditions=[FilterCondition(column="age", operator="gt", value=18)])
    q = build_filter_query(req, PROFILE)
    assert '"age" > ?' in q.sql
    assert q.parameters == [18]


def test_filter_lt():
    req = FilterRequest(conditions=[FilterCondition(column="salary", operator="lt", value=100000)])
    q = build_filter_query(req, PROFILE)
    assert '"salary" < ?' in q.sql


def test_filter_gte():
    req = FilterRequest(conditions=[FilterCondition(column="age", operator="gte", value=18)])
    q = build_filter_query(req, PROFILE)
    assert '"age" >= ?' in q.sql


def test_filter_lte():
    req = FilterRequest(conditions=[FilterCondition(column="age", operator="lte", value=65)])
    q = build_filter_query(req, PROFILE)
    assert '"age" <= ?' in q.sql


# ---------------------------------------------------------------------------
# Filter — contains
# ---------------------------------------------------------------------------


def test_filter_contains_generates_like():
    req = FilterRequest(
        conditions=[FilterCondition(column="city", operator="contains", value="York")]
    )
    q = build_filter_query(req, PROFILE)
    assert "LIKE ?" in q.sql
    assert "ESCAPE" in q.sql
    assert q.parameters == ["%York%"]


def test_filter_contains_escapes_percent_in_value():
    req = FilterRequest(
        conditions=[FilterCondition(column="city", operator="contains", value="50%")]
    )
    q = build_filter_query(req, PROFILE)
    # value must not contain unescaped % except at start/end (wildcard wrap)
    param = q.parameters[0]
    assert isinstance(param, str)
    inner = param[1:-1]
    assert "\\%" in inner


def test_filter_contains_escapes_underscore_in_value():
    req = FilterRequest(
        conditions=[FilterCondition(column="bio", operator="contains", value="col_name")]
    )
    q = build_filter_query(req, PROFILE)
    param = q.parameters[0]
    assert "\\_" in param


def test_filter_contains_escapes_backslash_in_value():
    req = FilterRequest(
        conditions=[FilterCondition(column="bio", operator="contains", value="C:\\path")]
    )
    q = build_filter_query(req, PROFILE)
    param = q.parameters[0]
    assert "\\\\" in param


# ---------------------------------------------------------------------------
# Filter — is_null / is_not_null
# ---------------------------------------------------------------------------


def test_filter_is_null_no_parameter():
    req = FilterRequest(conditions=[FilterCondition(column="age", operator="is_null")])
    q = build_filter_query(req, PROFILE)
    assert '"age" IS NULL' in q.sql
    assert q.parameters == []


def test_filter_is_not_null_no_parameter():
    req = FilterRequest(conditions=[FilterCondition(column="salary", operator="is_not_null")])
    q = build_filter_query(req, PROFILE)
    assert '"salary" IS NOT NULL' in q.sql
    assert q.parameters == []


def test_filter_is_null_with_value_raises():
    with pytest.raises(QueryBuilderError, match="does not accept a value"):
        req = FilterRequest(conditions=[FilterCondition(column="age", operator="is_null", value=0)])
        build_filter_query(req, PROFILE)


def test_filter_is_not_null_with_value_raises():
    with pytest.raises(QueryBuilderError, match="does not accept a value"):
        req = FilterRequest(
            conditions=[FilterCondition(column="age", operator="is_not_null", value=42)]
        )
        build_filter_query(req, PROFILE)


# ---------------------------------------------------------------------------
# Filter — multiple conditions (AND)
# ---------------------------------------------------------------------------


def test_filter_multiple_conditions_joined_with_and():
    req = FilterRequest(
        conditions=[
            FilterCondition(column="age", operator="gte", value=18),
            FilterCondition(column="city", operator="eq", value="London"),
        ]
    )
    q = build_filter_query(req, PROFILE)
    assert " AND " in q.sql
    assert q.parameters == [18, "London"]


def test_filter_parameters_in_order():
    req = FilterRequest(
        conditions=[
            FilterCondition(column="age", operator="gt", value=10),
            FilterCondition(column="salary", operator="lt", value=200000),
            FilterCondition(column="city", operator="eq", value="NYC"),
        ]
    )
    q = build_filter_query(req, PROFILE)
    assert q.parameters == [10, 200000, "NYC"]


# ---------------------------------------------------------------------------
# Filter — LIMIT
# ---------------------------------------------------------------------------


def test_filter_default_limit():
    req = FilterRequest(conditions=[FilterCondition(column="age", operator="is_null")])
    q = build_filter_query(req, PROFILE)
    assert "LIMIT 10000" in q.sql


def test_filter_custom_limit():
    req = FilterRequest(conditions=[FilterCondition(column="age", operator="is_null")])
    q = build_filter_query(req, PROFILE, max_result_rows=500)
    assert "LIMIT 500" in q.sql


# ---------------------------------------------------------------------------
# Filter — validation errors
# ---------------------------------------------------------------------------


def test_filter_unknown_column_raises():
    req = FilterRequest(conditions=[FilterCondition(column="nonexistent", operator="eq", value=1)])
    with pytest.raises(UnknownColumnError, match="nonexistent"):
        build_filter_query(req, PROFILE)


def test_filter_gt_on_categorical_raises():
    req = FilterRequest(conditions=[FilterCondition(column="city", operator="gt", value="A")])
    with pytest.raises(ColumnTypeError, match="'gt'"):
        build_filter_query(req, PROFILE)


def test_filter_contains_on_numeric_raises():
    req = FilterRequest(
        conditions=[FilterCondition(column="age", operator="contains", value="hello")]
    )
    with pytest.raises(ColumnTypeError, match="'contains'"):
        build_filter_query(req, PROFILE)


def test_filter_contains_on_boolean_raises():
    req = FilterRequest(
        conditions=[FilterCondition(column="active", operator="contains", value="yes")]
    )
    with pytest.raises(ColumnTypeError, match="'contains'"):
        build_filter_query(req, PROFILE)


def test_filter_eq_missing_value_raises():
    req = FilterRequest(conditions=[FilterCondition(column="age", operator="eq", value=None)])
    with pytest.raises(MissingValueError, match="requires a non-null value"):
        build_filter_query(req, PROFILE)


def test_filter_contains_non_string_value_raises():
    req = FilterRequest(
        conditions=[FilterCondition(column="city", operator="contains", value=42)]  # type: ignore[arg-type]
    )
    with pytest.raises(ColumnTypeError, match="string value"):
        build_filter_query(req, PROFILE)


# ---------------------------------------------------------------------------
# Filter — datetime column operators
# ---------------------------------------------------------------------------


def test_filter_gt_on_datetime_allowed():
    req = FilterRequest(
        conditions=[FilterCondition(column="joined_at", operator="gt", value="2024-01-01")]
    )
    q = build_filter_query(req, PROFILE)
    assert '"joined_at" > ?' in q.sql
    assert q.parameters == ["2024-01-01"]


def test_filter_contains_on_datetime_raises():
    req = FilterRequest(
        conditions=[FilterCondition(column="joined_at", operator="contains", value="2024")]
    )
    with pytest.raises(ColumnTypeError):
        build_filter_query(req, PROFILE)


# ---------------------------------------------------------------------------
# Filter — security: SQL injection attempts in values
# ---------------------------------------------------------------------------


def test_injection_sql_statement_in_value_is_parameterized():
    """SQL statement in a value must be a parameter, never interpolated."""
    malicious = "'; DROP TABLE datasets; --"
    req = FilterRequest(conditions=[FilterCondition(column="city", operator="eq", value=malicious)])
    q = build_filter_query(req, PROFILE)
    assert malicious not in q.sql
    assert q.parameters == [malicious]


def test_injection_sql_comment_in_value_is_parameterized():
    malicious = "London' -- "
    req = FilterRequest(conditions=[FilterCondition(column="city", operator="eq", value=malicious)])
    q = build_filter_query(req, PROFILE)
    assert malicious not in q.sql
    assert q.parameters == [malicious]


def test_injection_quotes_in_value_are_parameterized():
    malicious = "' OR '1'='1"
    req = FilterRequest(conditions=[FilterCondition(column="city", operator="eq", value=malicious)])
    q = build_filter_query(req, PROFILE)
    assert malicious not in q.sql
    assert q.parameters == [malicious]


def test_injection_semicolon_in_value_is_parameterized():
    malicious = "x; SELECT 1"
    req = FilterRequest(
        conditions=[FilterCondition(column="bio", operator="contains", value=malicious)]
    )
    q = build_filter_query(req, PROFILE)
    assert "SELECT 1" not in q.sql
    assert isinstance(q.parameters[0], str)


def test_injection_union_in_value_is_parameterized():
    malicious = "' UNION SELECT username, password FROM users --"
    req = FilterRequest(conditions=[FilterCondition(column="city", operator="eq", value=malicious)])
    q = build_filter_query(req, PROFILE)
    assert "UNION" not in q.sql
    assert q.parameters == [malicious]


def test_injection_malicious_column_name_is_rejected():
    """An attacker supplying a crafted column name must be rejected, not interpolated."""
    req = FilterRequest(
        conditions=[FilterCondition(column="age; DROP TABLE datasets", operator="eq", value=1)]
    )
    with pytest.raises(UnknownColumnError):
        build_filter_query(req, PROFILE)


def test_injection_double_quote_in_column_name_is_escaped():
    profile = _make_profile(('col"name', "numeric"))
    req = FilterRequest(conditions=[FilterCondition(column='col"name', operator="eq", value=1)])
    q = build_filter_query(
        req, PROFILE if 'col"name' in [c.name for c in PROFILE.columns] else profile
    )
    # Double-quote in identifier must be escaped as ""
    assert '""' in q.sql


def test_wildcard_injection_via_contains_escapes_percent():
    """A % in a contains value must not become a SQL wildcard."""
    req = FilterRequest(conditions=[FilterCondition(column="bio", operator="contains", value="%")])
    q = build_filter_query(req, PROFILE)
    param = q.parameters[0]
    # The only unescaped % should be the leading/trailing wildcards
    inner = param[1:-1]
    # inner should be \%  (escaped percent)
    assert inner == "\\%"


def test_wildcard_injection_via_contains_escapes_underscore():
    req = FilterRequest(conditions=[FilterCondition(column="bio", operator="contains", value="_")])
    q = build_filter_query(req, PROFILE)
    inner = q.parameters[0][1:-1]
    assert inner == "\\_"


# ---------------------------------------------------------------------------
# Sort
# ---------------------------------------------------------------------------


def test_sort_asc():
    req = SortRequest(columns=[SortColumn(column="age", direction="asc")])
    q = build_sort_query(req, PROFILE)
    assert '"age" ASC' in q.sql
    assert q.parameters == []
    assert q.is_limited is True


def test_sort_desc():
    req = SortRequest(columns=[SortColumn(column="salary", direction="desc")])
    q = build_sort_query(req, PROFILE)
    assert '"salary" DESC' in q.sql


def test_sort_multiple_columns():
    req = SortRequest(
        columns=[
            SortColumn(column="city", direction="asc"),
            SortColumn(column="age", direction="desc"),
        ]
    )
    q = build_sort_query(req, PROFILE)
    assert '"city" ASC' in q.sql
    assert '"age" DESC' in q.sql
    assert q.sql.index('"city"') < q.sql.index('"age"')


def test_sort_unknown_column_raises():
    req = SortRequest(columns=[SortColumn(column="nonexistent", direction="asc")])
    with pytest.raises(UnknownColumnError, match="nonexistent"):
        build_sort_query(req, PROFILE)


def test_sort_limit_applied():
    req = SortRequest(columns=[SortColumn(column="age", direction="asc")])
    q = build_sort_query(req, PROFILE, max_result_rows=250)
    assert "LIMIT 250" in q.sql


def test_sort_identifier_quoted():
    profile = _make_profile(("first name", "categorical"))
    req = SortRequest(columns=[SortColumn(column="first name", direction="asc")])
    q = build_sort_query(req, profile)
    assert '"first name" ASC' in q.sql


def test_sort_no_parameters():
    req = SortRequest(columns=[SortColumn(column="age", direction="asc")])
    q = build_sort_query(req, PROFILE)
    assert q.parameters == []


# ---------------------------------------------------------------------------
# Aggregate — individual functions
# ---------------------------------------------------------------------------


def test_aggregate_sum():
    req = AggregateRequest(aggregations=[AggregationSpec(function="SUM", column="salary")])
    q = build_aggregate_query(req, PROFILE)
    assert 'SUM("salary")' in q.sql


def test_aggregate_avg():
    req = AggregateRequest(aggregations=[AggregationSpec(function="AVG", column="age")])
    q = build_aggregate_query(req, PROFILE)
    assert 'AVG("age")' in q.sql


def test_aggregate_count():
    req = AggregateRequest(aggregations=[AggregationSpec(function="COUNT", column="age")])
    q = build_aggregate_query(req, PROFILE)
    assert 'COUNT("age")' in q.sql


def test_aggregate_min():
    req = AggregateRequest(aggregations=[AggregationSpec(function="MIN", column="salary")])
    q = build_aggregate_query(req, PROFILE)
    assert 'MIN("salary")' in q.sql


def test_aggregate_max():
    req = AggregateRequest(aggregations=[AggregationSpec(function="MAX", column="age")])
    q = build_aggregate_query(req, PROFILE)
    assert 'MAX("age")' in q.sql


def test_aggregate_median():
    req = AggregateRequest(aggregations=[AggregationSpec(function="MEDIAN", column="salary")])
    q = build_aggregate_query(req, PROFILE)
    assert 'MEDIAN("salary")' in q.sql


def test_aggregate_stddev_maps_to_stddev_samp():
    req = AggregateRequest(aggregations=[AggregationSpec(function="STDDEV", column="age")])
    q = build_aggregate_query(req, PROFILE)
    assert 'STDDEV_SAMP("age")' in q.sql


def test_aggregate_distinct_count():
    req = AggregateRequest(aggregations=[AggregationSpec(function="DISTINCT_COUNT", column="city")])
    q = build_aggregate_query(req, PROFILE)
    assert 'COUNT(DISTINCT "city")' in q.sql


# ---------------------------------------------------------------------------
# Aggregate — group_by
# ---------------------------------------------------------------------------


def test_aggregate_with_group_by():
    req = AggregateRequest(
        group_by=["city"],
        aggregations=[AggregationSpec(function="SUM", column="salary")],
    )
    q = build_aggregate_query(req, PROFILE)
    assert 'GROUP BY "city"' in q.sql
    assert '"city"' in q.sql
    assert 'SUM("salary")' in q.sql


def test_aggregate_no_group_by_no_group_by_clause():
    req = AggregateRequest(aggregations=[AggregationSpec(function="COUNT", column="age")])
    q = build_aggregate_query(req, PROFILE)
    assert "GROUP BY" not in q.sql


def test_aggregate_multiple_group_by():
    req = AggregateRequest(
        group_by=["city", "active"],
        aggregations=[AggregationSpec(function="AVG", column="salary")],
    )
    q = build_aggregate_query(req, PROFILE)
    assert 'GROUP BY "city", "active"' in q.sql


# ---------------------------------------------------------------------------
# Aggregate — alias management
# ---------------------------------------------------------------------------


def test_aggregate_auto_alias_format():
    req = AggregateRequest(aggregations=[AggregationSpec(function="SUM", column="salary")])
    q = build_aggregate_query(req, PROFILE)
    assert '"sum_salary"' in q.sql


def test_aggregate_user_alias():
    req = AggregateRequest(
        aggregations=[AggregationSpec(function="SUM", column="salary", alias="total_salary")]
    )
    q = build_aggregate_query(req, PROFILE)
    assert '"total_salary"' in q.sql


def test_aggregate_duplicate_auto_alias_raises():
    req = AggregateRequest(
        aggregations=[
            AggregationSpec(function="SUM", column="salary"),
            AggregationSpec(function="SUM", column="salary"),
        ]
    )
    with pytest.raises(DuplicateAliasError):
        build_aggregate_query(req, PROFILE)


def test_aggregate_duplicate_user_alias_raises():
    req = AggregateRequest(
        aggregations=[
            AggregationSpec(function="SUM", column="salary", alias="total"),
            AggregationSpec(function="AVG", column="age", alias="total"),
        ]
    )
    with pytest.raises(DuplicateAliasError):
        build_aggregate_query(req, PROFILE)


def test_aggregate_empty_alias_raises():
    req = AggregateRequest(
        aggregations=[AggregationSpec(function="SUM", column="salary", alias="")]
    )
    with pytest.raises(InvalidAliasError, match="must not be empty"):
        build_aggregate_query(req, PROFILE)


def test_aggregate_alias_too_long_raises():
    long_alias = "a" * 256
    req = AggregateRequest(
        aggregations=[AggregationSpec(function="SUM", column="salary", alias=long_alias)]
    )
    with pytest.raises(InvalidAliasError, match="exceeds"):
        build_aggregate_query(req, PROFILE)


# ---------------------------------------------------------------------------
# Aggregate — validation errors
# ---------------------------------------------------------------------------


def test_aggregate_unknown_column_raises():
    req = AggregateRequest(aggregations=[AggregationSpec(function="SUM", column="nonexistent")])
    with pytest.raises(UnknownColumnError, match="nonexistent"):
        build_aggregate_query(req, PROFILE)


def test_aggregate_unknown_group_by_column_raises():
    req = AggregateRequest(
        group_by=["nonexistent"],
        aggregations=[AggregationSpec(function="COUNT", column="age")],
    )
    with pytest.raises(UnknownColumnError, match="nonexistent"):
        build_aggregate_query(req, PROFILE)


def test_aggregate_no_parameters():
    req = AggregateRequest(aggregations=[AggregationSpec(function="COUNT", column="age")])
    q = build_aggregate_query(req, PROFILE)
    assert q.parameters == []


def test_aggregate_limit_applied():
    req = AggregateRequest(aggregations=[AggregationSpec(function="COUNT", column="age")])
    q = build_aggregate_query(req, PROFILE, max_result_rows=1000)
    assert "LIMIT 1000" in q.sql
    assert q.is_limited is True


# ---------------------------------------------------------------------------
# Describe
# ---------------------------------------------------------------------------


def test_describe_all_numeric_columns():
    req = DescribeRequest()
    q = build_describe_query(req, PROFILE)
    assert '"age"' in q.sql
    assert '"salary"' in q.sql
    # Non-numeric columns must not appear
    assert '"city"' not in q.sql
    assert '"bio"' not in q.sql


def test_describe_specific_columns():
    req = DescribeRequest(columns=["age"])
    q = build_describe_query(req, PROFILE)
    assert '"age"' in q.sql
    assert '"salary"' not in q.sql


def test_describe_includes_all_stats():
    req = DescribeRequest(columns=["age"])
    q = build_describe_query(req, PROFILE)
    for stat in ("COUNT", "AVG", "MEDIAN", "STDDEV_SAMP", "MIN", "MAX", "PERCENTILE_CONT"):
        assert stat in q.sql


def test_describe_stat_aliases_use_column_prefix():
    req = DescribeRequest(columns=["age"])
    q = build_describe_query(req, PROFILE)
    for suffix in ("_count", "_mean", "_median", "_std", "_min", "_max", "_q1", "_q3"):
        assert f"age{suffix}" in q.sql


def test_describe_non_numeric_column_raises():
    req = DescribeRequest(columns=["city"])
    with pytest.raises(ColumnTypeError, match="'describe' only supports numeric"):
        build_describe_query(req, PROFILE)


def test_describe_unknown_column_raises():
    req = DescribeRequest(columns=["nonexistent"])
    with pytest.raises(UnknownColumnError):
        build_describe_query(req, PROFILE)


def test_describe_no_numeric_columns_raises():
    profile = _make_profile(("city", "categorical"), ("bio", "text"))
    req = DescribeRequest()
    with pytest.raises(QueryBuilderError, match="No numeric columns"):
        build_describe_query(req, profile)


def test_describe_no_parameters():
    req = DescribeRequest(columns=["age"])
    q = build_describe_query(req, PROFILE)
    assert q.parameters == []


def test_describe_not_limited():
    req = DescribeRequest(columns=["age"])
    q = build_describe_query(req, PROFILE)
    assert q.is_limited is False
    assert "LIMIT" not in q.sql


# ---------------------------------------------------------------------------
# Correlate
# ---------------------------------------------------------------------------


def test_correlate_basic_two_columns():
    req = CorrelateRequest(columns=["age", "salary"])
    q = build_correlate_query(req, PROFILE)
    assert 'CORR("age", "salary")' in q.sql
    # Only 1 pair for 2 columns
    assert q.sql.count("CORR(") == 1


def test_correlate_three_columns_generates_three_pairs():
    profile = _make_profile(("a", "numeric"), ("b", "numeric"), ("c", "numeric"))
    req = CorrelateRequest(columns=["a", "b", "c"])
    q = build_correlate_query(req, profile)
    # 3 unique pairs: (a,b), (a,c), (b,c)
    assert q.sql.count("CORR(") == 3


def test_correlate_auto_detects_numeric_columns():
    req = CorrelateRequest()
    q = build_correlate_query(req, PROFILE)
    # PROFILE has 2 numeric columns (age, salary) → 1 pair
    assert q.sql.count("CORR(") == 1
    assert '"age"' in q.sql
    assert '"salary"' in q.sql


def test_correlate_alias_uses_double_underscore():
    req = CorrelateRequest(columns=["age", "salary"])
    q = build_correlate_query(req, PROFILE)
    assert '"age__salary"' in q.sql


def test_correlate_non_numeric_column_raises():
    req = CorrelateRequest(columns=["age", "city"])
    with pytest.raises(ColumnTypeError, match="'correlate' only supports numeric"):
        build_correlate_query(req, PROFILE)


def test_correlate_unknown_column_raises():
    req = CorrelateRequest(columns=["age", "nonexistent"])
    with pytest.raises(UnknownColumnError):
        build_correlate_query(req, PROFILE)


def test_correlate_one_column_raises():
    req = CorrelateRequest(columns=["age"])
    with pytest.raises(QueryBuilderError, match="At least 2"):
        build_correlate_query(req, PROFILE)


def test_correlate_no_numeric_columns_raises():
    profile = _make_profile(("city", "categorical"))
    req = CorrelateRequest()
    with pytest.raises(QueryBuilderError, match="At least 2"):
        build_correlate_query(req, profile)


def test_correlate_no_parameters():
    req = CorrelateRequest(columns=["age", "salary"])
    q = build_correlate_query(req, PROFILE)
    assert q.parameters == []


def test_correlate_not_limited():
    req = CorrelateRequest(columns=["age", "salary"])
    q = build_correlate_query(req, PROFILE)
    assert q.is_limited is False
    assert "LIMIT" not in q.sql


def test_correlate_upper_triangle_only():
    """Each pair should appear exactly once (a,b not duplicated as b,a)."""
    profile = _make_profile(("x", "numeric"), ("y", "numeric"), ("z", "numeric"))
    req = CorrelateRequest(columns=["x", "y", "z"])
    q = build_correlate_query(req, profile)
    # Pairs: (x,y), (x,z), (y,z) = 3
    assert q.sql.count("CORR(") == 3
    # (y,x) must not appear — only (x,y)
    assert 'CORR("y", "x")' not in q.sql


# ---------------------------------------------------------------------------
# BuiltQuery dataclass
# ---------------------------------------------------------------------------


def test_built_query_fields():
    bq = BuiltQuery(sql="SELECT 1", parameters=[1, "a"], is_limited=True)
    assert bq.sql == "SELECT 1"
    assert bq.parameters == [1, "a"]
    assert bq.is_limited is True


def test_built_query_default_is_limited_false():
    bq = BuiltQuery(sql="SELECT 1", parameters=[])
    assert bq.is_limited is False


# ---------------------------------------------------------------------------
# Resource limit — max_result_rows
# ---------------------------------------------------------------------------


def test_max_result_rows_in_filter_sql():
    req = FilterRequest(conditions=[FilterCondition(column="age", operator="is_null")])
    q = build_filter_query(req, PROFILE, max_result_rows=42)
    assert "LIMIT 42" in q.sql


def test_max_result_rows_in_sort_sql():
    req = SortRequest(columns=[SortColumn(column="age")])
    q = build_sort_query(req, PROFILE, max_result_rows=99)
    assert "LIMIT 99" in q.sql


def test_max_result_rows_in_aggregate_sql():
    req = AggregateRequest(aggregations=[AggregationSpec(function="COUNT", column="age")])
    q = build_aggregate_query(req, PROFILE, max_result_rows=777)
    assert "LIMIT 777" in q.sql


# ---------------------------------------------------------------------------
# Identifier quoting in SQL output
# ---------------------------------------------------------------------------


def test_column_with_space_quoted_in_filter():
    profile = _make_profile(("first name", "categorical"))
    req = FilterRequest(
        conditions=[FilterCondition(column="first name", operator="eq", value="Alice")]
    )
    q = build_filter_query(req, profile)
    assert '"first name" = ?' in q.sql
    assert q.parameters == ["Alice"]


def test_column_with_sql_keyword_quoted():
    profile = _make_profile(("select", "numeric"))
    req = FilterRequest(conditions=[FilterCondition(column="select", operator="gt", value=0)])
    q = build_filter_query(req, profile)
    assert '"select" > ?' in q.sql


def test_column_with_double_quote_escaped_in_filter():
    profile = _make_profile(('my"col', "numeric"))
    req = FilterRequest(conditions=[FilterCondition(column='my"col', operator="eq", value=1)])
    q = build_filter_query(req, profile)
    assert '"my""col"' in q.sql


# ---------------------------------------------------------------------------
# Resource limits — max_correlation_columns
# ---------------------------------------------------------------------------


def test_correlate_too_many_columns_raises():
    """build_correlate_query must reject more columns than max_correlation_columns."""
    many_cols = [(f"col_{i}", "numeric") for i in range(10)]
    profile = _make_profile(*many_cols)
    req = CorrelateRequest(columns=[f"col_{i}" for i in range(10)])
    with pytest.raises(ResourceLimitError, match="Too many columns"):
        build_correlate_query(req, profile, max_correlation_columns=5)


def test_correlate_at_limit_allowed():
    """Exactly max_correlation_columns columns must not raise."""
    cols = [(f"col_{i}", "numeric") for i in range(5)]
    profile = _make_profile(*cols)
    req = CorrelateRequest(columns=[f"col_{i}" for i in range(5)])
    q = build_correlate_query(req, profile, max_correlation_columns=5)
    # 5 columns → 10 unique pairs
    assert q.sql.count("CORR(") == 10


def test_correlate_default_max_is_fifty():
    """Default max_correlation_columns is 50 — 51 should raise."""
    cols = [(f"col_{i}", "numeric") for i in range(51)]
    profile = _make_profile(*cols)
    req = CorrelateRequest(columns=[f"col_{i}" for i in range(51)])
    with pytest.raises(ResourceLimitError):
        build_correlate_query(req, profile)
