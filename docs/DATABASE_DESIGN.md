# Database Design

## Current State (Phase 0)

PostgreSQL 16 is running and the backend connects successfully via SQLAlchemy.
Alembic is configured for migrations. No application tables exist yet.

**Connection:** Configured via environment variables:
```
POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
```

The backend builds the connection URL from these variables at startup.
An explicit `DATABASE_URL` environment variable can override all individual settings.

---

## Migration Strategy

All schema changes must be tracked as Alembic migration files.

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

## Planned Entities (Phase 1+)

The following entities are planned but not yet implemented.
Do not create these models until the relevant phase begins.

### datasets

Stores metadata about uploaded files.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| filename | TEXT | Original uploaded filename |
| file_size | BIGINT | File size in bytes |
| row_count | INTEGER | Number of rows (after profiling) |
| column_count | INTEGER | Number of columns |
| created_at | TIMESTAMP WITH TIME ZONE | Upload time |
| storage_key | TEXT | Storage reference (R2 key or local path) |

### analysis_sessions

Tracks a user's conversational analysis session.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| dataset_id | UUID | Foreign key → datasets |
| objective | TEXT | User's stated analytical objective |
| status | TEXT | pending / running / completed / failed |
| created_at | TIMESTAMP WITH TIME ZONE | |
| completed_at | TIMESTAMP WITH TIME ZONE | Nullable |

### analysis_results

Stores individual analytical results within a session.

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| session_id | UUID | Foreign key → analysis_sessions |
| result_type | TEXT | statistic / visualization / insight |
| content | JSONB | Result payload |
| created_at | TIMESTAMP WITH TIME ZONE | |

---

## Data Persistence

PostgreSQL data is persisted via a Docker named volume (`postgres_data`).
Data survives container restarts and rebuilds.

To reset the database (destroy all data):
```bash
docker compose down -v
```
