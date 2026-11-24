"""
Integration test fixtures.

Uses an in-memory SQLite database and a temporary upload directory so tests
are fully isolated from development data.
"""

import io
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — registers all models on Base
from app.database import Base, get_db
from app.main import app
from app.services.storage.local import LocalStorage


@pytest.fixture(scope="function")
def db_engine():
    # StaticPool ensures all connections share one in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    SessionLocal = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def tmp_upload_dir(tmp_path: Path) -> Path:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    return upload_dir


@pytest.fixture(scope="function")
def client(db_session, tmp_upload_dir) -> Generator[TestClient, None, None]:
    storage = LocalStorage(tmp_upload_dir)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with (
        patch("app.api.v1.routes.datasets.get_storage", return_value=storage),
        TestClient(app) as c,
    ):
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test file factories
# ---------------------------------------------------------------------------


def make_csv(content: str = "a,b,c\n1,2,3\n4,5,6\n") -> bytes:
    return content.encode("utf-8")


def make_xlsx(sheet_data: dict[str, list[list]] | None = None) -> bytes:
    """Return minimal XLSX bytes using openpyxl."""
    import openpyxl

    wb = openpyxl.Workbook()
    if sheet_data is None:
        ws = wb.active
        ws.title = "Sheet1"
        ws.append(["col1", "col2"])
        ws.append([1, 2])
        ws.append([3, 4])
    else:
        wb.remove(wb.active)
        for sheet_name, rows in sheet_data.items():
            ws = wb.create_sheet(title=sheet_name)
            for row in rows:
                ws.append(row)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
