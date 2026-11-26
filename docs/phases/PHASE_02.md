# Phase 2 — Deterministic Analysis Engine

## Objective

Build a deterministic, SQL-backed analytical engine that can execute structured
analytical requests against an uploaded dataset without any LLM involvement.

Users submit a typed JSON request identifying the operation and its parameters.
The engine validates the request, executes it safely using DuckDB in-process,
and persists the result in PostgreSQL for retrieval.

---

## Scope

### In Scope
- Pydantic v2 request/response schemas (discriminated union on `operation` field)
- `analysis_records` PostgreSQL table with JSONB result storage
- DuckDB in-process execution (zero deployment overhead)
- Operations: `filter`, `sort`, `aggregate`, `describe`, `correlate`
- Security-first query builder: column names validated against `profile_summary`,
  values bound as SQL parameters, operators/functions validated against allow-lists
- Descriptive statistics: mean, median, std, min, max, quartiles, percentiles, count
- Correlation: Pearson only, numeric columns, pair-wise null exclusion
- Aggregation functions: SUM, AVG, COUNT, MIN, MAX, MEDIAN, STDDEV, DISTINCT_COUNT
- Result persistence and retrieval (GET previous analyses for a dataset)
- FastAPI routes nested under `/api/v1/datasets/{dataset_id}/analyses`
- Frontend analysis panel
- Documentation updates (all phase-numbering conflicts resolved)

### Out of Scope
- LLM integration (Phase 3)
- LangGraph workflows (Phase 3)
- Natural language objective parsing (Phase 3)
- Statistical hypothesis testing
- Machine learning / forecasting
- Multi-file joins
- Document ingestion

---

## Filtering Contract (v1)

Supported operators:

| Operator | Description |
|---|---|
| `eq` | Equal |
| `neq` | Not equal |
| `gt` | Greater than |
| `lt` | Less than |
| `gte` | Greater than or equal |
| `lte` | Less than or equal |
| `contains` | Case-sensitive substring (string columns only) |
| `is_null` | Column value is null (no `value` field required) |
| `is_not_null` | Column value is not null (no `value` field required) |

**v1 semantics:**
- Multiple conditions are combined with AND only. OR support is deferred.
- `contains` is case-sensitive. Case-insensitive variant deferred.
- Numeric type compatibility is enforced by the query builder (not the schema).
- Up to 20 conditions per request.

---

## Planned Endpoints

```
POST   /api/v1/datasets/{dataset_id}/analyses          Submit analysis request
GET    /api/v1/datasets/{dataset_id}/analyses          List all analyses for dataset
GET    /api/v1/datasets/{dataset_id}/analyses/{id}     Get analysis result
DELETE /api/v1/datasets/{dataset_id}/analyses/{id}     Delete analysis record
```

---

## Implementation Milestones

| # | Milestone | Deliverables |
|---|---|---|
| M1 | Schema and DB Foundation | Pydantic schemas, `AnalysisRecord` model, Alembic migration |
| M2 | Query Builder | Column validation, identifier quoting, parameterised SQL, allow-lists |
| M3 | Column Validation Layer | Validate requested columns against `profile_summary` |
| M4 | DuckDB Execution Engine | filter, sort, aggregate, describe, correlate operations |
| M5 | FastAPI Routes | 4 endpoints, result persistence, error handling |
| M6 | Frontend Analysis Panel | Request builder UI, result display |
| M7 | Documentation | All phase-numbering conflicts resolved, API spec updated |

---

## Acceptance Criteria

- [ ] All five operation types execute correctly against a profiled dataset
- [ ] Descriptive statistics match Pandas/NumPy reference values
- [ ] Pearson correlation matches NumPy reference values
- [ ] Column names and values are never interpolated into raw SQL strings
- [ ] An unknown column name returns 400, not a SQL error
- [ ] A dataset with no numeric columns returns a clear error for describe/correlate
- [ ] Results are persisted and retrievable by record ID
- [ ] Deleting a dataset cascades to its analysis records
- [ ] All CI checks pass (ruff, mypy, pytest, tsc, vitest)

