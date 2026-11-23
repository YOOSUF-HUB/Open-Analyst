# Phase 0 — Project Foundation

## Objective

Establish a clean, production-minded monorepo foundation with working CI.
No analytical features are implemented in this phase.

---

## Scope

### In Scope
- Monorepo directory structure
- FastAPI backend skeleton with health endpoints
- React + TypeScript + Vite frontend
- Backend connection status indicator in frontend
- PostgreSQL local database via Docker Compose
- SQLAlchemy connectivity and Alembic migration configuration
- Docker Compose full-stack development environment
- GitHub Actions CI pipeline
- Environment variable configuration
- Project documentation

### Out of Scope
- File upload
- Dataset storage or profiling
- LLM integration of any kind
- Authentication or user accounts
- Cloud deployment
- Any analytical features

---

## Implementation Tasks

- [x] Create monorepo structure (`apps/`, `docs/`, `infrastructure/`, `scripts/`)
- [x] Set up FastAPI application with app factory pattern
- [x] Implement Pydantic settings for configuration
- [x] Add structured logging
- [x] Add global exception handler
- [x] Implement `GET /api/v1/health` endpoint
- [x] Implement `GET /api/v1/health/ready` endpoint
- [x] Configure SQLAlchemy engine and session factory
- [x] Configure Alembic migrations
- [x] Write backend pytest tests (5 tests, all passing)
- [x] Configure Ruff for linting and formatting
- [x] Set up Vite + React + TypeScript frontend
- [x] Configure Tailwind CSS v3
- [x] Set up shadcn/ui
- [x] Enable TypeScript strict mode
- [x] Implement backend connection status indicator
- [x] Write frontend Vitest tests (6 tests, all passing)
- [x] Create Docker Compose with PostgreSQL, backend, frontend services
- [x] Add named volume for PostgreSQL persistence
- [x] Add health checks to Docker services
- [x] Create `.env.example`
- [x] Create `.gitignore`
- [x] Create `CLAUDE.md`
- [x] Create `CONTRIBUTING.md`
- [x] Create all documentation files
- [x] Configure GitHub Actions CI workflow

---

## Acceptance Criteria

| Criterion | Status |
|---|---|
| Monorepo structure established | PASS |
| React frontend starts successfully | PASS |
| FastAPI backend starts successfully | PASS |
| PostgreSQL starts successfully | PASS |
| Backend connects to PostgreSQL | PASS |
| Alembic migration configuration works | PASS |
| Frontend communicates with backend | PASS |
| Health endpoint returns successful response | PASS |
| Readiness endpoint checks PostgreSQL | PASS |
| Docker Compose starts full environment | PASS |
| PostgreSQL data persists across restarts | PASS |
| Backend tests pass (5/5) | PASS |
| Frontend tests pass (6/6) | PASS |
| Ruff checks pass | PASS |
| TypeScript checks pass | PASS |
| Frontend production build succeeds | PASS |
| GitHub Actions CI configured | PASS |
| Documentation complete and accurate | PASS |
| No Phase 1+ features implemented | PASS |

---

## Testing Requirements

### Backend
- `test_health_returns_ok` — health endpoint returns 200 with correct shape
- `test_readiness_returns_ready_when_db_ok` — readiness returns 200 when DB reachable
- `test_readiness_returns_503_when_db_down` — readiness returns 503 when DB unreachable
- `test_health_response_shape` — response has exactly the right fields
- `test_readiness_response_shape_when_db_ok` — response has exactly the right fields

### Frontend
- `ConnectionStatusIndicator` renders loading, connected, connected-with-version, disconnected states
- `fetchHealth` returns data on success and throws on HTTP error
