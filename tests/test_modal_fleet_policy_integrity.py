#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_modal_fleet_policy_integrity.py
==========================================
Unit test suite verifying Modal Fleet Policy Authorization Boundary (CWE-862):
1. Confirms output/modal_fleet_policy.json exists and adheres to required schema.
2. Verifies fail-closed enforcement when policy is missing (refuses permissive defaults).
3. Verifies schema validation and rejection of empty/malformed policy files.
4. Verifies scripts/modal_billing_sync fails closed if fleet policy is missing.
"""

import json
from pathlib import Path
import pytest

from scripts.modal_fleet_server import (
    load_fleet_policy,
    DEFAULT_FLEET_POLICY_PATH,
)
from scripts.modal_billing_sync import ModalBillingSyncEngine

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_POLICY_PATH = REPO_ROOT / "output" / "modal_fleet_policy.json"


def test_canonical_modal_fleet_policy_exists_and_valid():
    """Verify canonical modal_fleet_policy.json exists on disk and has valid schema."""
    assert CANONICAL_POLICY_PATH.exists(), f"Missing required policy file at {CANONICAL_POLICY_PATH}"
    data = json.loads(CANONICAL_POLICY_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "excluded" in data, "Missing 'excluded' in modal_fleet_policy.json"
    assert "deploy_blocked" in data, "Missing 'deploy_blocked' in modal_fleet_policy.json"
    assert "deploy_ok" in data, "Missing 'deploy_ok' in modal_fleet_policy.json"
    assert "routing" in data, "Missing 'routing' in modal_fleet_policy.json"

    # Invariant: 'motion' workspace must be excluded
    assert "motion" in data["excluded"], "'motion' must be listed in excluded workspaces"


def test_load_fleet_policy_loads_canonical_successfully():
    """Verify load_fleet_policy loads canonical file and returns valid dict."""
    policy = load_fleet_policy()
    assert isinstance(policy, dict)
    assert "excluded" in policy
    assert "motion" in policy["excluded"]


def test_load_fleet_policy_fails_closed_when_file_missing(tmp_path):
    """Verify load_fleet_policy raises RuntimeError when policy file is absent (CWE-862)."""
    missing_file = tmp_path / "non_existent_policy.json"
    with pytest.raises(RuntimeError) as exc_info:
        load_fleet_policy(missing_file)
    assert "CWE-862 fail-closed guard" in str(exc_info.value)
    assert "missing" in str(exc_info.value)


def test_load_fleet_policy_fails_closed_on_invalid_json(tmp_path):
    """Verify load_fleet_policy raises ValueError when file contains malformed JSON."""
    bad_json_file = tmp_path / "corrupt_policy.json"
    bad_json_file.write_text("{ this is not valid json", encoding="utf-8")
    with pytest.raises(ValueError) as exc_info:
        load_fleet_policy(bad_json_file)
    assert "Failed parsing Modal fleet policy JSON" in str(exc_info.value)


def test_load_fleet_policy_fails_closed_on_missing_schema_keys(tmp_path):
    """Verify load_fleet_policy rejects empty dict or missing mandatory schema keys."""
    empty_schema_file = tmp_path / "empty_policy.json"
    empty_schema_file.write_text(json.dumps({"some_key": "val"}), encoding="utf-8")
    with pytest.raises(ValueError) as exc_info:
        load_fleet_policy(empty_schema_file)
    assert "missing mandatory 'excluded' or 'deploy_blocked'" in str(exc_info.value)


def test_modal_billing_sync_fails_closed_when_policy_missing(tmp_path, monkeypatch):
    """Verify ModalBillingSyncEngine._get_configured_profiles raises RuntimeError when policy is missing."""
    engine = ModalBillingSyncEngine(modal_config_path=tmp_path / "fake_modal.toml")

    # Point to a missing path
    fake_parent = tmp_path / "fake_repo"
    fake_parent.mkdir(parents=True, exist_ok=True)
    fake_script = fake_parent / "scripts" / "modal_billing_sync.py"
    fake_script.parent.mkdir(parents=True, exist_ok=True)
    fake_script.write_text("# dummy", encoding="utf-8")

    import scripts.modal_billing_sync as mbs_mod
    monkeypatch.setattr(mbs_mod, "__file__", str(fake_script))

    with pytest.raises(RuntimeError) as exc_info:
        engine._get_configured_profiles()
    assert "Modal fleet policy missing" in str(exc_info.value)
