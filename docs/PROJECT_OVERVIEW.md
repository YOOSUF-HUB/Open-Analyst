# Project Overview

## What is Open Analyst?

Open Analyst is an open-source AI Data Analyst. It lets users upload datasets, describe their
analytical objectives in natural language, and receive statistics, visualizations, insights,
and reports — without writing code.

The system uses an LLM-based orchestration layer to plan and interpret analysis, while
all numerical calculations are performed by deterministic Python tools to guarantee accuracy.

---

## Target Users

- **Data analysts** who want to accelerate exploratory analysis.
- **Business intelligence teams** who need fast answers from operational data.
- **Researchers** working with structured datasets.
- **Non-technical stakeholders** who need insights from data without engineering support.

---

## Product Capabilities (Planned)

| Capability | Phase |
|---|---|
| CSV and Excel upload | 1 |
| Dataset profiling and schema inference | 1 |
| Conversational analysis objectives | 2 |
| Exploratory data analysis | 2 |
| Statistical analysis | 3 |
| Machine learning (classification, regression) | 5 |
| Forecasting | 5 |
| Interactive visualizations | 3 |
| Natural language reports | 4 |
| Follow-up questions | 4 |
| Self-hosted deployment (Ollama) | 6 |
| Cloud-hosted demo | 7 |

---

## Version Roadmap

### v0.1 — Project Foundation (Phase 0)
Monorepo, FastAPI backend, React frontend, PostgreSQL, Docker Compose, CI pipeline.
No analytical features.

### v0.2 — Data Ingestion (Phase 1)
CSV and Excel file upload, dataset storage, schema detection, basic profiling.

### v0.3 — Conversational Analysis (Phase 2)
LLM integration, natural language objectives, clarification questions, session management.

### v0.4 — Analytical Engine (Phase 3)
Deterministic calculation tools, EDA, statistics, visualizations via ECharts.

### v0.5 — Reports and Follow-ups (Phase 4)
AI-generated report narratives, follow-up question handling, full analysis sessions.

### v0.6 — Advanced Analytics (Phase 5)
Machine learning, regression, classification, forecasting, feature importance.

### v0.7 — Self-Hosted Support (Phase 6)
Ollama local inference support, self-hosted Docker Compose deployment.

### v1.0 — Public Release (Phase 7)
Cloud deployment (Vercel + Render + Supabase), public demo, authentication, API key support.

---

## Open Source

Open Analyst is released under the Apache License 2.0.
Contributions are welcome — see [CONTRIBUTING.md](../CONTRIBUTING.md).