---

## Resource Limits (configurable via Settings)

| Setting | Default |
|---|---|
| `max_filter_conditions` | 20 |
| `max_group_by_columns` | 5 |
| `max_aggregations_per_request` | 20 |
| `max_correlation_columns` | 50 |
| `max_analysis_result_rows` | 10 000 |

---

---

## Query Builder Architecture (Milestone 2 — Implemented)

**Location:** `apps/backend/app/services/analysis/`

### Package structure

```
app/services/analysis/
├── __init__.py
├── exceptions.py      — typed exceptions (all subclass ValueError)
└── query_builder.py   — BuiltQuery dataclass + five public build_* functions
```

### Output type

```python
@dataclass
class BuiltQuery:
    sql:        str                           # DuckDB SQL with ? placeholders
    parameters: list[str | int | float | bool]  # bound values in order
    is_limited: bool                          # True when LIMIT was added
```

### Public API

| Function | Input | Output SQL shape |
|---|---|---|
| `build_filter_query` | `FilterRequest`, `ProfileSummary` | `SELECT * FROM dataset WHERE … LIMIT N` |
| `build_sort_query` | `SortRequest`, `ProfileSummary` | `SELECT * FROM dataset ORDER BY … LIMIT N` |
| `build_aggregate_query` | `AggregateRequest`, `ProfileSummary` | `SELECT agg_exprs FROM dataset [GROUP BY …] LIMIT N` |
| `build_describe_query` | `DescribeRequest`, `ProfileSummary` | `SELECT stats… FROM dataset` |
| `build_correlate_query` | `CorrelateRequest`, `ProfileSummary` | `SELECT CORR(a, b) AS … FROM dataset` |

All functions accept an optional `max_result_rows` integer (default `10 000`).
`describe` and `correlate` are exempt — their output is bounded by column count.

### Security model

1. **Values never interpolated** — all user-supplied filter values are returned
   as `?` positional parameters.  The SQL string contains only validated
   identifiers and literal integers (LIMIT).
2. **Identifiers double-quoted** — every column name is passed through
   `_quote_identifier()` which wraps in `"` and escapes embedded `"` as `""`.
3. **Column names validated** — each referenced column is looked up in
   `ProfileSummary.columns` before being quoted; unknown columns raise
   `UnknownColumnError`.
4. **Operators from allowlist** — filter operators are checked against a
   per-logical-type `frozenset`; type-incompatible operators raise
   `ColumnTypeError`.
5. **Functions from allowlist** — aggregation functions are validated against
   `_ALL_FUNCTIONS`; unknown names raise `QueryBuilderError`.
6. **LIKE wildcard injection prevented** — `contains` values are passed through
   `_escape_like_pattern()` which escapes `\`, `%`, and `_` before wrapping the
   value in `%…%`.  The DuckDB `ESCAPE '\'` clause is emitted alongside.
7. **Sort directions from allowlist** — `asc`/`desc` validated against
   `_VALID_DIRECTIONS`; any other value raises `QueryBuilderError`.

### DuckDB table convention

The generated SQL references the table name `dataset`.  The execution layer
(M4) registers the in-memory DataFrame under that exact name via
`duckdb.register("dataset", df)` before executing the query.

### Exception hierarchy

```
QueryBuilderError (ValueError)
├── UnknownColumnError    — column not in ProfileSummary
├── ColumnTypeError       — operator/function incompatible with column type
├── MissingValueError     — operator requires a value but None was given
├── InvalidAliasError     — alias empty or exceeds 255 chars
└── DuplicateAliasError   — two specs resolve to the same output alias
```

---

## Dependencies to Add

- `duckdb>=1.1.0` — in-process SQL analytical engine (M4)

No LLM dependencies. No LangGraph. No OpenAI SDK.
