# Development Roadmap

## Phase Overview

| Phase | Name | Focus | Status |
|---|---|---|---|
| 0 | Project Foundation | Infrastructure, CI, health endpoints | Complete |
| 1 | Data Ingestion | File upload, storage, schema detection | Planned |
| 2 | Conversational Analysis | LLM integration, sessions, clarification | Planned |
| 3 | Analytical Engine | EDA, statistics, visualizations | Planned |
| 4 | Reports and Follow-ups | AI narratives, follow-up questions | Planned |
| 5 | Advanced Analytics | ML, forecasting, feature analysis | Planned |
| 6 | Self-Hosted Support | Ollama, full self-hosting | Planned |
| 7 | Public Release | Cloud deployment, auth, demo | Planned |

---

## Phase 0 — Project Foundation

**Goal:** Establish a clean, production-minded foundation. No analytical features.

**Deliverables:**
- Monorepo structure
- FastAPI backend with health and readiness endpoints
- React + TypeScript + Vite frontend
- PostgreSQL + Docker Compose
- Alembic migration configuration
- GitHub Actions CI

See [phases/PHASE_00.md](phases/PHASE_00.md) for full details.

---

## Phase 1 — Data Ingestion

**Goal:** Allow users to upload CSV and Excel files and persist them.

**Deliverables:**
- File upload endpoint (CSV, XLSX, XLS)
- File validation (size limits, format detection)
- Dataset metadata storage in PostgreSQL
- Basic schema/column type detection
- Dataset listing and deletion
- File storage (local or Cloudflare R2)

See [phases/PHASE_01.md](phases/PHASE_01.md) for full details.

---

## Phase 2 — Conversational Analysis

**Goal:** Introduce the LLM layer. Allow users to describe what they want to understand.

**Deliverables:**
- LLM provider abstraction (OpenAI-compatible API)
- Analysis session management
- Natural language objective parsing
- Clarification question generation
- Session state persistence

See [phases/PHASE_02.md](phases/PHASE_02.md) for full details.

---

## Phase 3 — Analytical Engine

**Goal:** Deterministic analysis tools. EDA, statistics, visualizations.

**Deliverables:**
- DuckDB integration for SQL analytics
- Pandas/Polars data processing tools
- EDA: summary statistics, distributions, correlations
- SciPy/Statsmodels statistical tests
- Apache ECharts visualizations
- LangGraph workflow orchestration

See [phases/PHASE_03.md](phases/PHASE_03.md) for full details.

---

## Phase 4 — Reports and Follow-ups

**Goal:** Produce readable reports and support conversational follow-ups.

**Deliverables:**
- AI-generated report narratives
- Full analysis session history
- Follow-up question handling
- Result export (PDF, Markdown)

See [phases/PHASE_04.md](phases/PHASE_04.md) for full details.

---

## Phase 5 — Advanced Analytics

**Goal:** Machine learning and forecasting capabilities.

**Deliverables:**
- Classification and regression (Scikit-learn)
- Time-series forecasting
- Feature importance and model explanation
- Clustering

See [phases/PHASE_05.md](phases/PHASE_05.md) for full details.

---

## Phase 6 — Self-Hosted Support

**Goal:** Make Open Analyst fully runnable on local hardware with Ollama.

**Deliverables:**
- Ollama integration for local LLM inference
- Offline-capable Docker Compose configuration
- Self-hosting documentation

See [phases/PHASE_06.md](phases/PHASE_06.md) for full details.

---

## Phase 7 — Public Release

**Goal:** Cloud deployment, authentication, and public demo.

**Deliverables:**
- Vercel frontend deployment
- Render backend deployment
- Supabase database + authentication
- Cloudflare R2 file storage
- Public demo with rate limiting
- User API key support

See [phases/PHASE_07.md](phases/PHASE_07.md) for full details.
