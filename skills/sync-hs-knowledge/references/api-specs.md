# REST API Specification: HS Knowledge Sync API

**Base URL**: `http://localhost:8000`  
**API Version**: `v1`  
**Protocol**: HTTP/1.1 & HTTP/2  
**Content-Type**: `application/json`

---

## 1. Health & Readiness Probes

### `GET /health`
Returns general service health and database connectivity.

**Response `200 OK`**:
```json
{
  "status": "ok",
  "database": "connected"
}
```

### `GET /health/live`
Kubernetes / systemd liveness probe.

**Response `200 OK`**:
```json
{
  "status": "alive",
  "service": "hs-sync"
}
```

### `GET /health/ready`
Kubernetes / systemd readiness probe checking DB ping.

**Response `200 OK`**:
```json
{
  "status": "ready",
  "database": "connected"
}
```

---

## 2. Source Registry & Health

### `GET /v1/sources`
Lists all registered knowledge sources with their current policy and status.

**Response `200 OK`**:
```json
[
  {
    "id": "VN_GOV_LEGAL",
    "name": "Cổng thông tin điện tử Chính phủ - Văn bản QPPL",
    "jurisdiction": "VN",
    "official_authority_tier": "A1_SIGNED_OFFICIAL",
    "is_enabled": true,
    "requires_license": false
  },
  {
    "id": "WCO_HS_CONTENT",
    "name": "WCO Trade Tools - Explanatory Notes & Compendium",
    "jurisdiction": "INT",
    "official_authority_tier": "A1_SIGNED_OFFICIAL",
    "is_enabled": true,
    "requires_license": true
  }
]
```

### `GET /v1/sources/{source_id}/health`
Returns reachability and latency metrics for a specific source.

**Parameters**:
- `source_id` (path, string): Unique identifier of the source (e.g. `VN_CUSTOMS_TARIFF`).

**Response `200 OK`**:
```json
{
  "source_id": "VN_CUSTOMS_TARIFF",
  "is_healthy": true,
  "latency_ms": 142,
  "status": "OK"
}
```

### `GET /v1/entitlements/validate`
Validates license readiness across all proprietary and gated sources.

**Response `200 OK`**:
```json
[
  {
    "source_id": "WCO_HS_CONTENT",
    "license_required": true,
    "license_status": "PENDING_ENTITLEMENT",
    "ready_for_full_sync": false,
    "allowed_ingestion_level": "METADATA_ONLY",
    "remediation": "Configure valid WCO Trade Tools subscription credentials."
  }
]
```

---

## 3. Synchronization & Crawl Runs

### `POST /v1/sync/plan`
Generates a dry-run execution plan without modifying the database.

**Request Body**:
```json
{
  "scope": "vietnam-core",
  "source_id": null,
  "mode": "incremental"
}
```

**Response `200 OK`**:
```json
{
  "scope": "vietnam-core",
  "mode": "incremental",
  "total_estimated": 16,
  "sources": [
    {
      "source_id": "VN_GOV_LEGAL",
      "action": "SYNC",
      "estimated_items": 3,
      "policy_decision": "ALLOWED",
      "reason": null
    }
  ]
}
```

### `POST /v1/sync/runs`
Triggers an immediate synchronization run.

**Request Body**:
```json
{
  "scope": "vietnam-core",
  "source_id": "VN_CUSTOMS_RULINGS",
  "mode": "incremental",
  "dry_run": false,
  "reparse": false
}
```

**Response `200 OK`**:
```json
{
  "status": "succeeded",
  "run_id": "0b71b13d-baa3-4186-b9f0-6de373f1cc33",
  "scope": "vietnam-core",
  "sources": ["VN_CUSTOMS_RULINGS"],
  "discovered": 2,
  "downloaded": 2,
  "unchanged": 0,
  "parsed": 2,
  "normalized": 8,
  "quarantined": 0,
  "license_blocks": [],
  "unattended_readiness": "ready",
  "checkpoint": {
    "VN_CUSTOMS_RULINGS": "2"
  },
  "coverage_report_uri": "memory://reports/0b71b13d-baa3-4186-b9f0-6de373f1cc33.json"
}
```

### `GET /v1/sync/runs/{run_id}`
Retrieves details and counters for a specific crawl run.

### `POST /v1/sync/on-demand`
Triggers an immediate, targeted real-time crawl and extraction for a specific HS code, taxonomy node, chapter, or commodity keyword, index matching entities, and dispatches the `hs.taxonomy.synced` webhook event to subscribers.

**Request Body**:
```json
{
  "taxonomy": "8471.30.20",
  "sources": ["VN_CUSTOMS_RULINGS", "VN_CUSTOMS_TARIFF", "VN_GOV_LEGAL"],
  "scope": "vietnam-core",
  "as_of": "2026-08-21",
  "webhook_callback_url": "https://erp.internal/webhooks/on-demand-callback"
}
```

