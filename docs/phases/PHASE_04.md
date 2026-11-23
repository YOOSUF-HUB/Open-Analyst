# Phase 4 — Reports and Follow-ups

## Objective

Generate readable AI-narrated reports from analysis results.
Support conversational follow-up questions within a session.

---

## Scope

### In Scope
- AI-generated report narratives from analysis results
- Full analysis session history (questions, results, narratives)
- Follow-up question handling (new analysis steps in existing session)
- Report export (Markdown, PDF)

### Out of Scope
- Machine learning (Phase 5)
- Authentication (later phase)

---

## Implementation Tasks

- [ ] Implement report generation workflow (LangGraph)
- [ ] Add narrative generation for each result type
- [ ] Implement follow-up question detection and routing
- [ ] Add report export (Markdown format, PDF via headless renderer)
- [ ] Add frontend report view with structured sections
- [ ] Add session history timeline in frontend

---

## Acceptance Criteria

- [ ] Generated reports accurately describe the analysis results
- [ ] Follow-up questions trigger additional analysis steps
- [ ] Exported Markdown is well-structured and readable
- [ ] Session history is complete and correctly ordered
- [ ] No numerical values are fabricated by the LLM
