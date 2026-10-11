# WAF and Challenge Resilience Lab

## Lab Objectives
Provides deterministic, offline unit/integration test simulation for edge conditions:
- HTTP 403 Forbidden
- HTTP 429 Rate Limit with `Retry-After`
- HTTP 500 / 502 / 503 / 504 Transient Server Errors
- Connection Timeouts and Network Resets
- Managed Challenges (Cloudflare Turnstile test keys / test doubles)

## Network Guard
- Lab execution strictly binds to `localhost` and local test doubles.
- Public network egress is blocked by test isolation fixtures.
- Validates that interactive challenges trigger quarantine and fallback without calling CAPTCHA solvers or stealth packages.
