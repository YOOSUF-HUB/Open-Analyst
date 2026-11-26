"""
Unit tests for Phase 2 analysis request/response schemas.

Verifies structural validation only — no execution logic is tested here.
"""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import TypeAdapter, ValidationError

from app.schemas.analysis import (
    AggregateRequest,
    AggregationSpec,
    AnalysisListResponse,
    AnalysisRecordResponse,
    AnalysisRequest,
    CorrelateRequest,
    DescribeRequest,
    FilterCondition,
    FilterRequest,
    SortColumn,
    SortRequest,
)

_request_adapter = TypeAdapter(AnalysisRequest)


# ---------------------------------------------------------------------------
# FilterCondition
# ---------------------------------------------------------------------------


def test_filter_condition_valid_eq():
    cond = FilterCondition(column="age", operator="eq", value=30)
    assert cond.column == "age"
    assert cond.operator == "eq"
    assert cond.value == 30


def test_filter_condition_is_null_no_value():
    cond = FilterCondition(column="score", operator="is_null")
    assert cond.value is None


def test_filter_condition_is_not_null_no_value():
    cond = FilterCondition(column="score", operator="is_not_null")
    assert cond.value is None


def test_filter_condition_contains_operator():
    cond = FilterCondition(column="name", operator="contains", value="Alice")
    assert cond.operator == "contains"
    assert cond.value == "Alice"


def test_filter_condition_invalid_operator():
    with pytest.raises(ValidationError):
        FilterCondition(column="x", operator="like")  # type: ignore[arg-type]


def test_filter_condition_empty_column_rejected():
    with pytest.raises(ValidationError):
        FilterCondition(column="", operator="eq", value=1)


# ---------------------------------------------------------------------------
# FilterRequest
# ---------------------------------------------------------------------------


def test_filter_request_valid():
    req = FilterRequest(conditions=[FilterCondition(column="city", operator="eq", value="London")])
    assert req.operation == "filter"
    assert len(req.conditions) == 1


def test_filter_request_missing_conditions_rejected():
    with pytest.raises(ValidationError):
        FilterRequest(conditions=[])


def test_filter_request_too_many_conditions_rejected():
    conditions = [FilterCondition(column="x", operator="eq", value=i) for i in range(21)]
    with pytest.raises(ValidationError):
        FilterRequest(conditions=conditions)


def test_filter_request_multiple_conditions():
    req = FilterRequest(
        conditions=[
            FilterCondition(column="age", operator="gte", value=18),
            FilterCondition(column="active", operator="eq", value=True),
        ]
    )
    assert len(req.conditions) == 2


# ---------------------------------------------------------------------------
# SortRequest
# ---------------------------------------------------------------------------


def test_sort_request_valid():
    req = SortRequest(columns=[SortColumn(column="price", direction="desc")])
    assert req.operation == "sort"
    assert req.columns[0].direction == "desc"


def test_sort_request_default_direction():
    col = SortColumn(column="name")
    assert col.direction == "asc"


def test_sort_request_empty_columns_rejected():
    with pytest.raises(ValidationError):
        SortRequest(columns=[])


def test_sort_request_multiple_columns():
    req = SortRequest(
        columns=[
            SortColumn(column="category", direction="asc"),
            SortColumn(column="revenue", direction="desc"),
        ]
    )
    assert len(req.columns) == 2


def test_sort_column_invalid_direction_rejected():
    with pytest.raises(ValidationError):
        SortColumn(column="x", direction="ASCENDING")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# AggregateRequest
# ---------------------------------------------------------------------------


def test_aggregate_request_valid_with_group_by():
    req = AggregateRequest(
        group_by=["region"],
        aggregations=[AggregationSpec(function="SUM", column="revenue")],
    )
    assert req.operation == "aggregate"
    assert req.group_by == ["region"]


def test_aggregate_request_valid_no_group_by():
    req = AggregateRequest(
        aggregations=[AggregationSpec(function="COUNT", column="id")],
    )
    assert req.group_by == []


def test_aggregate_request_too_many_group_by_rejected():
    with pytest.raises(ValidationError):
        AggregateRequest(
            group_by=["a", "b", "c", "d", "e", "f"],
            aggregations=[AggregationSpec(function="COUNT", column="id")],
        )


def test_aggregate_request_too_many_aggregations_rejected():
    aggs = [AggregationSpec(function="SUM", column=f"col{i}") for i in range(21)]
    with pytest.raises(ValidationError):
        AggregateRequest(aggregations=aggs)


def test_aggregate_request_no_aggregations_rejected():
    with pytest.raises(ValidationError):
        AggregateRequest(aggregations=[])


def test_aggregation_spec_all_functions():
    for fn in ("SUM", "AVG", "COUNT", "MIN", "MAX", "MEDIAN", "STDDEV", "DISTINCT_COUNT"):
        spec = AggregationSpec(function=fn, column="val")  # type: ignore[arg-type]
        assert spec.function == fn


