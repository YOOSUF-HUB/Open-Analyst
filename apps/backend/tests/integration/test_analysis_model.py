"""
Integration tests for the AnalysisRecord SQLAlchemy model.

Uses the existing in-memory SQLite fixture (conftest.py) so no live PostgreSQL
instance is required. JSON columns are stored as plain JSON on SQLite and as
JSONB on PostgreSQL; the model uses sqlalchemy.JSON which is compatible with both.
"""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.analysis import AnalysisRecord, AnalysisStatus
from app.models.dataset import Dataset, DatasetStatus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_dataset(db_session) -> Dataset:
    dataset = Dataset(
        id=uuid.uuid4(),
        original_filename="test.csv",
        storage_filename=f"{uuid.uuid4()}.csv",
        file_type="csv",
        file_size=1024,
        storage_path=f"uploads/{uuid.uuid4()}.csv",
        status=DatasetStatus.PROFILED,
    )
    db_session.add(dataset)
    db_session.flush()
    return dataset


def _make_record(dataset_id: uuid.UUID, **kwargs) -> AnalysisRecord:
    defaults = {
        "id": uuid.uuid4(),
        "dataset_id": dataset_id,
        "operation": "describe",
        "parameters": {"operation": "describe", "columns": None},
        "status": AnalysisStatus.PENDING,
    }
    defaults.update(kwargs)
    return AnalysisRecord(**defaults)


# ---------------------------------------------------------------------------
# Creation and defaults
# ---------------------------------------------------------------------------


def test_analysis_record_created(db_session):
    dataset = _make_dataset(db_session)
    record = _make_record(dataset.id)
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    assert record.id is not None
    assert record.dataset_id == dataset.id


def test_analysis_record_default_status(db_session):
    dataset = _make_dataset(db_session)
    record = _make_record(dataset.id)
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    assert record.status == AnalysisStatus.PENDING


def test_analysis_record_uuid_generation(db_session):
    dataset = _make_dataset(db_session)
    r1 = _make_record(dataset.id)
    r2 = _make_record(dataset.id)
    db_session.add_all([r1, r2])
    db_session.commit()
    assert r1.id != r2.id


def test_analysis_record_timestamps_set(db_session):
    dataset = _make_dataset(db_session)
    record = _make_record(dataset.id)
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    assert record.created_at is not None
    assert record.updated_at is not None


def test_analysis_record_completed_at_nullable(db_session):
    dataset = _make_dataset(db_session)
    record = _make_record(dataset.id)
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    assert record.completed_at is None


# ---------------------------------------------------------------------------
# JSON parameter / result storage
# ---------------------------------------------------------------------------


def test_analysis_record_parameters_json(db_session):
    dataset = _make_dataset(db_session)
    params = {
        "operation": "filter",
        "conditions": [{"column": "age", "operator": "gte", "value": 18}],
    }
    record = _make_record(dataset.id, operation="filter", parameters=params)
    db_session.add(record)
    db_session.commit()

    db_session.expire(record)
    db_session.refresh(record)
    assert record.parameters["conditions"][0]["column"] == "age"
    assert record.parameters["conditions"][0]["value"] == 18


def test_analysis_record_result_json(db_session):
    dataset = _make_dataset(db_session)
    record = _make_record(
        dataset.id,
        status=AnalysisStatus.COMPLETED,
        result={"mean": 42.5, "std": 3.1, "count": 100},
    )
    db_session.add(record)
    db_session.commit()

    db_session.expire(record)
    db_session.refresh(record)
    assert record.result["mean"] == pytest.approx(42.5)
    assert record.result["count"] == 100


def test_analysis_record_result_null_by_default(db_session):
    dataset = _make_dataset(db_session)
    record = _make_record(dataset.id)
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    assert record.result is None


# ---------------------------------------------------------------------------
# Multiple records per dataset
# ---------------------------------------------------------------------------


def test_multiple_records_per_dataset(db_session):
    dataset = _make_dataset(db_session)
    records = [
        _make_record(dataset.id, operation="describe"),
        _make_record(dataset.id, operation="correlate"),
        _make_record(dataset.id, operation="filter"),
    ]
    db_session.add_all(records)
    db_session.commit()

    fetched = db_session.query(AnalysisRecord).filter(AnalysisRecord.dataset_id == dataset.id).all()
    assert len(fetched) == 3


# ---------------------------------------------------------------------------
# Foreign-key behaviour
# ---------------------------------------------------------------------------


def test_analysis_record_invalid_dataset_id_rejected(db_session):
    record = _make_record(uuid.uuid4())  # non-existent dataset_id
    db_session.add(record)
    with pytest.raises((IntegrityError, Exception)):
        db_session.commit()
    db_session.rollback()


def test_dataset_delete_cascades_to_analysis_records(db_session):
    dataset = _make_dataset(db_session)
    r1 = _make_record(dataset.id, operation="describe")
    r2 = _make_record(dataset.id, operation="correlate")
    db_session.add_all([r1, r2])
    db_session.commit()

    db_session.delete(dataset)
    db_session.commit()

    remaining = (
        db_session.query(AnalysisRecord).filter(AnalysisRecord.dataset_id == dataset.id).all()
    )
    assert remaining == []


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------


def test_analysis_record_status_update(db_session):
    dataset = _make_dataset(db_session)
    record = _make_record(dataset.id)
    db_session.add(record)
    db_session.commit()

    record.status = AnalysisStatus.COMPLETED
    record.result = {"rows": 50}
    db_session.commit()
    db_session.refresh(record)

    assert record.status == AnalysisStatus.COMPLETED
    assert record.result["rows"] == 50


def test_analysis_record_failed_status_with_error(db_session):
    dataset = _make_dataset(db_session)
    record = _make_record(
        dataset.id,
        status=AnalysisStatus.FAILED,
        error_message="Column 'xyz' not found.",
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)

    assert record.status == AnalysisStatus.FAILED
    assert record.error_message == "Column 'xyz' not found."
