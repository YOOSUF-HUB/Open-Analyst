import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# SQLite uses JSON; PostgreSQL uses JSONB. with_variant ensures Alembic
# autogenerate sees no spurious type diff when compare_type is active.
_JSON_JSONB = JSON().with_variant(JSONB(), "postgresql")


class DatasetStatus:
    UPLOADED = "UPLOADED"
    NEEDS_SHEET_SELECTION = "NEEDS_SHEET_SELECTION"
    PROFILED = "PROFILED"
    FAILED = "FAILED"


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    selected_sheet: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sheet_names: Mapped[list | None] = mapped_column(_JSON_JSONB, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=DatasetStatus.UPLOADED)
    profile_summary: Mapped[dict | None] = mapped_column(_JSON_JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
