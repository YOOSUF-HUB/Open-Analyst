import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# SQLite uses JSON; PostgreSQL uses JSONB. with_variant ensures Alembic
# autogenerate sees no spurious type diff when compare_type is active.
_JSON_JSONB = JSON().with_variant(JSONB(), "postgresql")


class AnalysisStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    operation: Mapped[str] = mapped_column(String(30), nullable=False)
    parameters: Mapped[dict] = mapped_column(_JSON_JSONB, nullable=False)
    result: Mapped[dict | None] = mapped_column(_JSON_JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=AnalysisStatus.PENDING)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
