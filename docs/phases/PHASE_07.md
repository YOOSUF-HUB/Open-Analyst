# Phase 7 — Public Release

## Objective

Deploy Open Analyst as a publicly accessible cloud-hosted service with authentication,
rate limiting, and a free demo tier.

---

## Scope

### In Scope
- Vercel frontend deployment
- Render backend deployment
- Supabase PostgreSQL + authentication
- Cloudflare R2 file storage
- Cloudflare Turnstile bot protection
- Cloudflare Worker for scheduled file cleanup
- Public demo with rate limiting
- User account support
- Bring-your-own-API-key support
- Production CI/CD deployment pipeline

### Out of Scope
- Enterprise features
- Multi-tenancy

---

## Implementation Tasks

- [ ] Add Supabase authentication (email, OAuth)
- [ ] Migrate file storage to Cloudflare R2
- [ ] Configure Render backend deployment
- [ ] Configure Vercel frontend deployment
- [ ] Implement Cloudflare Turnstile on upload forms
- [ ] Add Cloudflare Worker for temporary file cleanup
- [ ] Add rate limiting middleware
- [ ] Add user API key management
- [ ] Create production Docker Compose for self-hosters
- [ ] Create deployment documentation

---

## Acceptance Criteria

- [ ] Application is accessible at a public URL
- [ ] Authentication works (sign up, sign in, sign out)
- [ ] File uploads are stored in R2 and cleaned up after expiry
- [ ] Demo tier rate limits are enforced
- [ ] Bot protection is active on public forms
- [ ] Self-hosted Docker Compose remains functional
- [ ] No secrets in environment or code

---

## Infrastructure Summary

| Service | Purpose |
|---|---|
| Vercel | Frontend (CDN + serverless) |
| Render | Backend (Python container) |
| Supabase | PostgreSQL + Auth |
| Cloudflare R2 | File storage |
| Cloudflare Turnstile | Bot protection |
| Cloudflare Worker | Scheduled cleanup |
