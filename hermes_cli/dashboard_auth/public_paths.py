"""Shared allowlist of ``/api/*`` paths that bypass dashboard auth.

Two middlewares enforce dashboard auth and previously kept independent
copies of this list:

* ``hermes_cli.web_server.auth_middleware`` — loopback / ``--insecure``
  mode, gates on the ephemeral ``_SESSION_TOKEN``.
* ``hermes_cli.dashboard_auth.middleware.gated_auth_middleware`` —
  non-loopback mode, gates on the OAuth session cookie.

When the lists drifted, ``/api/status`` ended up public under the legacy
gate but 401'd under the OAuth gate. That broke the portal's wildcard
liveness probe (``nous-account-service`` ``fly-provider.ts``
``getInstanceRuntimeStatus``), which fetches ``/api/status`` without a
cookie as its sole signal of "agent dashboard is alive": every healthy
wildcard-subdomain agent surfaced as STARTING/down in the portal UI even
though the dashboard was serving correctly.

Centralising the allowlist here so both middlewares import the same
frozenset prevents the next drift. Keep this list minimal — only truly
non-sensitive, read-only endpoints belong here. As a sanity check, every
entry should be safe to expose to:

  * external uptime probes (Pingdom, Better Stack, NAS),
  * the dashboard SPA before the user has logged in,
  * anyone who happens to ``curl`` the hostname.

If a new endpoint doesn't pass all three tests, it should be gated and
the SPA should bootstrap it after login instead.
"""
from __future__ import annotations
from typing import NamedTuple


class PublicPathSpec(NamedTuple):
    """Specification and audit contract for an unauthenticated public route."""
    path: str
    reason: str
    owner: str
    allowed_methods: tuple[str, ...] = ("GET",)


PUBLIC_API_PATH_SPECS: tuple[PublicPathSpec, ...] = (
    PublicPathSpec(
        path="/api/health",
        reason="Minimal process liveness probe for desktop/backend boot handshakes",
        owner="core-infra",
        allowed_methods=("GET",),
    ),
    PublicPathSpec(
        path="/api/status",
        reason="Liveness probe target for portal wildcard monitoring",
        owner="core-infra",
        allowed_methods=("GET",),
    ),
    PublicPathSpec(
        path="/api/config/defaults",
        reason="Read-only config defaults feed for unauthenticated SPA setup",
        owner="frontend-spa",
        allowed_methods=("GET",),
    ),
    PublicPathSpec(
        path="/api/config/schema",
        reason="Read-only JSON schema feed for config editor",
        owner="frontend-spa",
        allowed_methods=("GET",),
    ),
    PublicPathSpec(
        path="/api/model/info",
        reason="Read-only model metadata and context window specifications",
        owner="models-team",
        allowed_methods=("GET",),
    ),
    PublicPathSpec(
        path="/api/dashboard/themes",
        reason="Read-only theme manifest for pre-login styling",
        owner="frontend-spa",
        allowed_methods=("GET",),
    ),
    PublicPathSpec(
        path="/api/dashboard/plugins",
        reason="Read-only plugin manifests for client UI bootstrapping",
        owner="frontend-spa",
        allowed_methods=("GET",),
    ),
    PublicPathSpec(
        path="/api/cron/fire",
        reason="Chronos webhook callback; authenticated via independent short-lived JWT token",
        owner="scheduler",
        allowed_methods=("POST",),
    ),
    PublicPathSpec(
        path="/api/trae/status",
        reason="Trae Autopilot read-only telemetry and health status probe",
        owner="trae-agent",
        allowed_methods=("GET",),
    ),
)

PUBLIC_API_PATHS: frozenset[str] = frozenset(spec.path for spec in PUBLIC_API_PATH_SPECS)


def normalize_api_path(path: str) -> str:
    """Normalize a request path for consistent security boundary evaluation.

    Decodes URL-encoded octets (e.g. %2e%2e) and resolves posix traversal
    dots, double slashes, and trailing slashes. Fails closed to empty string
    on any malformed input or decoding error.
    """
    if not path or not isinstance(path, str):
        return ""
    try:
        from urllib.parse import unquote
        import posixpath
        unquoted = unquote(path)
        while unquoted.startswith("//"):
            unquoted = unquoted[1:]
        cleaned = posixpath.normpath(unquoted).rstrip("/") or "/"
        if cleaned.startswith("//"):
            cleaned = "/" + cleaned.lstrip("/")
        return cleaned
    except Exception:
        return ""


def is_public_api_path(path: str, method: str = "GET") -> bool:
    """Check whether a request path and HTTP method match an allowed public route spec.

    Fails closed: only paths explicitly registered in PUBLIC_API_PATH_SPECS with
    an allowed method return True. Path is normalized before matching to prevent
    traversal bypasses.
    """
    clean = normalize_api_path(path)
    if not clean:
        return False
    norm_method = (method or "GET").upper()
    for spec in PUBLIC_API_PATH_SPECS:
        if spec.path == clean:
            return norm_method in spec.allowed_methods
    return False


