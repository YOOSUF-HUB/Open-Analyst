# Phase 1 — Data Ingestion

## Objective

Allow users to upload CSV and Excel datasets. Store file metadata in PostgreSQL.
Detect column schema and perform basic profiling.

---

## Scope

### In Scope
- File upload endpoint (CSV, XLSX, XLS)
- File size and format validation
- Dataset metadata storage in PostgreSQL
- Column schema detection (name, inferred type)
- Basic dataset profiling (row count, column count, null counts)
- Dataset listing endpoint
- Dataset deletion endpoint
- Local file storage (development)

### Out of Scope
- LLM integration
- Analysis or calculation
- Authentication
- Cloud file storage (Phase 7)

---

## Planned Endpoints

```
POST   /api/v1/datasets              Upload a dataset
GET    /api/v1/datasets              List datasets
GET    /api/v1/datasets/{id}         Get dataset + profile
DELETE /api/v1/datasets/{id}         Delete dataset
```

---

## Implementation Tasks

- [ ] Add `datasets` database model
- [ ] Add Alembic migration for datasets table
- [ ] Implement file upload with validation
- [ ] Integrate Pandas for schema detection and profiling
- [ ] Add local file storage
- [ ] Implement list and delete endpoints
- [ ] Add frontend upload UI
- [ ] Add frontend dataset list view
- [ ] Write backend tests for all endpoints
- [ ] Write frontend tests for upload components

---

## Acceptance Criteria

- [ ] CSV files can be uploaded and stored
- [ ] XLSX files can be uploaded and stored
- [ ] Column names and types are detected correctly
- [ ] Row count and null statistics are computed
- [ ] Invalid files are rejected with descriptive errors
- [ ] Files exceeding size limits are rejected
- [ ] Uploaded dataset metadata persists across restarts
- [ ] All endpoints tested (happy path and error cases)
- [ ] All CI checks pass

---

## Dependencies to Add

- `pandas` — data loading and profiling
- `openpyxl` — Excel file reading
- `python-multipart` — FastAPI file upload support
