# Phase 3 — Analytical Engine

## Objective

Build the deterministic analysis execution layer. EDA, statistics, and
interactive visualizations. LLMs plan and interpret; tools calculate.

---

## Scope

### In Scope
- DuckDB integration for SQL analytics
- Pandas/Polars data processing tools
- Exploratory data analysis (distributions, correlations, outliers)
- SciPy/Statsmodels statistical tests
- Apache ECharts visualizations (rendered in frontend)
- LangGraph workflow orchestration connecting planner + tools + interpreter

### Out of Scope
- Machine learning (Phase 5)
- Forecasting (Phase 5)
- Report export (Phase 4)

---

## Implementation Tasks

- [ ] Integrate DuckDB for analytical queries
- [ ] Implement EDA tool suite (describe, correlate, distribution)
- [ ] Implement statistical test tools (t-test, chi-squared, etc.)
- [ ] Build LangGraph analysis workflow
- [ ] Add Apache ECharts frontend visualization components
- [ ] Add analysis results storage in PostgreSQL
- [ ] Wire LangGraph to execute tools and return results
- [ ] Write comprehensive tool tests (deterministic — no mocking needed)

---

## Acceptance Criteria

- [ ] EDA produces correct summary statistics (verified against known datasets)
- [ ] Correlation analysis produces correct results
- [ ] Statistical tests produce correct p-values and statistics
- [ ] All calculations are deterministic — same input always produces same output
- [ ] LLM narrates results but does not compute them
- [ ] Visualizations render correctly in the frontend
- [ ] All tests pass with no LLM calls in CI

---

## Dependencies to Add

- `duckdb` — analytical SQL engine
- `polars` — fast data processing
- `scipy` — statistical tests
- `statsmodels` — regression and time series
- `langgraph` — workflow orchestration
