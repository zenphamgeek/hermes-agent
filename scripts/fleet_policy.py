#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/fleet_policy.py
=======================
Pure-Python, dependency-free Modal Fleet Policy loader, schema validator,
and circuit-breaker authorization boundary (CWE-862 guard).
Shared by both scripts/modal_fleet_server.py and scripts/modal_billing_sync.py.
"""

from pathlib import Path
import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger("fleet_policy")

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FLEET_POLICY_PATH = REPO_ROOT / "output" / "modal_fleet_policy.json"

# Explicit degraded state. Consumers MUST check `_degraded` and refuse operations.
# Do NOT rely on list wildcards: `excluded` is a blocklist and would fail OPEN.
_POLICY_DENY_ALL: Dict[str, Any] = {
    "excluded": [],
    "deploy_blocked": [],
    "deploy_ok": [],
    "routing": {},
    "overdue_invoice": [],
    "_degraded": True,
}

_REQUIRED_KEYS = ("excluded", "deploy_blocked")


def _validate_policy(data: Any, target: Path) -> Dict[str, Any]:
    """Validates policy schema integrity, strips disk-supplied _degraded,
    and protects against empty blocklist fail-open vulnerability (F2, F7).
    """
    if not isinstance(data, dict):
        raise ValueError(f"CRITICAL: fleet policy at '{target}' is not a JSON object.")

    # F2: System-controlled only; never trust _degraded from disk
    data.pop("_degraded", None)

    missing = [k for k in _REQUIRED_KEYS if k not in data]
    if missing:
        raise ValueError(f"CRITICAL: fleet policy at '{target}' missing keys: {missing}")

    for k in _REQUIRED_KEYS:
        val = data[k]
        if not isinstance(val, list) or any(not isinstance(x, str) for x in val):
            raise ValueError(f"CRITICAL: fleet policy '{k}' must be a list[str] at '{target}'.")

    # F2 Anti-Fail-Open: empty exclusion list without explicit intent is rejected
    if not data["excluded"] and not data.get("excluded_intentionally_empty"):
        raise ValueError(
            f"CRITICAL: empty exclusion list at '{target}' without "
            "'excluded_intentionally_empty': true (refusing fail-open)."
        )

    return data


def load_fleet_policy(policy_path: Optional[Path] = None, *, strict: Optional[bool] = None) -> Dict[str, Any]:
    """Fail-closed policy loader (CWE-862).
    strict=True  -> raise on missing/invalid policy (hard fail).
    strict=False -> trip circuit breaker to _POLICY_DENY_ALL (degraded, operations refused).
    Default from MODAL_FLEET_POLICY_FAILMODE env ('crash' | 'deny_all'), defaulting to 'crash'.
    """
    if strict is None:
        strict = os.environ.get("MODAL_FLEET_POLICY_FAILMODE", "crash").strip().lower() != "deny_all"
    target = policy_path or DEFAULT_FLEET_POLICY_PATH
    try:
        if not target.exists():
            raise FileNotFoundError(f"policy file missing at '{target}'")
        data = json.loads(target.read_text(encoding="utf-8"))
        return _validate_policy(data, target)
    except Exception as e:
        logger.critical("Fleet policy load failed (mode=%s): %s", "strict" if strict else "degraded", e)
        if strict:
            raise RuntimeError(f"CRITICAL: fleet policy unusable at '{target}': {e}") from e
        return dict(_POLICY_DENY_ALL)


def _policy_degraded(policy: Optional[Dict[str, Any]] = None) -> bool:
    """Returns True if the policy is in a degraded / tripped state."""
    pol = policy if policy is not None else FLEET_POLICY
    return bool(pol.get("_degraded"))


FLEET_POLICY = load_fleet_policy()
FLEET_EXCLUDED = set(FLEET_POLICY.get("excluded", []))
FLEET_DEPLOY_BLOCKED = set(FLEET_POLICY.get("deploy_blocked", []))
