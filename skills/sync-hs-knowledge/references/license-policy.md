# License and Entitlement Policy

## States
- `PUBLIC_DOWNLOAD`: Full raw bytes, parsed text, and embeddings permitted.
- `PUBLIC_METADATA_ONLY`: Only titles, dates, URLs, and official summaries permitted.
- `LICENSE_REQUIRED`: Gated source; full text blocked until approved entitlement is present.
- `LICENSED`: Entitlement verified and within valid date window.
- `QUARANTINED`: Temporarily suspended due to circuit breaker or access contract deficit.

## Enforcement
1. Pre-fetch check evaluates `content_class` and active entitlements.
2. `storage_allowed=false` prohibits persisting raw blobs.
3. `embedding_allowed=false` excludes chunks from pgvector indices.
