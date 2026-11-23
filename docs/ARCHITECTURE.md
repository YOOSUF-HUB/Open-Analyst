# Architecture

## Overview

Open Analyst is a monorepo containing a React frontend and a FastAPI backend,
communicating over HTTP. PostgreSQL provides persistent storage.

```
┌─────────────────────┐         ┌─────────────────────┐
│   Browser           │  HTTP   │   FastAPI Backend   │
│   React + Vite      │◄───────►│   Python 3.11+      │
│   Port 5173         │         │   Port 8000         │
└─────────────────────┘         └──────────┬──────────┘
                                           │ SQLAlchemy
                                ┌──────────▼──────────┐
                                │   PostgreSQL 16      │
                                │   Port 5432          │
                                └─────────────────────┘
```

---

## Frontend Architecture

**Technology:** React 18, TypeScript (strict), Vite, Tailwind CSS v3, shadcn/ui

**Directory structure:**
```
apps/frontend/src/
├── components/       # Reusable UI components
│   └── ui/           # shadcn/ui primitives (Badge, Button, etc.)
├── lib/              # Shared utilities
│   └── utils.ts      # cn() helper for class composition
├── pages/            # Page-level components (one per route, future)
├── services/         # API client functions
└── test/             # Vitest tests
```

**Key decisions:**
- Path alias `@/` resolves to `src/` for clean imports.
- TypeScript strict mode — no implicit `any`.
- Tailwind CSS CSS variables for theming (dark mode compatible).
- API base URL read from `VITE_API_BASE_URL` environment variable.

**Future additions:**
- React Router for multi-page navigation (Phase 2+).
- Global state management (TBD — likely Zustand or React Query) (Phase 2+).
- Apache ECharts for data visualizations (Phase 3+).

---

## Backend Architecture

**Technology:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic

**Directory structure:**
```
apps/backend/app/
├── main.py           # App factory, middleware, lifespan
├── config.py         # Pydantic settings (all env vars)
├── database.py       # Engine, session factory, Base, health check
├── logging_config.py # Structured stdout logging
├── exceptions.py     # Global exception handler
├── api/
│   └── v1/
│       ├── router.py         # Aggregates all v1 routers
│       └── routes/
│           └── health.py     # /api/v1/health, /api/v1/health/ready
└── models/           # SQLAlchemy ORM models (future)
```

**Key decisions:**
- Configuration via Pydantic `BaseSettings` — reads from environment variables and `.env`.
- API versioning via URL prefix `/api/v1`.
- CORS origins are configurable via environment variable (comma-separated).
- Database connection check on readiness endpoint (`/api/v1/health/ready`).
- Lifespan context manager replaces deprecated `on_event`.

**Future additions:**
- Dataset models and repositories (Phase 1+).
- LangGraph workflow orchestration (Phase 3+).
- File upload endpoints with Cloudflare R2 (Phase 7+).
- Authentication middleware (Phase 4+).

---

## Database Architecture

**Technology:** PostgreSQL 16, SQLAlchemy 2.x (ORM), Alembic (migrations)

**Current state:** Connectivity established, no application tables yet.

**Migration approach:** Alembic autogenerate from SQLAlchemy models.
All schema changes must be tracked as versioned migration files.

**Future entities (planned, not yet implemented):**
- `datasets` — uploaded file metadata
- `analysis_sessions` — conversational analysis sessions
- `analysis_results` — stored results and visualizations

See [DATABASE_DESIGN.md](DATABASE_DESIGN.md) for detailed entity design.

---

## Communication

**Frontend → Backend:** HTTP REST over `VITE_API_BASE_URL` (default: `http://localhost:8000`).

**Backend → Database:** SQLAlchemy connection pool (pool_size=5, max_overflow=10).
Connection string built from `POSTGRES_*` environment variables.

**Inter-service (Docker):** Services communicate via Docker Compose service names
(e.g., backend connects to `postgres:5432`).

---

## Future AI Orchestration Architecture (Phase 3+)

The planned architecture keeps LLMs in the planning and interpretation layer
only — all numerical calculations are performed by deterministic tools.

```
User Message
     │
     ▼
LangGraph Orchestrator
     │
     ├─── Planner LLM (plan analysis steps)
     │
     ├─── Tool Executor
     │         ├── DuckDB (SQL analytics)
     │         ├── Pandas / Polars (data wrangling)
     │         ├── SciPy / Statsmodels (statistics)
     │         └── Scikit-learn (machine learning)
     │
     └─── Interpreter LLM (explain results in natural language)
```

LLM providers will be abstracted behind a common interface supporting:
- OpenAI-compatible APIs
- Ollama (local inference)

---

## Future Cloud Architecture (Phase 7+)

| Component | Service |
|---|---|
| Frontend hosting | Vercel |
| Backend hosting | Render |
| Database | Supabase (PostgreSQL) |
| File storage | Cloudflare R2 |
| Bot protection | Cloudflare Turnstile |
| Scheduled cleanup | Cloudflare Worker |

Phase 0–6 uses local Docker Compose only.
