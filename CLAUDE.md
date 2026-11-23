# Open Analyst — CLAUDE.md

This file is the authoritative guide for Claude Code sessions on this project.
Read it fully before making changes.

---

## Product Context

Open Analyst is an open-source AI Data Analyst that allows users to upload datasets,
describe their analytical objectives in natural language, and receive statistics,
visualizations, insights, and reports from an AI-driven analysis pipeline.

Target users: data analysts, researchers, business intelligence teams, and
anyone who needs to extract insights from structured data without writing code.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript (strict), Vite, Tailwind CSS v3, shadcn/ui |
| Backend | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x |
| Database | PostgreSQL 16 |
| Migrations | Alembic |
| Package manager (backend) | pip / pyproject.toml |
| Package manager (frontend) | npm |
| Linting/formatting (backend) | Ruff |
| Testing (backend) | pytest, httpx2 |
| Testing (frontend) | Vitest, React Testing Library |
| Infrastructure | Docker, Docker Compose |
| CI | GitHub Actions |

---

## Repository Structure

```
open-analyst/
├── apps/
│   ├── frontend/           # React + Vite + TypeScript application
│   └── backend/            # FastAPI application
├── docs/
│   ├── PROJECT_OVERVIEW.md
│   ├── ARCHITECTURE.md
│   ├── DATABASE_DESIGN.md
│   ├── API_SPECIFICATION.md
│   ├── DEVELOPMENT_ROADMAP.md
│   └── phases/             # Phase-by-phase scope documents
├── infrastructure/
│   └── docker/             # Additional Docker configs (future)
├── scripts/                # Development helper scripts (future)
├── .github/
│   └── workflows/ci.yml    # GitHub Actions CI
├── compose.yaml            # Docker Compose (development)
├── .env.example            # Environment variable template
└── CLAUDE.md               # This file
```

---

## Architecture Overview

**Frontend** (`apps/frontend/src/`):
- `components/` — Reusable UI components
- `components/ui/` — shadcn/ui base components
- `lib/` — Shared utilities (e.g., `cn()` helper)
- `pages/` — Page-level components
- `services/` — API client functions
- `test/` — Vitest test files

**Backend** (`apps/backend/app/`):
- `main.py` — FastAPI application factory
- `config.py` — Pydantic settings (environment-driven)
- `database.py` — SQLAlchemy engine, session, Base, DB check
- `logging_config.py` — Structured logging setup
- `exceptions.py` — Global exception handlers
- `api/v1/router.py` — API v1 router aggregation
- `api/v1/routes/` — Individual route modules
- `models/` — SQLAlchemy ORM models (future)

**API versioning:** All endpoints are under `/api/v1`.

**CORS:** Configured via `CORS_ORIGINS` environment variable (comma-separated).

---

## Development Commands

### Backend

```bash
cd apps/backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Run dev server
uvicorn app.main:app --reload

# Tests
pytest tests/ -v

# Lint / format
ruff check app/ tests/
ruff format app/ tests/

# Migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### Frontend

```bash
cd apps/frontend
npm install

# Run dev server
npm run dev

# Tests
npm test

# TypeScript check
npx tsc --noEmit

# Production build
npm run build
```

### Docker Compose

```bash
# Copy and configure environment
cp .env.example .env

# Start everything
docker compose up --build

# Start in background
docker compose up --build -d

# View logs
docker compose logs -f backend

# Stop
docker compose down

# Stop and remove volumes (deletes database)
docker compose down -v
```

---

## Coding Conventions

### Python
- Type-annotated function signatures required.
- Use `from __future__ import annotations` only when needed.
- Prefer `collections.abc` over `typing` for generic types (Python 3.10+).
- Pydantic v2 models for all API request/response schemas.
- Never use `Any` without justification.
- One module = one concern.
- Ruff enforces formatting and import order — run before committing.

### TypeScript / React
- Strict mode — no `any`, no non-null assertions without justification.
- Named exports preferred over default exports (except pages).
- Component files: PascalCase. Utility files: camelCase.
- Use `cn()` from `@/lib/utils` for conditional class composition.
- Path alias `@/` resolves to `src/`.

### General
- Never commit secrets or `.env` files.
- Never hardcode credentials.
- Error handling must be explicit — no silent catches.
- Comments only when the WHY is non-obvious.

---

## Testing Requirements

### Backend
- Tests in `apps/backend/tests/`.
- Use `pytest` with `TestClient` (via `httpx2`).
- Mock external dependencies (e.g., database) in unit tests.
- Required: test all API endpoints, happy path and error cases.

### Frontend
- Tests in `apps/frontend/src/test/`.
- Use Vitest + React Testing Library.
- Required: test UI components and API service functions.

---

## Security Requirements

- Never expose secrets through API responses or logs.
- CORS origins must be explicitly configured — no wildcard `*` in production.
- All inputs validated via Pydantic before processing.
- SQL queries must go through SQLAlchemy ORM — never raw string interpolation.
- No `eval()`, `exec()`, or dynamic code execution.
- Dependencies must be pinned.

---

## Phase Boundaries

**Implemented (Phase 0):**
- Monorepo structure
- FastAPI backend with health endpoints
- React frontend with backend connection status
- PostgreSQL + Docker Compose
- Alembic migration configuration
- CI pipeline

**NOT implemented yet — do not add prematurely:**
- File upload (Phase 1)
- Dataset profiling (Phase 1)
- LLM integration (Phase 2+)
- LangGraph workflows (Phase 3+)
- Authentication (Phase 4+)
- Cloud deployment (Phase 7+)

Before starting any new feature, verify which phase it belongs to and confirm
Phase 0 acceptance criteria are still met.

---

## Rules for Claude Code Sessions

1. Read this file at the start of every session.
2. Inspect existing code before writing new code.
3. Run tests before declaring any task complete.
4. Run `ruff check` and `ruff format --check` before committing backend changes.
5. Run `tsc --noEmit` before committing frontend changes.
6. Never implement features beyond the current phase boundary.
7. Document any architectural deviations in `docs/ARCHITECTURE.md`.
8. Update `docs/API_SPECIFICATION.md` when adding or changing endpoints.
9. Create Alembic migrations for all database schema changes.
10. Verify Docker Compose starts cleanly after infrastructure changes.
