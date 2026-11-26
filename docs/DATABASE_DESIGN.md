# Database Design

## Current State

PostgreSQL 16 running via Docker Compose.
Backend connects via SQLAlchemy (psycopg2).
Alembic manages all schema changes.

**Connection:** Configured via environment variables:
```
POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
```

An explicit `DATABASE_URL` environment variable overrides all individual settings.

---

## Migration Strategy

All schema changes are tracked as Alembic migration files.

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "describe the change"

# Apply all pending migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1
```

Migration files live in `apps/backend/alembic/versions/`.
They are committed to version control and applied in order.

---

## Phase 1 — Implemented

### datasets

Stores metadata about every uploaded file and its profiling result.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key, auto-generated |
| original_filename | VARCHAR(255) | User-supplied filename |
| storage_filename | VARCHAR(255) | UUID-prefixed filename on disk (unique) |
| file_type | VARCHAR(10) | `csv` or `xlsx` |
| file_size | INTEGER | Bytes |
| storage_path | VARCHAR(512) | Key within the storage backend |
| selected_sheet | VARCHAR(255) | Active sheet for Excel files (nullable) |
| sheet_names | JSONB | All sheet names for Excel files (nullable) |
| row_count | INTEGER | Set after profiling (nullable) |
| column_count | INTEGER | Set after profiling (nullable) |
| status | VARCHAR(30) | `UPLOADED` / `NEEDS_SHEET_SELECTION` / `PROFILED` / `FAILED` |
| profile_summary | JSONB | Full `ProfileSummary` model dump (nullable) |
| error_message | TEXT | Set on failure (nullable) |
| created_at | TIMESTAMP WITH TIME ZONE | Set by DB default |
| updated_at | TIMESTAMP WITH TIME ZONE | Set by DB default; updated on every change |

**Migration:** `a100747e3090_add_datasets_table.py`

---

## Phase 2 — Implemented (Milestone 1)

### analysis_records

Persists every deterministic analysis request and its result.
One dataset may have many analysis records.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key, auto-generated |
| dataset_id | UUID | Foreign key → datasets.id ON DELETE CASCADE, indexed |
| operation | VARCHAR(30) | `filter` / `sort` / `aggregate` / `describe` / `correlate` |
| parameters | JSONB | Full validated request (operation + params) |
| result | JSONB | Structured result payload (nullable until completed) |
| status | VARCHAR(20) | `pending` / `running` / `completed` / `failed` |
| error_message | TEXT | Set on failure (nullable) |
| created_at | TIMESTAMP WITH TIME ZONE | Set by DB default |
| completed_at | TIMESTAMP WITH TIME ZONE | Set when status → completed (nullable) |
| updated_at | TIMESTAMP WITH TIME ZONE | Set by DB default; updated on every change |

**Cascade:** Deleting a dataset deletes all associated analysis records.

**Migration:** `c3d4e5f60781_add_analysis_records_table.py`

---

## Data Persistence

PostgreSQL data is persisted via a Docker named volume (`postgres_data`).
Data survives container restarts and rebuilds.

To reset the database (destroy all data):
```bash
docker compose down -v
```
