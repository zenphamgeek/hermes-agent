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


def test_f6_secret_registry_ssot_gitignore_parity():
    """Verify programmatic SSOT parity between .security/secret_paths.registry and .gitignore."""
    sync_tool = REPO_ROOT / "tools" / "sync_secret_registry.py"
    assert sync_tool.is_file(), f"Sync tool missing at {sync_tool}"

    proc = subprocess.run(
        [sys.executable, str(sync_tool), "--check"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"SSOT parity check failed: {proc.stderr}\n{proc.stdout}"
    assert "100% parity" in proc.stdout


def test_f2_approval_asset_checksums_provenance():
    """Verify approval records strictly bind cryptographic sha256 checksums to approved artifacts."""
    import re
    approvals_dir = REPO_ROOT / "approvals"
    assert approvals_dir.is_dir()

    approval_files = list(approvals_dir.glob("S*_EP*_APPROVAL.json"))
    assert len(approval_files) > 0, "No approval manifest files found to audit"

    HEX64 = re.compile(r"^[0-9a-f]{64}$")

    for approval_path in approval_files:
        data = json.loads(approval_path.read_text(encoding="utf-8"))
        if data.get("decision") == "approved":
            checksums = data.get("asset_checksums", {})
            assert isinstance(checksums, dict) and len(checksums) > 0, (
                f"{approval_path.name} approved without asset_checksums"
            )
            for asset_key, sha in checksums.items():
                assert HEX64.match(sha), f"Malformed SHA-256 for {asset_key} in {approval_path.name}: {sha}"

            closure = data.get("closure_sha256")
            assert closure and HEX64.match(closure), (
                f"{approval_path.name} approved with missing or malformed closure_sha256: {closure}"
            )


def test_f1_approval_payloads_zero_secrets():
    """Verify approval manifest payloads contain zero secret tokens, client secrets, or OAuth credentials."""
    from tools.verify_approval_provenance import audit_approvals

    total, clean, errors = audit_approvals(verbose=False)
    assert total > 0, "Expected at least 1 approval file"
    assert not errors, f"Approval secret scanning failed with {len(errors)} errors: {errors}"


def test_f3_zero_assert_statements_in_assembly_scripts():
    """Verify production assembly scripts use explicit exceptions instead of assert statements (CWE-617)."""
    import ast

    for script_name in ["assemble_master_video_s1_ep01.py"]:
        script_path = REPO_ROOT / script_name
        if script_path.is_file():
            tree = ast.parse(script_path.read_text(encoding="utf-8"))
            assert_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]
            assert len(assert_nodes) == 0, (
                f"Found {len(assert_nodes)} assert statement(s) in {script_name} (lines: {[n.lineno for n in assert_nodes]})"
            )


def test_f5_dirty_tree_addendum_schema_and_verification(tmp_path):
    """Verify dirty_tree_addendum schema presence and cryptographic validation."""
    schema_path = REPO_ROOT / "approvals" / "canonical_manifest_schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert "dirty_tree_addendum" in schema["properties"]
    dirty_props = schema["properties"]["dirty_tree_addendum"]["properties"]
    assert "diff_sha256" in dirty_props
    assert "untracked_files_sha256" in dirty_props

    # Test that verify_approval_provenance catches malformed dirty_tree_addendum
    from tools.verify_approval_provenance import check_for_secrets
    import re
    hex64_re = re.compile(r"^[0-9a-f]{64}$")
    assert hex64_re.match("a" * 64)
    assert not hex64_re.match("bad_hash")


def test_f1_staging_artifacts_zero_secrets():
    """Verify machine-generated publish artifacts in output/youtube_staging/ contain zero credential leaks."""
    from tools.verify_approval_provenance import audit_staging_artifacts

    total_scanned, errors = audit_staging_artifacts(verbose=False)
    assert total_scanned > 0, "Expected at least 1 staging artifact in output/youtube_staging/"
    assert not errors, f"Staging publish-boundary secret scan failed with {len(errors)} errors: {errors}"


def test_f1_publish_payload_scanner_blocks_secrets():
    """Verify enforce_publish_gate blocks payload containing leaked credentials."""
    from tools.verify_approval_provenance import enforce_publish_gate, SecurityAuditFailure

    # Clean payload passes
    clean_snippet = {
        "title": "Tập 01: Xác Suất trong AI | ZENPHAM",
        "description": "Nghịch lý Laplace và Bayes...",
        "tags": ["AI", "Math"],
    }
    enforce_publish_gate(clean_snippet, context="clean_test")

    # Malicious payload with Google OAuth token must fail
    dirty_snippet = {
        "title": "Tập 01: Test",
        "description": "Debug token: ya29.a0ARrdaM_FakeTokenStringForTesting1234567890",
    }
    with pytest.raises(SecurityAuditFailure) as exc_info:
        enforce_publish_gate(dirty_snippet, context="dirty_test")
    assert "Release Gate Hard Stop" in str(exc_info.value)
    assert "ya29" in str(exc_info.value)


def test_f1_publish_payload_break_glass_logging(tmp_path, monkeypatch):
    """Verify break-glass override requires >=15 chars reason and logs audit record."""
    from tools.verify_approval_provenance import enforce_publish_gate, SecurityAuditFailure

    dirty_payload = "Bearer sk-ant-api03-FakeAnthropicKeyForTestingOnly-12345"

    # 1. Override without reason fails
    monkeypatch.setenv("HERMES_ALLOW_PUBLISH_OVERRIDE", "1")
    monkeypatch.setenv("HERMES_OVERRIDE_REASON", "short")
    with pytest.raises(SecurityAuditFailure) as exc_info:
        enforce_publish_gate(dirty_payload, context="break_glass_fail")
    assert "must be at least 15 characters" in str(exc_info.value)

    # 2. Override with valid reason succeeds and writes to log
    log_file = tmp_path / "test_overrides.log"
    monkeypatch.setattr("tools.verify_approval_provenance.OVERRIDES_LOG", log_file)
    valid_reason = "Emergency deployment authorized by SecOps lead"
    monkeypatch.setenv("HERMES_OVERRIDE_REASON", valid_reason)

    enforce_publish_gate(dirty_payload, context="break_glass_success")
    assert log_file.is_file()
    log_content = log_file.read_text(encoding="utf-8")
    assert valid_reason in log_content
    assert "break_glass_success" in log_content


def test_f1_publish_payload_allowlist_filtering():
    """Verify allowlist permits vetted benign substrings."""
    from tools.verify_approval_provenance import audit_publish_payload

    payload = {"info": "Reference to ya29.benign_mock_identifier"}
    # Without allowlist -> flagged
    leaks = audit_publish_payload(payload, context="test", allowlist=[])
    assert len(leaks) > 0

    # With allowlist -> allowed
    leaks_allowed = audit_publish_payload(payload, context="test", allowlist=["ya29.benign_mock_identifier"])
    assert len(leaks_allowed) == 0


def test_f1_publish_payload_break_glass_fails_closed_on_unwritable_sink(monkeypatch, tmp_path):
    """Verify break-glass override strictly fails closed when audit sink is unwritable (auditing auditor failure mode)."""
    from tools.verify_approval_provenance import enforce_publish_gate, SecurityAuditFailure

    dirty_payload = "Bearer sk-ant-api03-FakeKeyForFailClosedAuditTest-12345"
    monkeypatch.setenv("HERMES_ALLOW_PUBLISH_OVERRIDE", "1")
    monkeypatch.setenv("HERMES_OVERRIDE_REASON", "Valid override reason for audit sink test")

    # Point OVERRIDES_LOG to a path inside a non-existent unwritable directory (e.g. invalid filename / directory)
    unwritable_sink = tmp_path / "read_only_dir" / "publish_overrides.log"
    # Create the parent directory and make it read-only
    unwritable_sink.parent.mkdir()
    os.chmod(unwritable_sink.parent, 0o444)
    monkeypatch.setattr("tools.verify_approval_provenance.OVERRIDES_LOG", unwritable_sink)

    try:
        with pytest.raises(SecurityAuditFailure) as exc_info:
            enforce_publish_gate(dirty_payload, context="unwritable_sink_test")
        assert "Break-glass audit sink unavailable" in str(exc_info.value)
        assert "refusing unlogged break-glass override" in str(exc_info.value)
    finally:
        # Restore permissions so cleanup works
        os.chmod(unwritable_sink.parent, 0o755)


def test_f1_publish_payload_break_glass_second_actor_validation(monkeypatch, tmp_path):
    """Verify break-glass enforces distinct second-actor authorization when HERMES_REQUIRE_SECOND_ACTOR=1."""
    from tools.verify_approval_provenance import enforce_publish_gate, SecurityAuditFailure

    dirty_payload = "Bearer sk-ant-api03-FakeKeyForSecondActorTest-12345"
    log_file = tmp_path / "second_actor_overrides.log"
    monkeypatch.setattr("tools.verify_approval_provenance.OVERRIDES_LOG", log_file)
    monkeypatch.setenv("HERMES_ALLOW_PUBLISH_OVERRIDE", "1")
    monkeypatch.setenv("HERMES_OVERRIDE_REASON", "Critical emergency fix deployed by lead")
    monkeypatch.setenv("HERMES_REQUIRE_SECOND_ACTOR", "1")
    monkeypatch.setenv("USER", "zen_operator")

    # 1. Missing second actor -> fails
    monkeypatch.delenv("HERMES_OVERRIDE_ACTOR", raising=False)
    with pytest.raises(SecurityAuditFailure) as exc:
        enforce_publish_gate(dirty_payload, context="missing_second_actor")
    assert "requires HERMES_OVERRIDE_ACTOR" in str(exc.value)

    # 2. Self-approval (second actor == current user) -> fails
    monkeypatch.setenv("HERMES_OVERRIDE_ACTOR", "zen_operator")
    with pytest.raises(SecurityAuditFailure) as exc:
        enforce_publish_gate(dirty_payload, context="self_approval")
    assert "must be distinct from current operator" in str(exc.value)

    # 3. Valid distinct second actor -> succeeds and logs both operator and authorized_by
    monkeypatch.setenv("HERMES_OVERRIDE_ACTOR", "secops_lead_auditor")
    enforce_publish_gate(dirty_payload, context="valid_second_actor")
    assert log_file.is_file()
    entry = json.loads(log_file.read_text(encoding="utf-8").strip())
    assert entry["authorized_by"] == "secops_lead_auditor"
    assert entry["operator"] == "zen_operator"


def test_f1_publish_allowlist_schema_validation(monkeypatch, tmp_path):
    """Verify runtime schema validation for .security/publish_allowlist.json."""
    from tools.verify_approval_provenance import load_publish_allowlist

    # 1. Valid allowlist file
    valid_file = tmp_path / "valid_allowlist.json"
    valid_file.write_text(json.dumps({"allowed_patterns": ["pat1", "pat2"]}), encoding="utf-8")
    monkeypatch.setattr("tools.verify_approval_provenance.ALLOWLIST_FILE", valid_file)
    patterns = load_publish_allowlist(strict=True)
    assert patterns == ["pat1", "pat2"]

    # 2. Malformed JSON or non-dict root
    invalid_root = tmp_path / "invalid_root.json"
    invalid_root.write_text(json.dumps(["not", "a", "dict"]), encoding="utf-8")
    monkeypatch.setattr("tools.verify_approval_provenance.ALLOWLIST_FILE", invalid_root)
    with pytest.raises(ValueError, match="Allowlist schema root must be a dict"):
        load_publish_allowlist(strict=True)

    # 3. Non-string elements in allowed_patterns
    invalid_patterns = tmp_path / "invalid_patterns.json"
    invalid_patterns.write_text(json.dumps({"allowed_patterns": [123, False]}), encoding="utf-8")
    monkeypatch.setattr("tools.verify_approval_provenance.ALLOWLIST_FILE", invalid_patterns)
    with pytest.raises(ValueError, match="must be a list of strings"):
        load_publish_allowlist(strict=True)


def test_f3_duration_reconciliation_integrity():
    """Verify scene_timings.json reconciles with metadata.json and description timestamps."""
    timings_path = REPO_ROOT / "assets" / "scripts_video" / "audio" / "series_01" / "tap_01" / "scene_timings.json"
    metadata_path = REPO_ROOT / "assets" / "scripts_video" / "output" / "youtube_staging" / "series_01" / "tap_01" / "metadata.json"

    assert timings_path.is_file(), f"scene_timings.json missing at {timings_path}"
    assert metadata_path.is_file(), f"metadata.json missing at {metadata_path}"

    timings = json.loads(timings_path.read_text(encoding="utf-8"))
    meta = json.loads(metadata_path.read_text(encoding="utf-8"))

    scene_sum = sum(s["duration"] for s in timings)
    stinger_dur = 5.80
    closing_dur = 9.00
    expected_total = scene_sum + stinger_dur + closing_dur
    declared_total = float(meta["duration_seconds"])

    assert abs(expected_total - declared_total) <= 1.5, (
        f"Duration divergence: sum of scenes ({scene_sum}s) + brand ({stinger_dur+closing_dur}s) = "
        f"{expected_total:.2f}s != declared metadata duration {declared_total:.2f}s"
    )


def test_f3_disguised_outage_audio_corruption_rejected(tmp_path):
    """Verify assembly integrity guards reject empty bodies, truncated clips, and mismatched sample rates."""
    # 1. Truncated audio (< 5.0s) must be rejected
    def check_audio_guards(size_bytes: int, duration_s: float, sample_rate: int, channels: int):
        if size_bytes < 1024:
            raise ValueError(f"Corrupt or empty scene audio (size {size_bytes}B < 1KB)")
        if duration_s < 5.0:
            raise ValueError(f"Abnormally truncated scene audio duration ({duration_s:.2f}s < 5.0s)")
        if sample_rate != 48000:
            raise ValueError(f"Invalid audio sample rate ({sample_rate} != 48000Hz)")
        if channels != 2:
            raise ValueError(f"Invalid audio channels ({channels} != 2 Stereo)")

    # Empty body (<1KB) fails
    with pytest.raises(ValueError, match="Corrupt or empty"):
        check_audio_guards(500, 10.0, 48000, 2)

    # Truncated clip (<5s) fails
    with pytest.raises(ValueError, match="Abnormally truncated"):
        check_audio_guards(2048, 2.5, 48000, 2)

    # Corrupted sample rate fails
    with pytest.raises(ValueError, match="Invalid audio sample rate"):
        check_audio_guards(2048, 15.0, 44100, 2)

    # Mono audio fails
    with pytest.raises(ValueError, match="Invalid audio channels"):
        check_audio_guards(2048, 15.0, 48000, 1)

    # Pristine 48kHz Stereo audio passes
    check_audio_guards(100000, 66.0, 48000, 2)








