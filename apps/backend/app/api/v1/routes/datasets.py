import logging
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.dataset import Dataset, DatasetStatus
from app.schemas.dataset import (
    DatasetMetadataResponse,
    DatasetUploadResponse,
    DeleteResponse,
    PreviewResponse,
    ProfileSummary,
    SheetSelectionRequest,
)
from app.services.ingestion.csv_reader import read_csv
from app.services.ingestion.excel_reader import (
    get_sheet_names,
    read_excel,
    validate_sheet_name,
)
from app.services.ingestion.validators import (
    validate_extension,
    validate_file_contents,
    validate_file_size,
)
from app.services.profiling.profiler import build_preview, profile_dataframe
from app.services.storage.local import get_storage

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/datasets", tags=["datasets"])


def _get_dataset_or_404(dataset_id: uuid.UUID, db: Session) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found.")
    return dataset


@router.post("/upload", status_code=201, response_model=DatasetUploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DatasetUploadResponse:
    settings = get_settings()
    storage = get_storage()

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    # Extension validation
    try:
        ext = validate_extension(file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Read file into memory (bounded by max size + 1 byte to detect oversize)
    max_bytes = settings.max_upload_size_bytes
    data = await file.read(max_bytes + 1)

    try:
        validate_file_size(len(data), max_bytes)
    except ValueError as exc:
        status_code = 413 if "exceeds" in str(exc) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc

    try:
        validate_file_contents(data, ext)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Write to temp file for storage
    storage_filename = f"{uuid.uuid4()}{ext}"
    dataset_id = uuid.uuid4()

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)

    try:
        storage_key = storage.save(tmp_path, storage_filename)
    finally:
        tmp_path.unlink(missing_ok=True)

    # Build initial DB record
    dataset = Dataset(
        id=dataset_id,
        original_filename=file.filename,
        storage_filename=storage_filename,
        file_type=ext.lstrip("."),
        file_size=len(data),
        storage_path=storage_key,
        status=DatasetStatus.UPLOADED,
    )
    db.add(dataset)
    db.flush()

    # CSV: profile immediately
    if ext == ".csv":
        try:
            df = read_csv(data, settings.max_dataset_rows, settings.max_dataset_columns)
            profile = profile_dataframe(df, file.filename, "csv")
            dataset.row_count = profile.dataset.row_count
            dataset.column_count = profile.dataset.column_count
            dataset.status = DatasetStatus.PROFILED
            dataset.profile_summary = profile.model_dump()
            db.commit()
            db.refresh(dataset)
            return DatasetUploadResponse(
                dataset_id=dataset.id,
                original_filename=dataset.original_filename,
                file_type=dataset.file_type,
                file_size=dataset.file_size,
                status=dataset.status,
                profile=profile,
                created_at=dataset.created_at,
            )
        except ValueError as exc:
            dataset.status = DatasetStatus.FAILED
            dataset.error_message = str(exc)
            db.commit()
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            dataset.status = DatasetStatus.FAILED
            dataset.error_message = "Profiling failed."
            db.commit()
            logger.exception("Unexpected error profiling CSV %s", dataset_id)
            raise HTTPException(status_code=500, detail="Failed to process dataset.") from exc

    # Excel: inspect sheets
    try:
        sheet_names = get_sheet_names(data)
    except ValueError as exc:
        dataset.status = DatasetStatus.FAILED
        dataset.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if not sheet_names:
        dataset.status = DatasetStatus.FAILED
        dataset.error_message = "Workbook contains no worksheets."
        db.commit()
        raise HTTPException(status_code=422, detail="Workbook contains no worksheets.")

    dataset.sheet_names = sheet_names

    if len(sheet_names) == 1:
        # Auto-select single sheet
        try:
            df = read_excel(
                data, sheet_names[0], settings.max_dataset_rows, settings.max_dataset_columns
            )
            profile = profile_dataframe(df, file.filename, "xlsx")
            dataset.selected_sheet = sheet_names[0]
            dataset.row_count = profile.dataset.row_count
            dataset.column_count = profile.dataset.column_count
            dataset.status = DatasetStatus.PROFILED
            dataset.profile_summary = profile.model_dump()
            db.commit()
            db.refresh(dataset)
            return DatasetUploadResponse(
                dataset_id=dataset.id,
                original_filename=dataset.original_filename,
                file_type=dataset.file_type,
                file_size=dataset.file_size,
                status=dataset.status,
                sheet_names=sheet_names,
                profile=profile,
                created_at=dataset.created_at,
            )
        except ValueError as exc:
            dataset.status = DatasetStatus.FAILED
            dataset.error_message = str(exc)
            db.commit()
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    else:
        dataset.status = DatasetStatus.NEEDS_SHEET_SELECTION
        db.commit()
        db.refresh(dataset)
        return DatasetUploadResponse(
            dataset_id=dataset.id,
            original_filename=dataset.original_filename,
            file_type=dataset.file_type,
            file_size=dataset.file_size,
            status=dataset.status,
            sheet_names=sheet_names,
            created_at=dataset.created_at,
        )


@router.post("/{dataset_id}/profile", response_model=DatasetUploadResponse)
async def select_sheet_and_profile(
    dataset_id: uuid.UUID,
    request: SheetSelectionRequest,
    db: Session = Depends(get_db),
) -> DatasetUploadResponse:
    settings = get_settings()
    storage = get_storage()
    dataset = _get_dataset_or_404(dataset_id, db)

    if dataset.file_type != "xlsx":
        raise HTTPException(status_code=400, detail="Sheet selection only applies to Excel files.")

    sheet_names: list[str] = dataset.sheet_names or []
    try:
        validate_sheet_name(request.sheet_name, sheet_names)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Re-read file from storage
    file_path = storage.get_path(dataset.storage_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Stored file not found.")

    data = file_path.read_bytes()

    try:
        df = read_excel(
            data, request.sheet_name, settings.max_dataset_rows, settings.max_dataset_columns
        )
        profile = profile_dataframe(df, dataset.original_filename, "xlsx")
    except ValueError as exc:
        dataset.status = DatasetStatus.FAILED
        dataset.error_message = str(exc)
        db.commit()
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    dataset.selected_sheet = request.sheet_name
    dataset.row_count = profile.dataset.row_count
    dataset.column_count = profile.dataset.column_count
    dataset.status = DatasetStatus.PROFILED
    dataset.profile_summary = profile.model_dump()
    db.commit()
    db.refresh(dataset)

    return DatasetUploadResponse(
        dataset_id=dataset.id,
        original_filename=dataset.original_filename,
        file_type=dataset.file_type,
        file_size=dataset.file_size,
        status=dataset.status,
        sheet_names=sheet_names,
        profile=profile,
        created_at=dataset.created_at,
    )


@router.get("/{dataset_id}", response_model=DatasetMetadataResponse)
async def get_dataset(
    dataset_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> DatasetMetadataResponse:
    dataset = _get_dataset_or_404(dataset_id, db)
    return DatasetMetadataResponse(
        dataset_id=dataset.id,
        original_filename=dataset.original_filename,
        file_type=dataset.file_type,
        file_size=dataset.file_size,
        status=dataset.status,
        selected_sheet=dataset.selected_sheet,
        sheet_names=dataset.sheet_names,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        error_message=dataset.error_message,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
    )


@router.get("/{dataset_id}/profile", response_model=ProfileSummary)
async def get_profile(
    dataset_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ProfileSummary:
    dataset = _get_dataset_or_404(dataset_id, db)
    if dataset.status != DatasetStatus.PROFILED or dataset.profile_summary is None:
        raise HTTPException(
            status_code=400,
            detail=f"Dataset is not yet profiled (status: {dataset.status}).",
        )
    return ProfileSummary.model_validate(dataset.profile_summary)


@router.get("/{dataset_id}/preview", response_model=PreviewResponse)
async def get_preview(
    dataset_id: uuid.UUID,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> PreviewResponse:
    settings = get_settings()
    storage = get_storage()
    dataset = _get_dataset_or_404(dataset_id, db)

    if dataset.status not in (DatasetStatus.PROFILED,):
        raise HTTPException(
            status_code=400,
            detail=f"Dataset is not yet profiled (status: {dataset.status}).",
        )

    file_path = storage.get_path(dataset.storage_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Stored file not found.")

    data = file_path.read_bytes()
    effective_limit = min(limit, settings.preview_limit_max)

    if dataset.file_type == "csv":
        df = read_csv(data, settings.max_dataset_rows, settings.max_dataset_columns)
    else:
        sheet = dataset.selected_sheet or (dataset.sheet_names or [None])[0]
        if not sheet:
            raise HTTPException(status_code=400, detail="No sheet selected.")
        df = read_excel(data, sheet, settings.max_dataset_rows, settings.max_dataset_columns)

    rows = build_preview(df, effective_limit)
    return PreviewResponse(
        dataset_id=dataset.id,
        columns=list(df.columns),
        rows=rows,
        total_rows=len(df),
        preview_rows=len(rows),
    )


@router.delete("/{dataset_id}", response_model=DeleteResponse)
async def delete_dataset(
    dataset_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> DeleteResponse:
    storage = get_storage()
    dataset = _get_dataset_or_404(dataset_id, db)

    # Delete file from storage
    try:
        storage.delete(dataset.storage_path)
    except Exception:
        logger.warning("Could not delete file for dataset %s", dataset_id)

    db.delete(dataset)
    db.commit()

    return DeleteResponse(message="Dataset deleted.", dataset_id=dataset_id)
