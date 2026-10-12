#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_modal_fleet_policy_integrity.py
==========================================
Unit test suite verifying Modal Fleet Policy Authorization Boundary (CWE-862):
1. Confirms output/modal_fleet_policy.json exists and adheres to required schema.
2. Verifies fail-closed enforcement when policy is missing or strict.
3. Verifies circuit-breaker trip to _POLICY_DENY_ALL with _degraded flag.
4. Verifies schema validation (non-object, missing keys, non-string entries, routing typing).
5. Verifies empty exclusion list fail-open prevention (F2) and intent flag.
6. Verifies disk-supplied _degraded is stripped and not trusted (F2).
7. Verifies standalone scripts.fleet_policy module is decoupled from HTTP server (F1).
8. Verifies modal_billing_sync refuses operations when degraded or missing (F6).
9. Verifies shared probe lock identity (F5 fix) and serialized concurrency.
10. Verifies probe state hydration from persistent ledger (F3).
11. Verifies degraded policy blocks profile discovery and worker registration.
12. Verifies fail-closed accessors (is_excluded, is_deploy_blocked) exclude everything when degraded.
13. Verifies module reload does not crash when policy file is absent (import bulkhead).
"""

import importlib
import json
from pathlib import Path
import threading
import time
import pytest

import scripts.fleet_policy as fp
from scripts.fleet_policy import (
    load_fleet_policy,
    get_fleet_policy,
    DEFAULT_FLEET_POLICY_PATH,
    _policy_degraded,
    is_excluded,
    is_deploy_blocked,
)
from scripts.modal_billing_sync import ModalBillingSyncEngine

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_POLICY_PATH = REPO_ROOT / "output" / "modal_fleet_policy.json"


def _write_policy(tmp_path: Path, obj: dict) -> Path:
    p = tmp_path / "modal_fleet_policy.json"
    p.write_text(json.dumps(obj), encoding="utf-8")
    return p


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
    assert not policy.get("_degraded")


def test_missing_policy_strict_raises(tmp_path):
    """Verify load_fleet_policy raises RuntimeError when policy is missing in strict mode (F4)."""
    with pytest.raises(RuntimeError) as exc_info:
        load_fleet_policy(tmp_path / "nope.json", strict=True)
    assert "unusable" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()


def test_missing_policy_degraded_trips(tmp_path):
    """Verify load_fleet_policy returns _POLICY_DENY_ALL with _degraded=True when strict=False (F4)."""
    p = load_fleet_policy(tmp_path / "nope.json", strict=False)
    assert isinstance(p, dict)
    assert p.get("_degraded") is True
    assert "excluded" in p
    assert "deploy_blocked" in p


def test_malformed_json(tmp_path):
    """Verify malformed JSON raises error in strict mode."""
    f = tmp_path / "p.json"
    f.write_text("{ not json", encoding="utf-8")
    with pytest.raises((ValueError, RuntimeError)):
        load_fleet_policy(f, strict=True)


def test_non_object_rejected(tmp_path):
    """Verify non-dict JSON root is rejected."""
    f = tmp_path / "p.json"
    f.write_text("[]", encoding="utf-8")
    with pytest.raises((ValueError, RuntimeError)):
        load_fleet_policy(f, strict=True)


def test_missing_deploy_blocked(tmp_path):
    """Verify missing deploy_blocked key is rejected (schema parity F6)."""
    f = tmp_path / "p.json"
    f.write_text(json.dumps({"excluded": ["motion"]}), encoding="utf-8")
    with pytest.raises((ValueError, RuntimeError)):
        load_fleet_policy(f, strict=True)


def test_non_string_entries(tmp_path):
    """Verify non-string blocklist entry is rejected (type validation F7)."""
    f = tmp_path / "p.json"
    f.write_text(json.dumps({"excluded": [123], "deploy_blocked": []}), encoding="utf-8")
    with pytest.raises((ValueError, RuntimeError)):
        load_fleet_policy(f, strict=True)


def test_empty_exclusion_without_intent_is_rejected(tmp_path):
    """Verify empty exclusion list without explicit intent fails closed (F2 anti-fail-open)."""
    p = _write_policy(tmp_path, {"excluded": [], "deploy_blocked": []})
    with pytest.raises((ValueError, RuntimeError)):
        load_fleet_policy(p, strict=True)

    # In degraded mode, trips to _degraded: True
    pol = load_fleet_policy(p, strict=False)
    assert pol.get("_degraded") is True


def test_empty_exclusion_with_intent_is_accepted(tmp_path):
    """Verify empty exclusion list with explicit intent flag is accepted (F2)."""
    p = _write_policy(tmp_path, {
        "excluded": [],
        "deploy_blocked": [],
        "excluded_intentionally_empty": True,
    })
    pol = load_fleet_policy(p, strict=True)
    assert pol["excluded"] == []
    assert not pol.get("_degraded")


def test_empty_excluded_with_nonbool_flag_is_rejected(tmp_path):
    """Verify non-boolean excluded_intentionally_empty is rejected."""
    p = _write_policy(tmp_path, {
        "excluded": [],
        "deploy_blocked": [],
        "excluded_intentionally_empty": "true",
    })
    with pytest.raises((ValueError, RuntimeError)):
        load_fleet_policy(p, strict=True)


def test_disk_supplied_degraded_is_stripped(tmp_path):
    """Verify _degraded supplied from disk is stripped and not trusted (F2)."""
    p = _write_policy(tmp_path, {
        "excluded": ["motion"],
        "deploy_blocked": [],
        "_degraded": False,
    })
    pol = load_fleet_policy(p, strict=True)
    assert "_degraded" not in pol


def test_deny_all_mode_trips_breaker_on_missing_file(tmp_path):
    """Verify deny_all mode returns degraded policy without raising."""
    missing = tmp_path / "nope.json"
    pol = load_fleet_policy(missing, strict=False)
    assert _policy_degraded(pol) is True


def test_degraded_policy_excludes_everything(tmp_path):
    """Verify fail-closed membership accessors treat everything as excluded/blocked when degraded."""
    missing = tmp_path / "nope.json"
    pol = load_fleet_policy(missing, strict=False)
    assert is_excluded("any-workspace", pol) is True
    assert is_deploy_blocked("any-workspace", pol) is True


def test_routing_must_be_str_mapping(tmp_path):
    """Verify routing dict entries must not contain primitive numbers (injection guard)."""
    p = _write_policy(tmp_path, {
        "excluded": ["ws"],
        "deploy_blocked": [],
        "routing": {"job": 42},
    })
    with pytest.raises((ValueError, RuntimeError)):
        load_fleet_policy(p, strict=True)


def test_import_does_not_crash_when_policy_missing(monkeypatch, tmp_path):
    """Verify importing/reloading fleet_policy does not crash even if policy is missing (bulkhead)."""
    monkeypatch.setenv("MODAL_FLEET_POLICY_FAILMODE", "crash")
    monkeypatch.setattr(fp, "DEFAULT_FLEET_POLICY_PATH", tmp_path / "absent.json")
    # Must not raise during reload because loader is lazy
    importlib.reload(fp)


def test_fleet_policy_standalone_module_decoupled():
    """Verify scripts.fleet_policy is standalone and does not import network/HTTP servers (F1)."""
    assert hasattr(fp, "load_fleet_policy")
    assert hasattr(fp, "get_fleet_policy")
    assert hasattr(fp, "_validate_policy")
    assert hasattr(fp, "_policy_degraded")
    assert hasattr(fp, "is_excluded")
    assert hasattr(fp, "is_deploy_blocked")
    assert "http.server" not in fp.__dict__
    assert "socketserver" not in fp.__dict__


def test_billing_sync_refuses_when_degraded(monkeypatch, tmp_path):
    """Verify billing-sync fails closed when policy is degraded (F6)."""
    monkeypatch.setenv("MODAL_FLEET_POLICY_FAILMODE", "deny_all")
    engine = ModalBillingSyncEngine(
        modal_config_path=tmp_path / "fake_modal.toml",
        fleet_policy_path=tmp_path / "non_existent.json",
    )
    with pytest.raises(RuntimeError) as exc_info:
        engine._get_configured_profiles()
    assert "degraded" in str(exc_info.value).lower() or "fail-closed" in str(exc_info.value).lower()


def test_modal_billing_sync_fails_closed_when_policy_missing(tmp_path, monkeypatch):
    """Verify ModalBillingSyncEngine._get_configured_profiles raises RuntimeError when policy is missing."""
    engine = ModalBillingSyncEngine(modal_config_path=tmp_path / "fake_modal.toml")

    fake_parent = tmp_path / "fake_repo"
    fake_parent.mkdir(parents=True, exist_ok=True)
    fake_script = fake_parent / "scripts" / "modal_billing_sync.py"
    fake_script.parent.mkdir(parents=True, exist_ok=True)
    fake_script.write_text("# dummy", encoding="utf-8")

    import scripts.modal_billing_sync as mbs_mod
    monkeypatch.setattr(mbs_mod, "__file__", str(fake_script))

    with pytest.raises(RuntimeError):
        engine._get_configured_profiles()


def test_probe_lock_is_shared():
    """Verify _PROBE_LOCK and _PROBE_STATE share identity with MONITOR_PROBE_LOCK/STATE (F5)."""
    import scripts.modal_fleet_server as s
    assert s._PROBE_LOCK is not None
    if hasattr(s, "MONITOR_PROBE_LOCK"):
        assert s._PROBE_LOCK is s.MONITOR_PROBE_LOCK, "F5 regression: _PROBE_LOCK is not shared"
    if hasattr(s, "MONITOR_PROBE_STATE"):
        assert s._PROBE_STATE is s.MONITOR_PROBE_STATE, "F5 regression: _PROBE_STATE is not shared"


def test_probe_lock_concurrency_serialization():
    """Verify _PROBE_LOCK provides real mutual exclusion across concurrent threads (F5)."""
    import scripts.modal_fleet_server as s

    counter = 0
    max_concurrent = 0
    lock = s._PROBE_LOCK

    def worker():
        nonlocal counter, max_concurrent
        with lock:
            counter += 1
            if counter > max_concurrent:
                max_concurrent = counter
            time.sleep(0.005)
            counter -= 1

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert max_concurrent == 1, f"Lock failed to serialize execution, max concurrent was {max_concurrent}"


def test_probe_state_hydrates_from_disk_persistence():
    """Verify _PROBE_STATE hydrates from disk persistence file (F3)."""
    import scripts.modal_fleet_server as s
    assert s._PROBE_STATE is not None
    assert isinstance(s._PROBE_STATE, dict)
    assert "date" in s._PROBE_STATE or "count" in s._PROBE_STATE


def test_policy_degraded_blocks_operations(monkeypatch):
    """Verify _policy_degraded flag blocks profile discovery and worker registration."""
    import scripts.modal_fleet_server as s

    assert s._policy_degraded({"_degraded": True}) is True
    assert s._policy_degraded({"_degraded": False}) is False
    assert s._policy_degraded({}) is False

    # When policy is degraded, get_toml_profiles returns empty list (refuses discovery)
    monkeypatch.setattr(s, "FLEET_POLICY", {"_degraded": True, "excluded": []})
    assert s.get_toml_profiles() == []

    # When policy is degraded, register_hotplug_worker raises RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        s.register_hotplug_worker({
            "worker_id": "test-w",
            "workspace": "zenpeace",
            "gpu_tier": "T4",
            "endpoint_url": "https://test.example.com",
            "app_name": "test-app",
        })
    assert "degraded" in str(exc_info.value).lower()
