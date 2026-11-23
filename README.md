# Open Analyst

Open-source AI Data Analyst — turn raw data into meaningful insights using conversational AI.

## What is Open Analyst?

Open Analyst lets you upload datasets, describe what you want to understand, and receive
statistics, visualizations, and plain-language insights — all without writing code.

Powered by deterministic analytical tools and guided by an LLM-based orchestration layer,
Open Analyst keeps numerical results accurate while making analysis accessible to everyone.

## Status

**Phase 0 — Project Foundation** (current)

The project foundation is in place. The core stack (FastAPI, React, PostgreSQL) is running.
Analysis features will be introduced in Phase 1 and beyond.

See [docs/DEVELOPMENT_ROADMAP.md](docs/DEVELOPMENT_ROADMAP.md) for the full roadmap.

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- Git

### Run with Docker Compose

```bash
# Clone the repository
git clone https://github.com/yoosufahamed/Open-Analyst.git
cd Open-Analyst

# Configure environment
cp .env.example .env
# Edit .env if you want to change default credentials

# Start the full development environment
docker compose up --build
```

The application will be available at:
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API docs (dev):** http://localhost:8000/api/docs

### Run Without Docker

See [CONTRIBUTING.md](CONTRIBUTING.md) for local development setup instructions.

## Project Structure

```
open-analyst/
├── apps/
│   ├── frontend/   # React + TypeScript + Vite
│   └── backend/    # Python + FastAPI
├── docs/           # Architecture and design documentation
├── infrastructure/ # Docker and infrastructure configs
├── scripts/        # Developer helper scripts
└── compose.yaml    # Docker Compose development environment
```

## Documentation

| Document | Description |
|---|---|
| [PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md) | Product vision and roadmap summary |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture |
| [DATABASE_DESIGN.md](docs/DATABASE_DESIGN.md) | Database design |
| [API_SPECIFICATION.md](docs/API_SPECIFICATION.md) | API reference |
| [DEVELOPMENT_ROADMAP.md](docs/DEVELOPMENT_ROADMAP.md) | Development phases |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guide |
| [CLAUDE.md](CLAUDE.md) | AI assistant context (for Claude Code) |

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy |
| Database | PostgreSQL |
| Infrastructure | Docker, Docker Compose |
| CI | GitHub Actions |

## License

Licensed under the [Apache License 2.0](LICENSE).
