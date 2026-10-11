# OpenAPI Specification: HSE Knowledge Platform & Webhook Hub

## Base URL: `/v1`

### 1. Synchronization & On-Demand
- `POST /v1/sync/plan`: Dry-run evaluation of sync workload.
- `POST /v1/sync/runs`: Triggers a full or incremental synchronization run.
- `GET /v1/sync/runs/{id}`: Retrieves run status and statistics.
- `POST /v1/sync/runs/{id}/resume`: Resumes an interrupted run.
- `POST /v1/sync/on-demand`: Real-time on-demand crawling for a specific topic, chemical, regulation, or standard.

### 2. Sources & Entitlements
- `GET /v1/sources`: Lists configured sources and health.
- `GET /v1/sources/{id}/acquisition`: Detailed acquisition route, circuit breaker, and retry stats.

### 3. Applicability & Legal Registers
- `POST /v1/facility-profiles/validate`: Validates facility facts.
- `POST /v1/applicability/evaluate`: Evaluates applicable obligations and missing facts.
- `GET /v1/obligations`: Queries normalized legal obligations.

### 4. Search & HSE Domain Lookups
- `GET /v1/search`: Hybrid lexical, semantic, and temporal search (`query`, `as_of`, `authority`).
- `GET /v1/chemicals`: Queries substances, mixtures, and SDS 16-section data.
- `GET /v1/oels`: Queries Occupational Exposure Limits across jurisdictions.
- `GET /v1/hazards`: Queries hazards, bow-ties, and controls.
- `GET /v1/environmental-limits`: Queries discharge and emission limits.

### 5. Webhooks & Outbound Events
- `POST /v1/webhooks/subscriptions`: Creates outbound webhook subscription.
- `GET /v1/webhooks/subscriptions`: Lists subscriptions.
- `DELETE /v1/webhooks/subscriptions/{id}`: Deactivates subscription.
- `POST /v1/webhooks/subscriptions/{id}/test`: Sends ping test event.
- `GET /v1/webhooks/deliveries`: Lists webhook delivery audit logs.
- `POST /v1/webhooks/trigger`: Inbound webhook endpoint to trigger on-demand sync.
