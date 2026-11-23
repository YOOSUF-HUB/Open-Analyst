# Phase 2 — Conversational Analysis

## Objective

Introduce the LLM layer. Allow users to describe their analytical objectives and
ask the AI clarification questions. Manage analysis sessions.

---

## Scope

### In Scope
- LLM provider abstraction (OpenAI-compatible API)
- Analysis session creation and state management
- Natural language objective parsing
- Clarification question generation
- Session message history
- Session persistence in PostgreSQL

### Out of Scope
- Actual analysis execution (Phase 3)
- Visualizations (Phase 3)
- Report generation (Phase 4)
- Ollama local inference (Phase 6)

---

## Planned Endpoints

```
POST  /api/v1/sessions                     Create analysis session
GET   /api/v1/sessions/{id}                Get session state
POST  /api/v1/sessions/{id}/messages       Send user message
GET   /api/v1/sessions/{id}/messages       Get message history
```

---

## Implementation Tasks

- [ ] Add LLM provider abstraction interface
- [ ] Integrate OpenAI-compatible API client
- [ ] Add `analysis_sessions` and `messages` database models
- [ ] Add Alembic migrations
- [ ] Implement session creation endpoint
- [ ] Implement message send/receive endpoint
- [ ] Implement clarification question generation
- [ ] Add frontend chat interface
- [ ] Write backend tests (mock LLM responses)
- [ ] Write frontend tests for chat components

---

## Acceptance Criteria

- [ ] Sessions can be created for a dataset
- [ ] User can send a natural language objective
- [ ] LLM generates clarification questions when needed
- [ ] Session state persists across requests
- [ ] LLM calls are mocked in tests (never hit real API in CI)
- [ ] API key is read from environment variable — never hardcoded

---

## Dependencies to Add

- `langchain-openai` or direct `openai` SDK — LLM calls
- `langgraph` — workflow orchestration (initial setup)
