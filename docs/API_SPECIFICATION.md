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

## Phase 1 Endpoints (Implemented)

### POST /api/v1/datasets/upload

Upload a CSV or Excel file. Profiles the dataset immediately (CSV and
single-sheet Excel). Multi-sheet Excel returns `NEEDS_SHEET_SELECTION`.

### POST /api/v1/datasets/{id}/profile

Select a sheet and profile a multi-sheet Excel dataset.

### GET /api/v1/datasets/{id}

Get dataset metadata (status, row/column counts, sheet names, error).

### GET /api/v1/datasets/{id}/profile

Get the full `ProfileSummary` for a profiled dataset.

### GET /api/v1/datasets/{id}/preview

Get a preview of dataset rows (default 100, max 500 via `?limit=`).

### DELETE /api/v1/datasets/{id}

Delete a dataset and its stored file. Cascades to all analysis records.

---

## Phase 2 Endpoints (Planned — Milestone 5)

Analysis requests are nested under their parent dataset. All endpoints
require the dataset to exist; non-existent `dataset_id` returns 404.

### POST /api/v1/datasets/{dataset_id}/analyses

Submit an analysis request. The request body is a discriminated JSON object
with an `operation` field that routes to the correct schema.

**Request body** (examples):

```json
{ "operation": "describe" }

{ "operation": "describe", "columns": ["age", "salary"] }

{
  "operation": "filter",
  "conditions": [
    { "column": "age", "operator": "gte", "value": 18 },
    { "column": "active", "operator": "eq", "value": true }
  ]
}

{
  "operation": "aggregate",
  "group_by": ["region"],
  "aggregations": [
    { "function": "SUM", "column": "revenue", "alias": "total_revenue" },
    { "function": "COUNT", "column": "id", "alias": "num_records" }
  ]
}

{
  "operation": "correlate",
  "columns": ["age", "salary", "tenure"],
  "method": "pearson"
}
```

**Supported operations:** `filter`, `sort`, `aggregate`, `describe`, `correlate`

**Response 201:** `AnalysisRecordResponse`

### GET /api/v1/datasets/{dataset_id}/analyses

List all analysis records for a dataset, most recent first.

**Response 200:** `AnalysisListResponse`

### GET /api/v1/datasets/{dataset_id}/analyses/{record_id}

Get a single analysis record including its result payload.

**Response 200:** `AnalysisRecordResponse`

### DELETE /api/v1/datasets/{dataset_id}/analyses/{record_id}

Delete a single analysis record.

**Response 200:** `{ "message": "Analysis record deleted.", "record_id": "..." }`

---

## Phase 3 Endpoints (Planned)

Conversational analysis sessions (LLM-backed). Phase 3 scope.

```
POST /api/v1/sessions                      Create analysis session
GET  /api/v1/sessions/{id}                 Get session state
POST /api/v1/sessions/{id}/messages        Send user message
GET  /api/v1/sessions/{id}/messages        Get message history
```
