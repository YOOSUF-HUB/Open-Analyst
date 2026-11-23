import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import check_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


class ReadinessResponse(BaseModel):
    status: str
    database: str
    timestamp: str


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version="0.1.0",
        timestamp=datetime.now(UTC).isoformat(),
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness() -> ReadinessResponse:
    db_ok = check_db_connection()
    if not db_ok:
        logger.warning("Readiness check failed: database unreachable")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unavailable",
                "database": "unreachable",
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )
    return ReadinessResponse(
        status="ready",
        database="connected",
        timestamp=datetime.now(UTC).isoformat(),
    )