**Response `200 OK`**:
```json
{
  "run_id": "97e6822c-76b3-469b-98a4-681a95e0cba1",
  "taxonomy": "8471.30.20",
  "status": "succeeded",
  "discovered": 2,
  "downloaded": 2,
  "normalized": 2,
  "quarantined": 0,
  "results": [
    {
      "entity_type": "classification_ruling",
      "entity_id": "8921/TB-TCHQ",
      "title": "8921/TB-TCHQ - Máy tính bảng iPad",
      "content_text": "Mã HS kết luận: 8471.30.20",
      "score": 1.0,
      "source_url": "https://www.customs.gov.vn/index.jsp?cid=25&ruling_id=8921"
    }
  ],
  "event_dispatched": true
}
```

---

## 4. Hybrid Retrieval & Search

### `GET /v1/search`
Performs hybrid lexical, semantic, and temporal search across legal documents, HS codes, and customs rulings.

**Query Parameters**:
- `query` (string, required): Search phrase, keyword, document number, or HS code.
- `as_of` (string, optional, default: today): ISO-8601 date (`YYYY-MM-DD`) for temporal legal filtering.
- `limit` (integer, optional, default: 20): Maximum number of results to return.

**Response `200 OK`**:
```json
{
  "query": "8471.30.20",
  "as_of": "2026-08-21",
  "results": [
    {
      "entity_type": "hs_node",
      "entity_id": "8471.30.20",
      "title": "Mã HS 8471.30.20: Máy tính xách tay (laptops)",
      "content_snippet": "Level 4 - Parent: 8471.30. Máy tính xách tay (laptops)",
      "score": 0.95,
      "authority_level": "A1_SIGNED_OFFICIAL",
      "citation": {
        "source_url": null,
        "document_id": null,
        "artifact_sha256": null,
        "page": null,
        "section": "HS Chapter 84"
      },
      "valid_from": "2022-01-01",
      "valid_to": null
    },
    {
      "entity_type": "classification_ruling",
      "entity_id": "e948a62e-3af2-4c10-b965-7a8772f337b5",
      "title": "TB-001/HQ - Hàng hóa phân loại",
      "content_snippet": "Mã HS kết luận: 8471.30.20. Bộ xử lý điều khiển lập trình",
      "score": 0.92,
      "authority_level": "A2_OFFICIAL_DATABASE",
      "citation": {
        "source_url": "https://www.customs.gov.vn/index.jsp?cid=25&ruling_id=8921",
        "document_id": "TB-001/HQ",
        "artifact_sha256": "bea31c63-28b5-494d-b95c-6f123da2b1c5",
        "page": 1,
        "section": "Kết quả phân loại"
      },
      "valid_from": "2026-08-21",
      "valid_to": null
    }
  ]
}
```

---

## 5. Webhooks & Outbound Event Hub API

### `POST /v1/webhooks/subscriptions`
Registers a new subscriber endpoint with optional HMAC secret and event filters.

**Request Body**:
```json
{
  "name": "odoo-customs-sync",
  "target_url": "https://erp.company.com/webhooks/hs-events",
  "event_types": ["hs.legal_doc.promulgated", "hs.ruling.published", "hs.tariff.changed"],
  "secret_token": "optional_predefined_hmac_secret"
}
```

**Response `200 OK`**:
```json
{
  "subscription_id": "whsub_9b84e12fa83c",
  "name": "odoo-customs-sync",
  "target_url": "https://erp.company.com/webhooks/hs-events",
  "event_types": ["hs.legal_doc.promulgated", "hs.ruling.published", "hs.tariff.changed"],
  "is_active": true,
  "failure_count": 0,
  "created_at": "2026-08-21T09:40:00Z"
}
```

### `GET /v1/webhooks/subscriptions`
Lists all registered outbound webhook subscriptions.

**Query Parameters**:
- `active_only` (boolean, optional, default: false)

### `DELETE /v1/webhooks/subscriptions/{subscription_id}`
Deletes a webhook subscription.

### `POST /v1/webhooks/subscriptions/{subscription_id}/test`
Dispatches a `hs.ping.test` event directly to the subscriber to test reachability and HMAC verification.

### `GET /v1/webhooks/deliveries`
Audits recent webhook deliveries and status codes.

### `POST /v1/webhooks/trigger`
Inbound trigger allowing upstream systems / message queues to initiate an on-demand sync.

**Request Body**:
```json
{
  "scope": "vietnam-core",
  "source_id": "VN_CUSTOMS_TARIFF",
  "mode": "incremental"
}
```

```
