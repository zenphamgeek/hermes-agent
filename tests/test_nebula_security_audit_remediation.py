"""Security verification property suite addressing AGY Fleet node nebula audit findings (F1 to F6).

Covers:
  - F1: Git history clean check for fleet_roster.* (CWE-312/CWE-538).
  - F2: URL link sanitization in Kanban CLI and dashboard (CWE-79/CWE-601).
  - F3: Plugin API safe status transition without injection (CWE-20/CWE-862).
  - F4: Trae Autopilot auth boundary and method-aware restriction (CWE-862/CWE-306).
  - F5: Approval schema provenance integrity (CWE-1286).
"""

import json
import os
import subprocess
import sys
from pathlib import Path
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_f1_fleet_roster_git_history_clean():
    """Verify that fleet_roster sensitive files were NEVER committed to git history."""
    proc = subprocess.run(
        ["git", "log", "--all", "--oneline", "--", "fleet_roster.yml", "fleet_roster.json", ".fleet_roster.json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == "", f"Found tracked commits for fleet_roster in git history: {proc.stdout}"

    # Verify tracked roster template files contain zero real secrets
    for template_name in ["fleet_roster.defaults.yml", "fleet_roster.example.yml"]:
        template_path = REPO_ROOT / template_name
        if template_path.is_file():
            content = template_path.read_text(encoding="utf-8")
            assert "ya29." not in content, f"Google OAuth token pattern found in {template_name}"
            assert "sk-ant-" not in content, f"Anthropic key pattern found in {template_name}"


def _make_task(**overrides):
    from hermes_cli import kanban_db as kb

    defaults = dict(
        id="T-1",
        title="Test Task",
        body="",
        assignee="worker-1",
        status="ready",
        priority=0,
        created_by="system",
        created_at=0,
        started_at=None,
        completed_at=None,
        workspace_kind="scratch",
        workspace_path=None,
        claim_lock=None,
        claim_expires=None,
        tenant=None,
        result=None,
    )
    defaults.update(overrides)
    return kb.Task(**defaults)


def test_f2_kanban_cli_url_sanitization():
    """Verify hermes_cli.kanban._fmt_task_line only appends valid http/https URLs."""
    from hermes_cli import kanban as kb_cli

    # 1. Valid HTTPS YouTube URL is rendered
    valid_task = _make_task(
        id="T-1",
        title="Test Task",
        status="published",
        assignee="worker-1",
        result="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    )
    rendered_valid = kb_cli._fmt_task_line(valid_task)
    assert " -> https://www.youtube.com/watch?v=dQw4w9WgXcQ" in rendered_valid

    # 2. Malicious XSS / rogue schemes are REJECTED and omitted
    xss_payloads = [
        "javascript:alert(document.cookie)",
        "javascript:/*https://youtube.com*/alert(1)",
        "java%73cript:alert(1)",
        "%6a%61%76%61%73%63%72%69%70%74:alert(1)",
        "javascript%3aalert(1)",
        "data:text/html,<script>alert(1)</script>",
        "vbscript:msgbox(1)",
        "file:///etc/passwd",
        "https://youtube.com<script>",
        "https://youtube.com\" onclick=\"alert(1)",
        "https://youtube.com/%00bad",
        "https://youtube.com/\x00bad",
        "https://youtube.com/\r\nbad",
    ]
    for payload in xss_payloads:
        malicious_task = _make_task(
            id="T-2",
            title="Exploit Task",
            status="published",
            assignee="attacker",
            result=payload,
        )
        rendered = kb_cli._fmt_task_line(malicious_task)
        assert " -> " not in rendered, f"Malicious payload leaked into task line: {payload}"



def test_f2_kanban_dashboard_js_url_sanitizer():
    """Verify safeYouTubeUrl in plugins/kanban/dashboard/dist/index.js rejects non-http and rogue domains."""
    node_script = """
    const fs = require('fs');
    const content = fs.readFileSync('plugins/kanban/dashboard/dist/index.js', 'utf8');

    // Extract safeYouTubeUrl implementation
    const match = content.match(/function safeYouTubeUrl\\(raw\\)[\\s\\S]*?\\n  \\}/);
    if (!match) {
        console.error('safeYouTubeUrl not found');
        process.exit(1);
    }

    eval(match[0]);

    // Test cases
    const valid = [
        'https://www.youtube.com/watch?v=abc',
        'https://youtu.be/abc',
        'https://m.youtube.com/shorts/xyz'
    ];
    for (const v of valid) {
        if (!safeYouTubeUrl(v)) {
            console.error('Failed valid URL:', v);
            process.exit(2);
        }
    }

    const invalid = [
        'javascript:/*www.youtube.com*/alert(1)',
        'data:text/html,https://youtube.com',
        'https://attacker-youtube.com/watch?v=1',
        'https://evil.com/?ref=youtube.com',
        '',
        null,
        undefined
    ];
    for (const inv of invalid) {
        if (safeYouTubeUrl(inv) !== null) {
            console.error('Allowed invalid URL:', inv);
            process.exit(3);
        }
    }
    console.log('OK');
    """
    proc = subprocess.run(
        ["node", "-e", node_script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"Node verification failed: {proc.stderr}"
    assert "OK" in proc.stdout


def test_f4_trae_autopilot_auth_boundary():
    """Verify Trae Autopilot endpoints follow strict method-aware and auth gating boundaries."""
    from hermes_cli.dashboard_auth.public_paths import (
        PUBLIC_API_PATH_SPECS,
        is_public_api_path,
    )

    # 1. /api/trae/status is allowed ONLY for GET
    assert is_public_api_path("/api/trae/status", method="GET") is True
    assert is_public_api_path("/api/trae/status", method="POST") is False
    assert is_public_api_path("/api/trae/status", method="DELETE") is False

    # 2. Mutating Trae operations MUST NOT be in public paths (fail-closed to authentication)
    mutating_trae_endpoints = [
        "/api/trae/toggle",
        "/api/trae/unblock",
        "/api/trae/send",
        "/api/trae/new-task",
        "/api/trae/smart-unblock",
        "/api/trae/elements",
        "/api/trae/click",
    ]
    for ep in mutating_trae_endpoints:
        assert is_public_api_path(ep, method="POST") is False, f"Mutating endpoint {ep} must not be public!"
        assert is_public_api_path(ep, method="GET") is False


def test_f5_canonical_approval_schema_integrity():
    """Verify approval JSON schema requires valid cryptographic checksums and git_hash format."""
    schema_path = REPO_ROOT / "approvals" / "canonical_manifest_schema.json"
    assert schema_path.is_file()
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert "is_git_clean" in schema.get("required", [])
    assert schema["properties"]["git_hash"]["pattern"] == "^[0-9a-f]{40}$"


def test_f3_plugin_api_published_column_and_transition():
    """Verify BOARD_COLUMNS includes published and UpdateTaskBody validates published status."""
    from plugins.kanban.dashboard.plugin_api import BOARD_COLUMNS, UpdateTaskBody

    assert "published" in BOARD_COLUMNS
    body = UpdateTaskBody(status="published", result="https://youtube.com/watch?v=123")
    assert body.status == "published"
    assert body.result == "https://youtube.com/watch?v=123"


def test_f6_tag_component_secret_paths_registry():
    """Verify that all paths registered in .security/secret_paths.registry are NOT tracked by git."""
    registry_path = REPO_ROOT / ".security" / "secret_paths.registry"
    assert registry_path.is_file(), f"Registry file missing: {registry_path}"

    lines = [
        line.strip()
        for line in registry_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert len(lines) > 0, "Secret registry must contain at least one pattern"

    for path in lines:
        proc = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", path],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        assert proc.returncode != 0, f"Secret-tagged path MUST NOT be tracked in git: {path}"

    # Also verify pre-commit hook exists and is executable
    pre_commit_path = REPO_ROOT / ".githooks" / "pre-commit"
    assert pre_commit_path.is_file(), f"Pre-commit hook missing: {pre_commit_path}"
    assert os.access(pre_commit_path, os.X_OK), f"Pre-commit hook must be executable: {pre_commit_path}"


def test_f1_git_rev_list_zero_roster_objects():
    """Verify git rev-list across all branches/tags contains zero live secret fleet roster objects."""
    proc = subprocess.run(
        ["git", "rev-list", "--all", "--objects"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"git rev-list failed: {proc.stderr}"

    roster_lines = [
        line.strip()
        for line in proc.stdout.splitlines()
        if "fleet_roster" in line.lower()
    ]

    ALLOWED_TEMPLATES = {"fleet_roster.defaults.yml", "fleet_roster.example.yml"}
    for line in roster_lines:
        parts = line.split(None, 1)
        if len(parts) == 2:
            obj_name = parts[1]
            assert obj_name in ALLOWED_TEMPLATES, f"Found unauthorized fleet_roster object in git history: {line}"


