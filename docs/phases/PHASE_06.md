# Phase 6 — Self-Hosted Support

## Objective

Make Open Analyst fully runnable on local hardware using Ollama for LLM inference.
No external API keys required.

---

## Scope

### In Scope
- Ollama integration via OpenAI-compatible API
- Automatic detection of available local models
- Self-hosting Docker Compose configuration (includes Ollama service)
- Self-hosting documentation
- Configuration to switch between cloud and local inference

### Out of Scope
- Fine-tuning or custom model training
- GPU orchestration

---

## Implementation Tasks

- [ ] Add Ollama service to Docker Compose
- [ ] Configure LLM provider to auto-detect Ollama
- [ ] Add `OLLAMA_BASE_URL` and `OLLAMA_MODEL` environment variables
- [ ] Test analysis workflows with open-source models (e.g., Llama, Mistral)
- [ ] Document self-hosting setup (hardware requirements, model recommendations)
- [ ] Create self-hosted `.env.example.selfhosted`

---

## Acceptance Criteria

- [ ] Full analysis workflow completes using Ollama local inference
- [ ] No external API keys required in self-hosted mode
- [ ] `docker compose up` starts Ollama alongside all services
- [ ] Model selection is configurable via environment variable
- [ ] Self-hosting documentation is clear and accurate
