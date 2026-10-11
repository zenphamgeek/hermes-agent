# Data Quality & Integrity Gates

## Critical Gates (Commit Blockers)
- Invalid HS code format or missing parent in the same edition.
- Tariff rate missing rate type, unit, or condition.
- Document version missing provenance to an immutable artifact SHA-256.
- Raw artifact SHA-256 mismatch against byte content.
- Policy state violation (e.g. attempting to persist full content of `LICENSE_REQUIRED` source).

## High Severity Issues (Review Queue)
- Conflicting effective dates between two official sources.
- Ambiguous multi-result classification rulings not properly partitioned.
- Missing replaced document target reference.
