# Unattended Smart Acquisition Specification

## Channel Selection Priority
1. `official_api`: Dedicated REST/GraphQL endpoint or commercial licensed API.
2. `bulk_export`: Signed data dumps, SFTP/S3 shares.
3. `http`: Standard HTTP/HTTPS with ETag and conditional headers (`If-None-Match`, `If-Modified-Since`).
4. `browser_render`: Headless browser rendering for JavaScript-dependent DOM (no interactive challenge solving).
5. `sanctioned_fallback`: Pre-approved official mirrors.
6. `quarantine`: Source placed into quarantine when interactive challenges are detected.

## Adaptive Retry & Circuit Breaker
- Exponential backoff with decorrelated jitter.
- Strict adherence to `Retry-After` HTTP headers.
- Hard stop on 401, 403, 404, or interactive challenges (no infinite loops).
- Circuit breaker trips after threshold consecutive failures (default 8); low-rate probes scheduled every 30 minutes.
