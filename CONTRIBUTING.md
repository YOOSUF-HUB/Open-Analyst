# Contributing to Open Analyst

Thank you for your interest in contributing.

---

## Development Setup

### Prerequisites

- Python 3.11+ 
- Node.js 20+
- npm 9+
- Docker and Docker Compose (for the full stack)
- Git

### Backend

```bash
cd apps/backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate         # Windows

# Install dependencies (including dev tools)
pip install -e ".[dev]"

# Run the development server
uvicorn app.main:app --reload
# API available at http://localhost:8000
# Interactive docs at http://localhost:8000/api/docs
```

### Frontend

```bash
cd apps/frontend

# Install dependencies
npm install

# Run the development server
npm run dev
# App available at http://localhost:5173
```

### Full Stack with Docker Compose

```bash
# From the repository root
cp .env.example .env

docker compose up --build
```

---

## Environment Variables

Copy `.env.example` to `.env` and adjust values for local development.
See comments in `.env.example` for descriptions of each variable.

Never commit `.env` to version control.

---

## Running Tests

### Backend

```bash
cd apps/backend
source .venv/bin/activate

pytest tests/ -v
```

### Frontend

```bash
cd apps/frontend

npm test
```

---

## Code Quality

### Backend

```bash
# Lint
ruff check app/ tests/

# Format
ruff format app/ tests/

# Check format without modifying
ruff format --check app/ tests/
```

### Frontend

```bash
# TypeScript type check
npx tsc --noEmit
```

All CI checks must pass before merging.

---

## Database Migrations

After modifying SQLAlchemy models, generate and apply a migration:

```bash
cd apps/backend
source .venv/bin/activate

# Autogenerate migration
alembic revision --autogenerate -m "describe the change"

# Apply migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1
```

---

## Branching Conventions

| Branch | Purpose |
|---|---|
| `main` | Stable, deployable code |
| `feature/<name>` | New features |
| `fix/<name>` | Bug fixes |
| `chore/<name>` | Maintenance, deps, refactors |
| `docs/<name>` | Documentation only |

Base branches off `main`. Open a pull request against `main`.

---

## Pull Request Guidelines

1. Keep PRs focused on a single concern.
2. All CI checks must pass.
3. Include a description of what changed and why.
4. Reference any related issues.
5. Update documentation if the change affects architecture or APIs.

---

## Phase Boundaries

Before implementing a feature, check [docs/DEVELOPMENT_ROADMAP.md](docs/DEVELOPMENT_ROADMAP.md)
to confirm which phase it belongs to. Do not introduce features beyond the active phase.
