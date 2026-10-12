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

    # Validate mandatory keys
    missing = [k for k in _REQUIRED_KEYS if k not in data]
    if missing:
        raise ValueError(f"CRITICAL: fleet policy at '{target}' missing keys: {missing}")

    for k in _REQUIRED_KEYS:
        val = data[k]
        if not isinstance(val, list) or any(not isinstance(x, str) for x in val):
            raise ValueError(f"CRITICAL: fleet policy '{k}' must be a list[str] at '{target}'.")

    # Anti-fail-open escape hatch validation
    intentional = data.pop("excluded_intentionally_empty", False)
    if not isinstance(intentional, bool):
        raise ValueError(
            f"CRITICAL: 'excluded_intentionally_empty' must be a JSON bool at '{target}'."
        )
    if not data["excluded"] and not intentional:
        raise ValueError(
            f"CRITICAL: empty exclusion list at '{target}' without "
            "'excluded_intentionally_empty': true (refusing fail-open)."
        )

    # Validate optional routing dict structure
    if "routing" in data:
        routing = data["routing"]
        if not isinstance(routing, dict):
            raise ValueError(f"CRITICAL: fleet policy 'routing' must be a dict at '{target}'.")
        for rk, rv in routing.items():
            if not isinstance(rk, str):
                raise ValueError(f"CRITICAL: fleet policy 'routing' key '{rk}' must be a str at '{target}'.")
            if not isinstance(rv, (dict, list, str)):
                raise ValueError(f"CRITICAL: fleet policy 'routing' entry '{rk}' must be dict, list, or str at '{target}'.")
            if isinstance(rv, list) and any(not isinstance(x, str) for x in rv):
                raise ValueError(f"CRITICAL: fleet policy 'routing' list '{rk}' must contain str items at '{target}'.")

    # Validate optional list keys
    for opt_key in ("deploy_ok", "overdue_invoice"):
        if opt_key in data:
            opt_val = data[opt_key]
            if not isinstance(opt_val, list) or any(not isinstance(x, str) for x in opt_val):
                raise ValueError(f"CRITICAL: fleet policy '{opt_key}' must be list[str] at '{target}'.")

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


_FLEET_POLICY_CACHE: Optional[Dict[str, Any]] = None


def get_fleet_policy(*, refresh: bool = False, policy_path: Optional[Path] = None, strict: Optional[bool] = None) -> Dict[str, Any]:
    """Lazily load + memoize the policy. Import never crashes; first real
    use is still fail-closed per MODAL_FLEET_POLICY_FAILMODE."""
    global _FLEET_POLICY_CACHE
    if refresh or _FLEET_POLICY_CACHE is None or policy_path is not None:
        pol = load_fleet_policy(policy_path, strict=strict)
        if policy_path is None:
            _FLEET_POLICY_CACHE = pol
        return pol
    return _FLEET_POLICY_CACHE


def _policy_degraded(policy: Optional[Dict[str, Any]] = None) -> bool:
    """Returns True if the policy is in a degraded / tripped state."""
    pol = policy if policy is not None else get_fleet_policy()
    return bool(pol.get("_degraded"))


def is_excluded(workspace: str, policy: Optional[Dict[str, Any]] = None) -> bool:
    """Fail-closed membership check. In degraded state EVERYTHING is treated
    as excluded so no privileged action proceeds against a tripped breaker."""
    pol = policy if policy is not None else get_fleet_policy()
    if _policy_degraded(pol):
        return True  # degraded => exclude all; refuse operations
    return workspace in set(pol.get("excluded", []))


def is_deploy_blocked(workspace: str, policy: Optional[Dict[str, Any]] = None) -> bool:
    """Fail-closed deploy-blocked check. In degraded state ALL deployments are blocked."""
    pol = policy if policy is not None else get_fleet_policy()
    if _policy_degraded(pol):
        return True  # degraded => block all deploys
    return workspace in set(pol.get("deploy_blocked", []))


def __getattr__(name: str) -> Any:
    """Module-level attribute fallback for backward compatibility."""
    if name == "FLEET_POLICY":
        return get_fleet_policy()
    if name == "FLEET_EXCLUDED":
        pol = get_fleet_policy()
        return set(pol.get("excluded", []))
    if name == "FLEET_DEPLOY_BLOCKED":
        pol = get_fleet_policy()
        return set(pol.get("deploy_blocked", []))
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
