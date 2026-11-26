"""
Pydantic v2 schemas for the Phase 2 Deterministic Analysis Engine.

Operations supported:
  filter    — row-level filtering with structured conditions
  sort      — ordering by one or more columns
  aggregate — group-by with aggregation functions
  describe  — descriptive statistics for numeric columns
  correlate — Pearson correlation matrix for numeric columns

Execution logic lives in app/services/analysis/ (implemented in later milestones).
These schemas define the request/response contract and perform structural validation only.

Filtering semantics (v1):
  - All conditions are combined with AND.
  - Supported operators: eq, neq, gt, lt, gte, lte, contains, is_null, is_not_null.
  - is_null / is_not_null ignore the `value` field.
  - contains performs case-sensitive substring matching on string columns.
  - Numeric type compatibility is enforced by the execution layer, not here.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Operation type constants
# ---------------------------------------------------------------------------


class AnalysisOperationType:
    FILTER = "filter"
    SORT = "sort"
    AGGREGATE = "aggregate"
    DESCRIBE = "describe"
    CORRELATE = "correlate"


# ---------------------------------------------------------------------------
# Filter operation
# ---------------------------------------------------------------------------


class FilterCondition(BaseModel):
    """A single filter predicate applied to one column.

    For is_null and is_not_null operators the `value` field is ignored.
    For all other operators a non-None value is required; this is enforced
    by the query builder (Milestone 2), not here.
    """

    column: str = Field(min_length=1, max_length=255)
    operator: Literal["eq", "neq", "gt", "lt", "gte", "lte", "contains", "is_null", "is_not_null"]
    value: str | int | float | bool | None = None


class FilterRequest(BaseModel):
    """Filter rows where ALL conditions match (AND semantics, v1)."""

    operation: Literal["filter"] = "filter"
    conditions: list[FilterCondition] = Field(min_length=1, max_length=20)


# ---------------------------------------------------------------------------
# Sort operation
# ---------------------------------------------------------------------------


class SortColumn(BaseModel):
    column: str = Field(min_length=1, max_length=255)
    direction: Literal["asc", "desc"] = "asc"


class SortRequest(BaseModel):
    """Sort rows by one or more columns."""

    operation: Literal["sort"] = "sort"
    columns: list[SortColumn] = Field(min_length=1)


# ---------------------------------------------------------------------------
# Aggregate operation
# ---------------------------------------------------------------------------


class AggregationSpec(BaseModel):
    function: Literal["SUM", "AVG", "COUNT", "MIN", "MAX", "MEDIAN", "STDDEV", "DISTINCT_COUNT"]
    column: str = Field(min_length=1, max_length=255)
    alias: str | None = None


class AggregateRequest(BaseModel):
    """Group rows and compute aggregate metrics."""

    operation: Literal["aggregate"] = "aggregate"
    group_by: list[str] = Field(default_factory=list, max_length=5)
    aggregations: list[AggregationSpec] = Field(min_length=1, max_length=20)


# ---------------------------------------------------------------------------
# Describe operation
# ---------------------------------------------------------------------------


class DescribeRequest(BaseModel):
    """Compute descriptive statistics for numeric columns.

    columns=None means all numeric columns detected in the profile.
    """

    operation: Literal["describe"] = "describe"
    columns: list[str] | None = None


# ---------------------------------------------------------------------------
# Correlate operation
# ---------------------------------------------------------------------------


class CorrelateRequest(BaseModel):
    """Compute pairwise Pearson correlation for numeric columns.

    columns=None means all numeric columns detected in the profile.
    Null values are excluded pair-wise before correlation is computed.
    """

    operation: Literal["correlate"] = "correlate"
    columns: list[str] | None = None
    method: Literal["pearson"] = "pearson"


# ---------------------------------------------------------------------------
# Discriminated union — routes validation to the correct request submodel
# ---------------------------------------------------------------------------


AnalysisRequest = Annotated[
    FilterRequest | SortRequest | AggregateRequest | DescribeRequest | CorrelateRequest,
    Field(discriminator="operation"),
]

# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class AnalysisRecordResponse(BaseModel):
    """Full representation of a persisted analysis record."""

    record_id: uuid.UUID
    dataset_id: uuid.UUID
    operation: str
    parameters: dict
    result: dict | None = None
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class AnalysisListResponse(BaseModel):
    """Paginated list of analysis records for a dataset."""

    dataset_id: uuid.UUID
    records: list[AnalysisRecordResponse]
    total: int
