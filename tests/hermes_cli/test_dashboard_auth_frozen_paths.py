"""Property and regression test suite for public paths and auth boundaries.

Guards against framework upgrade semantics shifts (path normalization, trailing
slashes, regex vs prefix matching) and enforces that auth bypass allowlists are
pinned against an explicit frozen fixture.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from hermes_cli import web_server
from hermes_cli.dashboard_auth import clear_providers, register_provider
from hermes_cli.dashboard_auth.public_paths import (
    PUBLIC_API_PATHS,
    PUBLIC_API_PATH_SPECS,
    is_public_api_path,
    normalize_api_path,
)
from tests.hermes_cli.conftest_dashboard_auth import StubAuthProvider


FROZEN_PUBLIC_API_PATHS_FIXTURE: frozenset[str] = frozenset({
    "/api/health",
    "/api/status",
    "/api/config/defaults",
    "/api/config/schema",
    "/api/model/info",
    "/api/dashboard/themes",
    "/api/dashboard/plugins",
    "/api/cron/fire",
    "/api/trae/status",
})


def test_public_api_paths_match_frozen_fixture():
    """Assert that the live PUBLIC_API_PATHS exactly matches the frozen security fixture.

    Any addition, removal, or path drift must fail loudly and require an explicit,
    deliberate update to both the security fixture and the architectural charter.
    """
    assert PUBLIC_API_PATHS == FROZEN_PUBLIC_API_PATHS_FIXTURE, (
        f"Drift detected between live PUBLIC_API_PATHS and frozen security fixture!\n"
        f"Added: {PUBLIC_API_PATHS - FROZEN_PUBLIC_API_PATHS_FIXTURE}\n"
        f"Removed: {FROZEN_PUBLIC_API_PATHS_FIXTURE - PUBLIC_API_PATHS}"
    )


def test_public_api_path_specs_metadata_integrity():
    """Verify that every route spec carries complete audit provenance and valid constraints."""
    valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
    for spec in PUBLIC_API_PATH_SPECS:
        assert spec.path.startswith("/api/"), f"Path {spec.path} must start with /api/"
        assert spec.reason.strip(), f"Spec {spec.path} missing audit reason"
        assert spec.owner.strip(), f"Spec {spec.path} missing team owner"
        assert len(spec.allowed_methods) >= 1, f"Spec {spec.path} must specify allowed methods"
        for method in spec.allowed_methods:
            assert method in valid_methods, f"Invalid method {method} in {spec.path}"


@pytest.mark.parametrize(
    "raw_path,method,expected",
    [
        # Canonical routes
        ("/api/status", "GET", True),
        ("/api/health", "GET", True),
        ("/api/config/defaults", "GET", True),
        ("/api/config/schema", "GET", True),
        ("/api/model/info", "GET", True),
        ("/api/dashboard/themes", "GET", True),
        ("/api/dashboard/plugins", "GET", True),
        ("/api/trae/status", "GET", True),
        ("/api/cron/fire", "POST", True),

        # Method enforcement (negative cases)
        ("/api/status", "POST", False),
        ("/api/health", "DELETE", False),
        ("/api/cron/fire", "GET", False),
        ("/api/cron/fire", "PUT", False),

        # Trailing slash normalization
        ("/api/status/", "GET", True),
        ("/api/health/", "GET", True),
        ("/api/cron/fire/", "POST", True),

        # Duplicate slash normalization
        ("/api//status", "GET", True),
        ("//api/status", "GET", True),

        # Traversal attacks attempting to escape to sensitive routes
        ("/api/status/../sessions", "GET", False),
        ("/api/status/../../etc/passwd", "GET", False),
        ("/api/%2e%2e/api/sessions", "GET", False),
        ("/api/health/../admin", "GET", False),

        # Subpaths not explicitly allowed
        ("/api/status/secret", "GET", False),
        ("/api/health/deep", "GET", False),

        # Malformed or non-API inputs
        ("", "GET", False),
        (None, "GET", False),
        ("/non-api/status", "GET", False),
    ],
)
def test_is_public_api_path_canonical_and_traversal_guards(raw_path, method, expected):
    """Ensure normalization, method gating, and anti-traversal rules pass uniformly."""
    assert is_public_api_path(raw_path, method) is expected


def test_property_registered_routes_auth_boundary():
    """Property test: every registered /api/ route in the app must be gated unless in fixture."""
    from starlette.routing import Route

    for route in web_server.app.routes:
        if isinstance(route, Route):
            path = route.path
            if path.startswith("/api/"):
                # Ignore dynamic MCP callback routes
                if path.startswith("/api/mcp/oauth/callback/"):
                    continue
                # If path has path parameters like /api/sessions/{session_id}
                clean_static_prefix = path.split("{")[0].rstrip("/")
                if path in FROZEN_PUBLIC_API_PATHS_FIXTURE:
                    assert path in PUBLIC_API_PATHS
                    assert is_public_api_path(path, "GET") or is_public_api_path(path, "POST")
                else:
                    # Sensitive route must NOT be recognized as public
                    assert is_public_api_path(path, "GET") is False
                    assert is_public_api_path(path, "POST") is False


def test_unauthenticated_request_behavior_under_gated_mode():
    """Verify live HTTP behavior under OAuth gated mode (non-loopback)."""
    clear_providers()
    register_provider(StubAuthProvider())
    prev_host = getattr(web_server.app.state, "bound_host", None)
    prev_port = getattr(web_server.app.state, "bound_port", None)
    prev_required = getattr(web_server.app.state, "auth_required", None)

    try:
        web_server.app.state.bound_host = "fly-app.fly.dev"
        web_server.app.state.bound_port = 443
        web_server.app.state.auth_required = True

        client = TestClient(web_server.app, base_url="https://fly-app.fly.dev")

        # Public endpoints return 200 without cookies
        res_status = client.get("/api/status")
        assert res_status.status_code == 200

        res_health = client.get("/api/health")
        assert res_health.status_code == 200

        # Trailing slash public endpoint passes auth gate (not blocked with 401 or 302 to login)
        res_trailing = client.get("/api/status/", follow_redirects=False)
        assert res_trailing.status_code != 401
        assert res_trailing.headers.get("location") != "/login"

        # Gated sensitive endpoints return 401
        res_sessions = client.get("/api/sessions", follow_redirects=False)
        assert res_sessions.status_code == 401

        # Traversal attempts return 401
        res_traversal = client.get("/api/status/../sessions", follow_redirects=False)
        assert res_traversal.status_code in (401, 404)

        # Wrong HTTP method on public endpoint returns 401 or 405 (never unauthenticated 200)
        res_wrong_method = client.post("/api/status")
        assert res_wrong_method.status_code in (401, 405)
    finally:
        clear_providers()
        web_server.app.state.bound_host = prev_host
        web_server.app.state.bound_port = prev_port
        web_server.app.state.auth_required = prev_required
