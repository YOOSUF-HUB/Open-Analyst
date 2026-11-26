"""
Secure query builder for the Phase 2 Deterministic Analysis Engine.

Converts validated Pydantic analysis requests into DuckDB-compatible SQL.

Security guarantees
-------------------
- User-supplied values are NEVER interpolated into SQL strings.
  They are always returned as positional (?) parameters.
- Column identifiers are validated against the dataset's ProfileSummary
  before being referenced in the SQL.
- All identifiers are double-quoted with any internal double-quotes escaped
  as "" (standard SQL identifier quoting).
- SQL operators are looked up from an explicit frozenset allowlist.
- SQL aggregate functions are looked up from an explicit frozenset allowlist.
- Sort directions are validated against an explicit frozenset allowlist.
- contains() values are LIKE-escaped (%, _, backslash) before binding,
  preventing wildcard injection while preserving literal substring semantics.

The generated SQL references the table name `dataset`.  The execution layer
(M4) registers the in-memory DataFrame under that exact name before running
the query through DuckDB.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.analysis import (
    AggregateRequest,
    CorrelateRequest,
    DescribeRequest,
    FilterRequest,
    SortRequest,
)
from app.schemas.dataset import ProfileSummary
from app.services.analysis.exceptions import (
    ColumnTypeError,
    DuplicateAliasError,
    InvalidAliasError,
    MissingValueError,
    QueryBuilderError,
    ResourceLimitError,
    UnknownColumnError,
)

# DuckDB table name that the execution layer registers the DataFrame under.
_TABLE = "dataset"

# ---------------------------------------------------------------------------
# Allowlists
# ---------------------------------------------------------------------------

_VALID_DIRECTIONS: frozenset[str] = frozenset({"asc", "desc"})

# Operators that require a non-None value
_VALUE_REQUIRED_OPERATORS: frozenset[str] = frozenset(
    {"eq", "neq", "gt", "lt", "gte", "lte", "contains"}
)

# Operators that use no value
_NO_VALUE_OPERATORS: frozenset[str] = frozenset({"is_null", "is_not_null"})

# Valid operators for each logical type
_OPERATORS_BY_TYPE: dict[str, frozenset[str]] = {
    "numeric": frozenset({"eq", "neq", "gt", "lt", "gte", "lte", "is_null", "is_not_null"}),
    "categorical": frozenset({"eq", "neq", "contains", "is_null", "is_not_null"}),
    "text": frozenset({"eq", "neq", "contains", "is_null", "is_not_null"}),
    "boolean": frozenset({"eq", "neq", "is_null", "is_not_null"}),
    "datetime": frozenset({"eq", "neq", "gt", "lt", "gte", "lte", "is_null", "is_not_null"}),
}

# Operator → SQL fragment  (column comes before the fragment)
_OPERATOR_SQL: dict[str, str] = {
    "eq": "= ?",
    "neq": "!= ?",
    "gt": "> ?",
    "lt": "< ?",
    "gte": ">= ?",
    "lte": "<= ?",
    "contains": r"LIKE ? ESCAPE '\'",
    "is_null": "IS NULL",
    "is_not_null": "IS NOT NULL",
}

# Aggregation function name → DuckDB SQL function
# DISTINCT_COUNT is handled specially (see _build_agg_expr).
_AGGREGATION_SQL: dict[str, str] = {
    "SUM": "SUM",
    "AVG": "AVG",
    "COUNT": "COUNT",
    "MIN": "MIN",
    "MAX": "MAX",
    "MEDIAN": "MEDIAN",
    "STDDEV": "STDDEV_SAMP",
}

# All valid aggregation function names (including DISTINCT_COUNT)
_ALL_FUNCTIONS: frozenset[str] = frozenset({*_AGGREGATION_SQL, "DISTINCT_COUNT"})

# Descriptive statistics computed per numeric column.
# {col} is replaced with the double-quoted identifier at build time.
_DESCRIBE_STATS: list[tuple[str, str]] = [
    ("count", "COUNT({col})"),
    ("mean", "AVG({col})"),
    ("median", "MEDIAN({col})"),
    ("std", "STDDEV_SAMP({col})"),
    ("min", "MIN({col})"),
    ("max", "MAX({col})"),
    ("q1", "PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {col})"),
    ("q3", "PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {col})"),
]

# Maximum alias length (characters)
_MAX_ALIAS_LEN = 255


# ---------------------------------------------------------------------------
# Public result type
# ---------------------------------------------------------------------------


@dataclass
class BuiltQuery:
    """The output produced by the query builder.

    sql:
        DuckDB-compatible SQL string.  User-supplied values are represented
        as ``?`` positional placeholders — never interpolated into the string.
    parameters:
        Bound parameter values in the same order as the ``?`` placeholders.
        Contains only non-None primitives (str, int, float, bool).
    is_limited:
        True when a LIMIT clause was added.  The execution layer should
        compare actual row count to the limit and report truncation if equal.
    """

    sql: str
    parameters: list[str | int | float | bool] = field(default_factory=list)
    is_limited: bool = False


# ---------------------------------------------------------------------------
# Internal helpers — identifier quoting
# ---------------------------------------------------------------------------


def _quote_identifier(name: str) -> str:
    """Double-quote an SQL identifier, escaping embedded double-quotes as ``""``."""
    return '"' + name.replace('"', '""') + '"'


# ---------------------------------------------------------------------------
# Internal helpers — column validation
# ---------------------------------------------------------------------------


def _get_column_types(profile: ProfileSummary) -> dict[str, str]:
    return {col.name: col.logical_type for col in profile.columns}


def _validate_column(col: str, column_types: dict[str, str]) -> None:
    if col not in column_types:
        available = sorted(column_types)
        raise UnknownColumnError(
            f"Column {col!r} does not exist in this dataset. Available columns: {available!r}"
        )


def _validate_operator_for_type(operator: str, logical_type: str, column: str) -> None:
    valid = _OPERATORS_BY_TYPE.get(logical_type, frozenset())
    if operator not in valid:
        raise ColumnTypeError(
            f"Operator '{operator}' is not supported for column '{column}' "
            f"(logical type: '{logical_type}'). "
            f"Supported operators for this type: {sorted(valid)!r}"
        )


# ---------------------------------------------------------------------------
# Internal helpers — LIKE escaping for `contains`
# ---------------------------------------------------------------------------


def _escape_like_pattern(value: str) -> str:
    """Escape LIKE metacharacters in *value* and wrap it in ``%`` wildcards.

    Uses backslash as the LIKE escape character (DuckDB ``ESCAPE '\\'``).
    Characters escaped: backslash, ``%``, ``_``.
    """
    value = value.replace("\\", "\\\\")  # escape the escape char first
    value = value.replace("%", "\\%")
    value = value.replace("_", "\\_")
    return f"%{value}%"


# ---------------------------------------------------------------------------
# Internal helpers — alias management
# ---------------------------------------------------------------------------


def _auto_alias(function: str, column: str) -> str:
    return f"{function.lower()}_{column}"


def _validate_alias(alias: str) -> None:
    if not alias:
        raise InvalidAliasError("Aggregation alias must not be empty.")
    if len(alias) > _MAX_ALIAS_LEN:
        raise InvalidAliasError(f"Aggregation alias exceeds {_MAX_ALIAS_LEN} characters: {alias!r}")


# ---------------------------------------------------------------------------
# Internal helpers — single filter condition fragment
# ---------------------------------------------------------------------------


def _build_condition_fragment(
    col: str,
    operator: str,
    value: str | int | float | bool | None,
    column_types: dict[str, str],
    params: list[str | int | float | bool],
) -> str:
    """Return a single WHERE-clause fragment and append any bound value to *params*."""
    _validate_column(col, column_types)
    logical_type = column_types[col]
    _validate_operator_for_type(operator, logical_type, col)

    # is_null / is_not_null must not receive a value
    if operator in _NO_VALUE_OPERATORS and value is not None:
        raise QueryBuilderError(
            f"Operator '{operator}' does not accept a value, but got: {value!r}"
        )

    # all other operators require a non-None value
    if operator in _VALUE_REQUIRED_OPERATORS and value is None:
        raise MissingValueError(
            f"Operator '{operator}' requires a non-null value, but value is None."
        )

    # contains requires a string value
    if operator == "contains" and not isinstance(value, str):
        raise ColumnTypeError(
            f"Operator 'contains' requires a string value, got {type(value).__name__!r}."
        )

    quoted_col = _quote_identifier(col)
    sql_op = _OPERATOR_SQL[operator]

    if operator in _NO_VALUE_OPERATORS:
        return f"{quoted_col} {sql_op}"

    if operator == "contains":
        # value is guaranteed str at this point
        params.append(_escape_like_pattern(str(value)))
        return f"{quoted_col} {sql_op}"

    # value is guaranteed non-None for all other operators
    params.append(value)  # type: ignore[arg-type]
    return f"{quoted_col} {sql_op}"


# ---------------------------------------------------------------------------
# Internal helpers — aggregation expression
# ---------------------------------------------------------------------------


def _build_agg_expr(function: str, quoted_col: str) -> str:
    if function == "DISTINCT_COUNT":
        return f"COUNT(DISTINCT {quoted_col})"
    sql_fn = _AGGREGATION_SQL[function]
    return f"{sql_fn}({quoted_col})"


# ---------------------------------------------------------------------------
# Public builder functions
# ---------------------------------------------------------------------------


def build_filter_query(
    request: FilterRequest,
    profile: ProfileSummary,
    max_result_rows: int = 10_000,
) -> BuiltQuery:
    """Build ``SELECT * FROM dataset WHERE … LIMIT N`` from a FilterRequest.

    All condition values are returned as positional parameters — never
    interpolated into the SQL string.
    """
    column_types = _get_column_types(profile)
    params: list[str | int | float | bool] = []
    clauses: list[str] = []

    for condition in request.conditions:
        fragment = _build_condition_fragment(
            condition.column,
            condition.operator,
            condition.value,
            column_types,
            params,
        )
        clauses.append(fragment)

    where_sql = " AND ".join(clauses)
    sql = f"SELECT * FROM {_TABLE} WHERE {where_sql} LIMIT {max_result_rows}"
    return BuiltQuery(sql=sql, parameters=params, is_limited=True)


def build_sort_query(
    request: SortRequest,
    profile: ProfileSummary,
    max_result_rows: int = 10_000,
) -> BuiltQuery:
    """Build ``SELECT * FROM dataset ORDER BY … LIMIT N`` from a SortRequest."""
    column_types = _get_column_types(profile)
    order_parts: list[str] = []

    for sort_col in request.columns:
        col = sort_col.column
        direction = sort_col.direction

        _validate_column(col, column_types)

        if direction not in _VALID_DIRECTIONS:
            raise QueryBuilderError(
                f"Invalid sort direction: {direction!r}. "
                f"Must be one of: {sorted(_VALID_DIRECTIONS)!r}"
            )

        order_parts.append(f"{_quote_identifier(col)} {direction.upper()}")

    order_sql = ", ".join(order_parts)
    sql = f"SELECT * FROM {_TABLE} ORDER BY {order_sql} LIMIT {max_result_rows}"
    return BuiltQuery(sql=sql, parameters=[], is_limited=True)


def build_aggregate_query(
    request: AggregateRequest,
    profile: ProfileSummary,
    max_result_rows: int = 10_000,
) -> BuiltQuery:
    """Build a GROUP BY / aggregation query from an AggregateRequest.

    Generated SQL shape:
    ``SELECT <group_cols>, <agg_exprs> FROM dataset [GROUP BY <group_cols>] LIMIT N``
    """
    column_types = _get_column_types(profile)
    select_parts: list[str] = []
    group_cols: list[str] = []
    seen_aliases: set[str] = set()

    for col in request.group_by:
        _validate_column(col, column_types)
        quoted = _quote_identifier(col)
        group_cols.append(quoted)
        select_parts.append(quoted)

    for spec in request.aggregations:
        _validate_column(spec.column, column_types)

        if spec.function not in _ALL_FUNCTIONS:
            raise QueryBuilderError(f"Unknown aggregation function: {spec.function!r}")

        # Determine and validate alias
        if spec.alias is not None:
            _validate_alias(spec.alias)
            alias_key = spec.alias
        else:
            alias_key = _auto_alias(spec.function, spec.column)

        if alias_key in seen_aliases:
            raise DuplicateAliasError(
                f"Duplicate aggregation alias {alias_key!r}. "
                "Provide explicit 'alias' fields to disambiguate."
            )
        seen_aliases.add(alias_key)

        quoted_col = _quote_identifier(spec.column)
        quoted_alias = _quote_identifier(alias_key)
        expr = _build_agg_expr(spec.function, quoted_col)
        select_parts.append(f"{expr} AS {quoted_alias}")

    select_sql = ", ".join(select_parts)

    if group_cols:
        group_by_sql = ", ".join(group_cols)
        sql = f"SELECT {select_sql} FROM {_TABLE} GROUP BY {group_by_sql} LIMIT {max_result_rows}"
    else:
        sql = f"SELECT {select_sql} FROM {_TABLE} LIMIT {max_result_rows}"

    return BuiltQuery(sql=sql, parameters=[], is_limited=True)


def build_describe_query(
    request: DescribeRequest,
    profile: ProfileSummary,
) -> BuiltQuery:
    """Build a single-row descriptive statistics query.

    Computes count, mean, median, std, min, max, q1, q3 for each numeric
    column.  When ``request.columns`` is None, all numeric columns in the
    profile are targeted.

    Returns one row with one column per statistic per targeted column,
    named ``<col>_<stat>`` (e.g. ``age_mean``).
    """
    column_types = _get_column_types(profile)

    if request.columns is not None:
        target_cols = list(request.columns)
        for col in target_cols:
            _validate_column(col, column_types)
            if column_types[col] != "numeric":
                raise ColumnTypeError(
                    f"Column '{col}' has type '{column_types[col]}', "
                    "but 'describe' only supports numeric columns."
                )
    else:
        target_cols = [name for name, t in column_types.items() if t == "numeric"]
        if not target_cols:
            raise QueryBuilderError(
                "No numeric columns found in this dataset. "
                "'describe' requires at least one numeric column."
            )

    select_parts: list[str] = []
    for col in target_cols:
        quoted_col = _quote_identifier(col)
        for stat_name, stat_template in _DESCRIBE_STATS:
            expr = stat_template.format(col=quoted_col)
            alias = _quote_identifier(f"{col}_{stat_name}")
            select_parts.append(f"{expr} AS {alias}")

    select_sql = ", ".join(select_parts)
    sql = f"SELECT {select_sql} FROM {_TABLE}"
    return BuiltQuery(sql=sql, parameters=[], is_limited=False)


def build_correlate_query(
    request: CorrelateRequest,
    profile: ProfileSummary,
    max_correlation_columns: int = 50,
) -> BuiltQuery:
    """Build pairwise Pearson correlation query.

    Generates one ``CORR(a, b)`` expression for each unique unordered pair
    of numeric columns.  The result alias is ``<col_a>__<col_b>``.

    When ``request.columns`` is None, all numeric columns in the profile
    are targeted.  At least 2 numeric columns are required.
    """
    column_types = _get_column_types(profile)

    if request.columns is not None:
        target_cols = list(request.columns)
        for col in target_cols:
            _validate_column(col, column_types)
            if column_types[col] != "numeric":
                raise ColumnTypeError(
                    f"Column '{col}' has type '{column_types[col]}', "
                    "but 'correlate' only supports numeric columns."
                )
    else:
        target_cols = [name for name, t in column_types.items() if t == "numeric"]

    if len(target_cols) < 2:
        raise QueryBuilderError(
            f"At least 2 numeric columns are required for correlation, but found: {target_cols!r}"
        )

    if len(target_cols) > max_correlation_columns:
        raise ResourceLimitError(
            f"Too many columns for correlation: {len(target_cols)} "
            f"(max {max_correlation_columns}). "
            "Specify a smaller subset with the 'columns' field."
        )

    # Upper-triangle pairs (i < j) — symmetric, so only compute each pair once
    select_parts: list[str] = []
    for i, col_a in enumerate(target_cols):
        for j, col_b in enumerate(target_cols):
            if i >= j:
                continue
            quoted_a = _quote_identifier(col_a)
            quoted_b = _quote_identifier(col_b)
            alias = _quote_identifier(f"{col_a}__{col_b}")
            select_parts.append(f"CORR({quoted_a}, {quoted_b}) AS {alias}")

    select_sql = ", ".join(select_parts)
    sql = f"SELECT {select_sql} FROM {_TABLE}"
    return BuiltQuery(sql=sql, parameters=[], is_limited=False)
