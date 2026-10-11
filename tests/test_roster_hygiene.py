"""Static Roster Hygiene & Historical Leak Prevention Test Suite.

Enforces:
1. fleet_roster.example.yml exists, is valid YAML, and provides documented templates.
2. pro-claude-pool NEVER contains any Ultra tier account or keyword in either example or active roster.
3. Git history is clean of untracked roster files (fleet_roster.yml, fleet_roster.json).
"""

import os
import subprocess
import sys
from pathlib import Path
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_ROSTER = REPO_ROOT / "fleet_roster.example.yml"
ACTIVE_ROSTER = REPO_ROOT / "fleet_roster.yml"

DEFAULTS_ROSTER = REPO_ROOT / "fleet_roster.defaults.yml"

ULTRA_IDENTIFIERS = {"ultra-1", "ultra-2", "lthn.ariana", "ariana"}


def test_example_roster_template_exists_and_valid():
    """Verify fleet_roster.example.yml is committed and adheres to canonical schema."""
    assert EXAMPLE_ROSTER.is_file(), "fleet_roster.example.yml must exist as committed template"
    with open(EXAMPLE_ROSTER, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert isinstance(data, dict), "Roster must parse to dictionary"
    assert "pools" in data, "Roster must define 'pools'"
    assert "pro-claude-pool" in data["pools"], "Must define 'pro-claude-pool'"
    assert "ultra-gemini-pool" in data["pools"], "Must define 'ultra-gemini-pool'"


def test_defaults_roster_template_exists_and_valid():
    """Verify fleet_roster.defaults.yml is present and adheres to canonical schema."""
    assert DEFAULTS_ROSTER.is_file(), "fleet_roster.defaults.yml must exist as topology fallback"
    with open(DEFAULTS_ROSTER, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert isinstance(data, dict), "Defaults roster must parse to dictionary"
    assert "pools" in data, "Defaults roster must define 'pools'"
    assert "pro-claude-pool" in data["pools"], "Must define 'pro-claude-pool'"
    assert "ultra-gemini-pool" in data["pools"], "Must define 'ultra-gemini-pool'"
    assert "nebula-pool" in data["pools"], "Must define 'nebula-pool'"


def test_no_ultra_account_in_example_claude_pool():
    """Verify pro-claude-pool in example roster contains zero Ultra accounts."""
    with open(EXAMPLE_ROSTER, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    nodes = data.get("pools", {}).get("pro-claude-pool", {}).get("nodes", [])
    for node in nodes:
        alias = str(node.get("alias", "")).lower()
        tier = str(node.get("tier", "")).lower()
        assert tier != "ultra", f"Ultra tier node '{alias}' found in pro-claude-pool!"
        assert not any(u in alias for u in ULTRA_IDENTIFIERS), (
            f"Ultra identifier found in pro-claude-pool alias: '{alias}'"
        )


def test_no_ultra_account_in_defaults_claude_pool():
    """Verify pro-claude-pool in defaults roster contains zero Ultra accounts."""
    with open(DEFAULTS_ROSTER, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    nodes = data.get("pools", {}).get("pro-claude-pool", {}).get("nodes", [])
    for node in nodes:
        alias = str(node.get("alias", "")).lower()
        tier = str(node.get("tier", "")).lower()
        assert tier != "ultra", f"Ultra tier node '{alias}' found in defaults pro-claude-pool!"
        assert not any(u in alias for u in ULTRA_IDENTIFIERS), (
            f"Ultra identifier found in defaults pro-claude-pool alias: '{alias}'"
        )


@pytest.mark.skipif(not ACTIVE_ROSTER.is_file(), reason="Active fleet_roster.yml not present on disk")
def test_no_ultra_account_in_active_claude_pool():
    """Static linter: verify active fleet_roster.yml pro-claude-pool has zero Ultra accounts."""
    with open(ACTIVE_ROSTER, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    nodes = data.get("pools", {}).get("pro-claude-pool", {}).get("nodes", [])
    for node in nodes:
        alias = str(node.get("alias", "")).lower()
        tier = str(node.get("tier", "")).lower()
        assert tier != "ultra", f"Ultra tier node '{alias}' found in active pro-claude-pool!"
        assert not any(u in alias for u in ULTRA_IDENTIFIERS), (
            f"Ultra identifier found in active pro-claude-pool alias: '{alias}'"
        )


def test_git_history_clean_of_roster_leaks():
    """Verify fleet_roster.yml, fleet_roster.json, .fleet_roster.json were NEVER committed to git."""
    cmd = [
        "git",
        "log",
        "--all",
        "--oneline",
        "--",
        "fleet_roster.yml",
        "fleet_roster.json",
        ".fleet_roster.json",
    ]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    assert proc.returncode == 0
    output = proc.stdout.strip()
    assert output == "", (
        f"SECURITY BREACH: Untracked roster files found in git history!\n{output}\n"
        f"Must purge with git-filter-repo and rotate any leaked credentials."
    )


def test_startup_roster_consistency_fails_closed_on_poisoned_roster(tmp_path: Path):
    """Dialectic Synthesis Guard: startup consistency check fails closed on poisoned roster."""
    from hermes_cli.routing_policy import verify_roster_consistency, RoutingViolation, assert_routing_allowed

    # 1. Clean synthetic roster should pass
    clean_roster = tmp_path / "clean_roster.yml"
    clean_data = {
        "version": "1.0",
        "pools": {
            "pro-claude-pool": {"nodes": [{"alias": "pro-node-1", "tier": "pro"}]},
            "ultra-gemini-pool": {"nodes": [{"alias": "ultra-2", "tier": "ultra"}]},
        },
    }
    clean_roster.write_text(yaml.dump(clean_data), encoding="utf-8")
    is_ok, violations = verify_roster_consistency(clean_roster, fail_closed=True)
    assert is_ok is True
    assert len(violations) == 0

    # 2. Poisoned roster with Ultra injected into pro-claude-pool MUST FAIL CLOSED
    poisoned_roster = tmp_path / "poisoned_roster.yml"
    poisoned_data = {
        "version": "1.0",
        "pools": {
            "pro-claude-pool": [
                {"alias": "pro-node-1", "tier": "pro"},
                {"alias": "ultra-2", "tier": "ultra"},  # POISON!
            ],
            "ultra-gemini-pool": [{"alias": "ultra-2", "tier": "ultra"}],
        },
    }
    # Fix dict format
    poisoned_data["pools"]["pro-claude-pool"] = {"nodes": [{"alias": "ultra-2", "tier": "ultra"}]}
    poisoned_roster.write_text(yaml.dump(poisoned_data), encoding="utf-8")

    is_ok, violations = verify_roster_consistency(poisoned_roster, fail_closed=False)
    assert is_ok is False
    assert len(violations) == 1
    assert "CRITICAL ROSTER DRIFT" in violations[0]

    with pytest.raises(RoutingViolation, match=r"CRITICAL ROSTER DRIFT.*Ultra account"):
        verify_roster_consistency(poisoned_roster, fail_closed=True)


def test_assert_routing_allowed_alias():
    """Verify assert_routing_allowed is an exact alias of assert_routing_legal."""
    from hermes_cli.routing_policy import assert_routing_allowed, assert_routing_legal, RoutingViolation

    assert assert_routing_allowed is assert_routing_legal
    with pytest.raises(RoutingViolation):
        assert_routing_allowed("ultra-2", "claude-opus-5-5-high")


def test_ci_scanner_script_clean_execution():
    """Verify scripts/ci_secret_and_roster_scan.py runs and exits with code 0."""
    script_path = REPO_ROOT / "scripts" / "ci_secret_and_roster_scan.py"
    assert script_path.is_file(), "Scanner script must exist"
    proc = subprocess.run([sys.executable, str(script_path)], cwd=REPO_ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, f"Scanner script failed: {proc.stdout}\n{proc.stderr}"
    assert "PASSED" in proc.stdout


