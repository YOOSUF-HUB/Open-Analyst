# API Specification

## Conventions

- **Base URL:** `/api/v1`
- **Content-Type:** `application/json`
- **Timestamps:** ISO 8601 with UTC timezone (`2024-01-01T12:00:00+00:00`)
- **Errors:** Standard FastAPI/Pydantic error format with `detail` field

### Error Response Shape

```json
{
  "detail": "Human-readable error message"
}
```

Validation errors return a list of objects:
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "missing"
    }
  ]
}
```

---

## Health Endpoints

### GET /api/v1/health

Returns basic API health information. Always returns 200 when the backend is running.

**Response 200:**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "timestamp": "2024-01-01T12:00:00+00:00"
}
```

**Fields:**
| Field | Type | Description |
|---|---|---|
| status | string | Always `"ok"` |
| version | string | Application version |
| timestamp | string | ISO 8601 UTC timestamp |

---

### GET /api/v1/health/ready

Checks whether the backend can successfully communicate with PostgreSQL.
Returns 200 if ready, 503 if the database is unavailable.

**Response 200:**
```json
{
  "status": "ready",
  "database": "connected",
  "timestamp": "2024-01-01T12:00:00+00:00"
}
```

**Response 503:**
```json
{
  "detail": {
    "status": "unavailable",
    "database": "unreachable",
    "timestamp": "2024-01-01T12:00:00+00:00"
  }
}
```

**Fields:**
| Field | Type | Description |
|---|---|---|
| status | string | `"ready"` or `"unavailable"` |
| database | string | `"connected"` or `"unreachable"` |
| timestamp | string | ISO 8601 UTC timestamp |

---

## Development API Docs

When `ENVIRONMENT=development` (the default), interactive API documentation is available:

- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc
- **OpenAPI JSON:** http://localhost:8000/api/openapi.json

API docs are disabled in production (`ENVIRONMENT=production`).

---

## Future Endpoints (Planned)

The following endpoints are planned but not yet implemented.
Do not implement until the relevant phase begins.

### Phase 1 — Data Ingestion

```
POST /api/v1/datasets          Upload a dataset (CSV/Excel)
GET  /api/v1/datasets          List uploaded datasets
GET  /api/v1/datasets/{id}     Get dataset metadata
DELETE /api/v1/datasets/{id}   Delete a dataset
```

### Phase 2 — Analysis Sessions

```
POST /api/v1/sessions          Start an analysis session
GET  /api/v1/sessions/{id}     Get session status
POST /api/v1/sessions/{id}/messages  Send a message
GET  /api/v1/sessions/{id}/results   Get analysis results
```