def test_aggregation_spec_invalid_function_rejected():
    with pytest.raises(ValidationError):
        AggregationSpec(function="VARIANCE", column="val")  # type: ignore[arg-type]


def test_aggregation_spec_alias():
    spec = AggregationSpec(function="AVG", column="price", alias="avg_price")
    assert spec.alias == "avg_price"


# ---------------------------------------------------------------------------
# DescribeRequest
# ---------------------------------------------------------------------------


def test_describe_request_no_columns():
    req = DescribeRequest()
    assert req.operation == "describe"
    assert req.columns is None


def test_describe_request_specific_columns():
    req = DescribeRequest(columns=["age", "salary"])
    assert req.columns == ["age", "salary"]


# ---------------------------------------------------------------------------
# CorrelateRequest
# ---------------------------------------------------------------------------


def test_correlate_request_defaults():
    req = CorrelateRequest()
    assert req.operation == "correlate"
    assert req.columns is None
    assert req.method == "pearson"


def test_correlate_request_specific_columns():
    req = CorrelateRequest(columns=["a", "b", "c"])
    assert len(req.columns) == 3  # type: ignore[arg-type]


def test_correlate_request_invalid_method_rejected():
    with pytest.raises(ValidationError):
        CorrelateRequest(method="spearman")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Discriminated union — AnalysisRequest
# ---------------------------------------------------------------------------


def test_analysis_request_routes_to_filter():
    raw = {"operation": "filter", "conditions": [{"column": "x", "operator": "eq", "value": 1}]}
    req = _request_adapter.validate_python(raw)
    assert isinstance(req, FilterRequest)


def test_analysis_request_routes_to_sort():
    raw = {"operation": "sort", "columns": [{"column": "y", "direction": "desc"}]}
    req = _request_adapter.validate_python(raw)
    assert isinstance(req, SortRequest)


def test_analysis_request_routes_to_aggregate():
    raw = {
        "operation": "aggregate",
        "group_by": ["region"],
        "aggregations": [{"function": "SUM", "column": "sales"}],
    }
    req = _request_adapter.validate_python(raw)
    assert isinstance(req, AggregateRequest)


def test_analysis_request_routes_to_describe():
    raw = {"operation": "describe"}
    req = _request_adapter.validate_python(raw)
    assert isinstance(req, DescribeRequest)


def test_analysis_request_routes_to_correlate():
    raw = {"operation": "correlate"}
    req = _request_adapter.validate_python(raw)
    assert isinstance(req, CorrelateRequest)


def test_analysis_request_unknown_operation_rejected():
    with pytest.raises(ValidationError):
        _request_adapter.validate_python({"operation": "ml_predict"})


def test_analysis_request_missing_operation_rejected():
    with pytest.raises(ValidationError):
        _request_adapter.validate_python({"conditions": []})


# ---------------------------------------------------------------------------
# AnalysisRecordResponse
# ---------------------------------------------------------------------------


def _make_response(**kwargs) -> dict:
    base = {
        "record_id": uuid.uuid4(),
        "dataset_id": uuid.uuid4(),
        "operation": "describe",
        "parameters": {"operation": "describe", "columns": None},
        "result": None,
        "status": "pending",
        "error_message": None,
        "created_at": datetime.now(tz=UTC),
        "updated_at": datetime.now(tz=UTC),
        "completed_at": None,
    }
    base.update(kwargs)
    return base


def test_analysis_record_response_valid():
    resp = AnalysisRecordResponse(**_make_response())
    assert resp.status == "pending"
    assert resp.result is None


def test_analysis_record_response_with_result():
    resp = AnalysisRecordResponse(**_make_response(result={"mean": 3.5}, status="completed"))
    assert resp.result == {"mean": 3.5}


def test_analysis_record_response_uuid_round_trip():
    record_id = uuid.uuid4()
    dataset_id = uuid.uuid4()
    resp = AnalysisRecordResponse(**_make_response(record_id=record_id, dataset_id=dataset_id))
    assert resp.record_id == record_id
    assert resp.dataset_id == dataset_id


def test_analysis_record_response_string_uuid_accepted():
    # FastAPI/Pydantic coerces string UUIDs from JSON
    resp = AnalysisRecordResponse(**_make_response(record_id=str(uuid.uuid4())))
    assert isinstance(resp.record_id, uuid.UUID)


def test_analysis_list_response_valid():
    dataset_id = uuid.uuid4()
    record = AnalysisRecordResponse(**_make_response(dataset_id=dataset_id))
    listing = AnalysisListResponse(dataset_id=dataset_id, records=[record], total=1)
    assert listing.total == 1
    assert listing.records[0].dataset_id == dataset_id
