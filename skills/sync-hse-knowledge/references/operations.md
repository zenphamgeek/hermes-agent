# Operations & Quality Rules Specification

## 1. Run Lifecycles & Checkpoints

Each synchronization run progresses through strictly tracked states: `PLANNED` -> `RUNNING` -> `SUCCEEDED` / `PARTIAL` / `FAILED` / `QUARANTINED`.

- **Checkpoints**: Stored per source and cursor in `checkpoint` table.
- **Reparsing**: Re-evaluates raw stored artifacts without re-downloading bytes.
- **Reconciliation**: Verifies graph integrity, missing citations, and orphans monthly.

---

## 2. Quality Gates

- **Critical Gates (Publish Blocking)**:
  - Missing source legal citation or authority level.
  - Conflicting unhandled effective dates.
  - Invalid CAS number checksum or unverified mixture components.
  - Incomplete SDS with missing supplier identification or major section errors.
  - Integrity mismatch between downloaded artifact bytes and computed SHA-256.
- **High Severity (Steward Queue)**:
  - Regulatory replacement missing target reference.
  - OEL values differing across jurisdictions.
  - High OCR ambiguity on threshold values.
