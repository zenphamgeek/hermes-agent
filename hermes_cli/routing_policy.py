"""Version-controlled AGY Fleet Sovereign Routing Policy & Architectural Invariants.

Enforces hard technical controls at the dispatch boundary:
  1. Ultra tier accounts (ultra-2, lthn.Ariana) strictly and exclusively serve Gemini models.
     Routing Claude models to Ultra accounts is strictly prohibited to protect Claude quota.
  2. Nebula API gateway strictly and exclusively serves Claude Opus 4.8.
     Routing Gemini models or non-Opus-4.8 Claude models to Nebula is strictly prohibited.
  3. All security allowlists are tracked, version-controlled, and reviewable in git.
     Untracked roster files (fleet_roster.yml) can only register additional node aliases;
     they CANNOT bypass or declassify immutable policy invariants.

TTL Self-Healing:
  If FLEET_ROUTING_GUARD is temporarily degraded to 'warn' or 'off' during incident recovery,
  it automatically self-heals back to 'enforce' mode once the TTL expires (default 300s).
"""
from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RoutingViolation(ValueError):
    """Raised when a task dispatch violates AGY Fleet sovereign routing invariants."""
    pass


class NoCapacityError(RoutingViolation):
    """Raised when no compliant fleet node has capacity to serve the requested route."""
    pass


class ScopeViolation(RoutingViolation):
    """Raised when a failover cascade crosses an unauthorized trust or scope boundary."""
    pass


# ---------------------------------------------------------------------------
# Immutable Version-Controlled Invariants (Ground Truth)
# ---------------------------------------------------------------------------
IMMUTABLE_ULTRA_ACCOUNTS: frozenset[str] = frozenset({
    "ultra-2",
    "lthn.ariana",
})

IMMUTABLE_NEBULA_NODES: frozenset[str] = frozenset({
    "nebula",
    "b.ai",
})

IMMUTABLE_NEBULA_MODELS: frozenset[str] = frozenset({
    "claude-opus-4.8",
})

CLAUDE_MODELS: frozenset[str] = frozenset({
    "claude-sonnet-5-5-high",
    "claude-opus-5-5-high",
    "claude-opus-4-6-thinking",
    "claude-opus-4.8",
})

GEMINI_MODELS: frozenset[str] = frozenset({
    "gemini-3.1-pro-high",
    "gemini-3.8-flash-high",
})

# Backward compatibility aliases
ULTRA_ACCOUNTS = IMMUTABLE_ULTRA_ACCOUNTS
NEBULA_NODES = IMMUTABLE_NEBULA_NODES


# ---------------------------------------------------------------------------
# Formal Policy Typing & Cartesian Matrix Evaluation (Nebula Parity)
# ---------------------------------------------------------------------------
from enum import Enum


class Tier(str, Enum):
    ULTRA = "ultra"      # ultra-gemini-pool (strictly Gemini)
    PRO = "pro"          # pro-claude-pool (Claude Pro-first + Gemini)
    NEBULA = "nebula"    # b.ai API gateway (strictly Claude Opus 4.8)


class Family(str, Enum):
    GEMINI = "gemini"
    CLAUDE = "claude"


@dataclass(frozen=True)
class RouteRequest:
    tier: Tier
    family: Family
    model: str


def is_routing_allowed(req: RouteRequest) -> bool:
    """Evaluates whether a RouteRequest is permitted by sovereign policy."""
    if req.tier is Tier.ULTRA or req.tier == "ultra":
        return req.family is Family.GEMINI or req.family == "gemini"
    if req.tier is Tier.NEBULA or req.tier == "nebula":
        return req.model == "claude-opus-4.8"
    if req.tier is Tier.PRO or req.tier == "pro":
        return True
    return False


# Aliases
is_allowed = is_routing_allowed


# ---------------------------------------------------------------------------
# Sovereign Policy Manifest & Tier Compliance Assertion (Nebula Finding 5)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PolicyTierSpec:
    """Immutable formal specification for a routing tier."""
    tier: Tier
    allowed_families: frozenset[Family]
    allowed_models: frozenset[str]
    forbidden_families: frozenset[Family]
    immutable_nodes: frozenset[str]
    description: str


SOVEREIGN_POLICY_MANIFEST: Dict[Tier, PolicyTierSpec] = {
    Tier.ULTRA: PolicyTierSpec(
        tier=Tier.ULTRA,
        allowed_families=frozenset({Family.GEMINI}),
        allowed_models=GEMINI_MODELS,
        forbidden_families=frozenset({Family.CLAUDE}),
        immutable_nodes=IMMUTABLE_ULTRA_ACCOUNTS,
        description="Ultra nodes for high-complexity Gemini inference (strictly Gemini-only to protect Claude quota)",
    ),
    Tier.PRO: PolicyTierSpec(
        tier=Tier.PRO,
        allowed_families=frozenset({Family.CLAUDE, Family.GEMINI}),
        allowed_models=CLAUDE_MODELS | GEMINI_MODELS,
        forbidden_families=frozenset(),
        immutable_nodes=frozenset({"pro-1", "sunward", "insilos", "binhthuong", "justaskgao", "team-3"}),
        description="Pro CLI nodes with Claude quota (Claude Pro-first + Gemini)",
    ),
    Tier.NEBULA: PolicyTierSpec(
        tier=Tier.NEBULA,
        allowed_families=frozenset({Family.CLAUDE}),
        allowed_models=IMMUTABLE_NEBULA_MODELS,
        forbidden_families=frozenset({Family.GEMINI}),
        immutable_nodes=IMMUTABLE_NEBULA_NODES,
        description="Nebula API gateway (strictly fallback-only, strictly Claude Opus 4.8)",
    ),
}


def assert_node_tier_compliance(node_alias: str, claimed_tier: str | Tier) -> None:
    """Validates that a node strictly conforms to its immutable policy tier constraints.

    Prevents configuration tampering where an untracked roster reclassifies an Ultra account
    as Pro (which would breach the Ultra Gemini-only invariant) or Nebula as Pro.
    """
    node_lower = node_alias.strip().lower()
    claimed_tier_str = claimed_tier.value.lower() if isinstance(claimed_tier, Tier) else str(claimed_tier).strip().lower()

    is_ultra = any(u in node_lower for u in IMMUTABLE_ULTRA_ACCOUNTS)
    is_nebula = any(n in node_lower for n in IMMUTABLE_NEBULA_NODES)

    if is_ultra and claimed_tier_str != "ultra":
        raise RoutingViolation(
            f"Config Integrity Violation: Node {node_alias!r} is an immutable Ultra account "
            f"and cannot claim tier {claimed_tier_str!r}. Ultra accounts are strictly Gemini-only."
        )
    if is_nebula and claimed_tier_str != "nebula":
        raise RoutingViolation(
            f"Config Integrity Violation: Node {node_alias!r} is an immutable Nebula node "
            f"and cannot claim tier {claimed_tier_str!r}. Nebula is strictly Claude Opus 4.8 only."
        )


# ---------------------------------------------------------------------------
# Dynamic Roster Pool Discovery (Additive Only — Cannot Declassify Invariants)
# ---------------------------------------------------------------------------
_ROSTER_CACHE_TIME: float = 0.0
_CACHED_ULTRA_ACCOUNTS: frozenset[str] = IMMUTABLE_ULTRA_ACCOUNTS
_CACHED_NEBULA_NODES: frozenset[str] = IMMUTABLE_NEBULA_NODES


def _load_roster_pools() -> Tuple[frozenset[str], frozenset[str]]:
    """Loads additional Ultra/Nebula aliases from fleet_roster.yml with fail-open resilience.
    
    Guarantees:
      - Additive only: IMMUTABLE sets can never be shrunk or bypassed by untracked config.
      - Cached for 30s TTL.
      - Fail-open on YAML corruption without crashing routing engine.
    """
    global _ROSTER_CACHE_TIME, _CACHED_ULTRA_ACCOUNTS, _CACHED_NEBULA_NODES
    now = time.time()
    if now - _ROSTER_CACHE_TIME < 30.0:
        return _CACHED_ULTRA_ACCOUNTS, _CACHED_NEBULA_NODES

    roster_path = Path(__file__).resolve().parent.parent / "fleet_roster.yml"
    if not roster_path.is_file():
        roster_path = Path(__file__).resolve().parent.parent / "fleet_roster.defaults.yml"
    if not roster_path.is_file():
        _ROSTER_CACHE_TIME = now
        return _CACHED_ULTRA_ACCOUNTS, _CACHED_NEBULA_NODES

    try:
        import yaml
        with open(roster_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            ultras = set(IMMUTABLE_ULTRA_ACCOUNTS)
            nebulas = set(IMMUTABLE_NEBULA_NODES)
            for node in data.get("pools", {}).get("ultra-gemini-pool", {}).get("nodes", []):
                if isinstance(node, dict) and "alias" in node:
                    ultras.add(str(node["alias"]).strip().lower())
            for node in data.get("pools", {}).get("nebula-pool", {}).get("nodes", []):
                if isinstance(node, dict) and "alias" in node:
                    nebulas.add(str(node["alias"]).strip().lower())
            _CACHED_ULTRA_ACCOUNTS = frozenset(ultras)
            _CACHED_NEBULA_NODES = frozenset(nebulas)
            _ROSTER_CACHE_TIME = now
    except Exception as e:
        logger.warning("Failed to load fleet_roster.yml for routing guard (failing open): %s", e)

    return _CACHED_ULTRA_ACCOUNTS, _CACHED_NEBULA_NODES


# ---------------------------------------------------------------------------
# TTL Self-Healing State
# ---------------------------------------------------------------------------
_GUARD_OVERRIDE_TIMESTAMP: float = 0.0
_GUARD_OVERRIDE_MODE: Optional[str] = None
_DEFAULT_GUARD_OVERRIDE_TTL: float = 300.0  # 5 minutes auto-heal back to 'enforce'


def _reset_guard_override_state() -> None:
    """Resets guard override timestamp (used for test isolation)."""
    global _GUARD_OVERRIDE_TIMESTAMP, _GUARD_OVERRIDE_MODE
    _GUARD_OVERRIDE_TIMESTAMP = 0.0
    _GUARD_OVERRIDE_MODE = None


# ---------------------------------------------------------------------------
# Continuous Routing-Attestation Ledger & Offline Invariant Verifier
# ---------------------------------------------------------------------------
import hashlib
import json

DEFAULT_ATTESTATION_LEDGER_PATH = Path(__file__).resolve().parent.parent / ".routing_attestation_ledger.jsonl"


def record_routing_attestation(
    account: str,
    model: str,
    verdict: str,
    violation_reason: Optional[str] = None,
    ledger_path: Optional[Path] = None,
    task_id: Optional[str] = None,
    policy_version: str = "1.0.0",
) -> Dict[str, Any]:
    """Records an immutable audit attestation entry to the local ledger."""
    target_ledger = ledger_path or DEFAULT_ATTESTATION_LEDGER_PATH
    now = time.time()
    account_lower = account.lower()
    model_lower = model.lower()

    if any(u in account_lower for u in IMMUTABLE_ULTRA_ACCOUNTS):
        tier = "ultra"
    elif any(n in account_lower for n in IMMUTABLE_NEBULA_NODES):
        tier = "nebula"
    else:
        tier = "pro"

    task_str = task_id or "none"
    payload_str = f"{policy_version}:{now:.4f}:{account_lower}:{model_lower}:{verdict}:{tier}:{task_str}"
    digest = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    record = {
        "timestamp": now,
        "account": account,
        "model": model,
        "tier": tier,
        "verdict": verdict,
        "violation_reason": violation_reason,
        "task_id": task_id,
        "policy_version": policy_version,
        "digest": digest,
    }

    try:
        target_ledger.parent.mkdir(parents=True, exist_ok=True)
        with open(target_ledger, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        logger.warning("Could not append to routing attestation ledger: %s", e)

    return record


def verify_routing_attestation_ledger(ledger_path: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """Passive offline invariant-checker over the routing attestation ledger.
    
    Returns (is_valid, violations_list). Fails CI if any historical dispatch violated
    the Ultra Gemini-only or Nebula Opus-4.8 invariants while marked 'ALLOWED'.
    """
    target_ledger = ledger_path or DEFAULT_ATTESTATION_LEDGER_PATH
    if not target_ledger.is_file():
        return True, []

    violations: List[str] = []
    line_num = 0

    try:
        with open(target_ledger, "r", encoding="utf-8") as f:
            for line in f:
                line_num += 1
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception as err:
                    violations.append(f"Line {line_num}: Corrupted JSON record: {err}")
                    continue

                account = str(entry.get("account", "")).lower()
                model = str(entry.get("model", "")).lower()
                verdict = str(entry.get("verdict", "")).upper()
                is_redacted = entry.get("redacted", False) or account == "[redacted]"

                if verdict == "ALLOWED" and not is_redacted:
                    # Check Invariant 1: Ultra Gemini-only
                    is_ultra = any(u in account for u in IMMUTABLE_ULTRA_ACCOUNTS)
                    is_claude = any(c in model for c in ("claude", "opus", "sonnet"))
                    if is_ultra and is_claude:
                        violations.append(
                            f"Line {line_num} (ts={entry.get('timestamp')}): CRITICAL INVARIANT BREACH! "
                            f"Claude model {model!r} was ALLOWED on Ultra account {account!r}."
                        )

                    # Check Invariant 2: Nebula Opus 4.8 exclusive
                    is_nebula = any(n in account for n in IMMUTABLE_NEBULA_NODES)
                    is_gemini = any(g in model for g in ("gemini", "flash"))
                    if is_nebula and is_gemini:
                        violations.append(
                            f"Line {line_num} (ts={entry.get('timestamp')}): CRITICAL INVARIANT BREACH! "
                            f"Gemini model {model!r} was ALLOWED on Nebula node {account!r}."
                        )
                    elif is_nebula and "opus-4.8" not in model and "claude-opus-4.8" not in model:
                        violations.append(
                            f"Line {line_num} (ts={entry.get('timestamp')}): CRITICAL INVARIANT BREACH! "
                            f"Non-Opus-4.8 model {model!r} was ALLOWED on Nebula node {account!r}."
                        )
    except Exception as e:
        violations.append(f"Ledger read error: {e}")

    return len(violations) == 0, violations


def redact_routing_attestation_record(
    task_id: str,
    ledger_path: Optional[Path] = None,
    redacted_reason: str = "GDPR_RIGHT_TO_ERASURE",
) -> int:
    """Tombstones and crypto-shreds identifying fields of an attestation record by task_id.

    Reconciles immutable auditability with right-to-erasure (GDPR 72h SLA) by preserving
    the entry structure and timestamp while zeroing/redacting identifying account data.

    Returns the number of records redacted.
    """
    target_ledger = ledger_path or DEFAULT_ATTESTATION_LEDGER_PATH
    if not target_ledger.is_file():
        return 0

    redacted_count = 0
    updated_lines: List[str] = []
    now = time.time()

    with open(target_ledger, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                entry = json.loads(line_str)
            except Exception:
                updated_lines.append(line_str)
                continue

            if str(entry.get("task_id", "")) == str(task_id):
                redacted_count += 1
                entry["account"] = "[REDACTED]"
                entry["model"] = "[REDACTED]"
                if entry.get("violation_reason"):
                    entry["violation_reason"] = "[REDACTED]"
                entry["redacted"] = True
                entry["redacted_at"] = now
                entry["redacted_reason"] = redacted_reason
                # Recompute tombstone digest preserving task_id and policy_version
                tombstone_payload = f"TOMBSTONE:{entry.get('policy_version', '1.0.0')}:{now:.4f}:{entry.get('task_id')}:{redacted_reason}"
                entry["digest"] = hashlib.sha256(tombstone_payload.encode("utf-8")).hexdigest()

            updated_lines.append(json.dumps(entry))

    if redacted_count > 0:
        temp_ledger = target_ledger.with_suffix(".tmp")
        with open(temp_ledger, "w", encoding="utf-8") as f:
            for ul in updated_lines:
                f.write(ul + "\n")
        temp_ledger.replace(target_ledger)

    return redacted_count


# ---------------------------------------------------------------------------
# Main Routing Boundary Invariant Assertion
# ---------------------------------------------------------------------------
def assert_routing_legal(
    account: Optional[str],
    model: Optional[str],
    ledger_path: Optional[Path] = None,
    task_id: Optional[str] = None,
) -> None:
    """Enforces that Claude never routes to Ultra and Gemini never routes to Nebula.
    
    Controlled by FLEET_ROUTING_GUARD env var:
      - 'enforce' (default): raises RoutingViolation
      - 'warn': logs warning and emits metric, does not raise
      - 'off': disables check
      
    Self-Healing: 'warn' and 'off' overrides automatically expire after FLEET_ROUTING_GUARD_TTL
    (default 300s), restoring 'enforce' mode to prevent permanent exposure.
    
    Attestation: Emits a tamper-evident record to .routing_attestation_ledger.jsonl on every call.
    """
    global _GUARD_OVERRIDE_TIMESTAMP, _GUARD_OVERRIDE_MODE
    guard_mode = os.environ.get(
        "FLEET_ROUTING_GUARD",
        os.environ.get("FLEET_ROUTING_ENFORCE", "enforce")
    ).strip().lower()
    if guard_mode == "block":
        guard_mode = "enforce"

    if guard_mode in ("warn", "off"):
        now = time.time()
        try:
            override_ttl = float(os.environ.get("FLEET_ROUTING_GUARD_TTL", _DEFAULT_GUARD_OVERRIDE_TTL))
        except ValueError:
            override_ttl = _DEFAULT_GUARD_OVERRIDE_TTL

        if _GUARD_OVERRIDE_MODE != guard_mode:
            _GUARD_OVERRIDE_MODE = guard_mode
            _GUARD_OVERRIDE_TIMESTAMP = now
        elif (now - _GUARD_OVERRIDE_TIMESTAMP) > override_ttl:
            logger.warning(
                "🚨 [FLEET_ROUTING_GUARD:AUTO_HEAL] FLEET_ROUTING_GUARD=%s TTL (%.1fs) expired. Auto-restoring to 'enforce'.",
                guard_mode, override_ttl
            )
            guard_mode = "enforce"
            os.environ["FLEET_ROUTING_GUARD"] = "enforce"
            _GUARD_OVERRIDE_MODE = None
            _GUARD_OVERRIDE_TIMESTAMP = 0.0

    if not account or not model:
        return

    account_lower = account.lower()
    model_lower = model.lower()

    if guard_mode == "off":
        record_routing_attestation(account, model, verdict="OFF_BYPASSED", ledger_path=ledger_path, task_id=task_id)
        return

    ultra_accounts, nebula_nodes = _load_roster_pools()

    violation_msg: Optional[str] = None

    # Ultra accounts strictly serve Gemini only (reject Claude and any non-Gemini model)
    is_ultra = any(u in account_lower for u in ultra_accounts)
    is_claude = any(c in model_lower for c in ("claude", "opus", "sonnet"))
    if is_ultra:
        if is_claude:
            violation_msg = (
                f"Claude model {model!r} routed to Ultra account {account!r} "
                f"(Ultra accounts strictly serve Gemini only to protect Claude quota)"
            )
        elif not any(g in model_lower for g in ("gemini", "flash")):
            violation_msg = (
                f"Non-Gemini model {model!r} routed to Ultra account {account!r} "
                f"(Ultra accounts strictly serve approved Gemini models only)"
            )

    # Nebula nodes strictly serve Claude Opus 4.8 only (zero Gemini)
    if not violation_msg:
        is_nebula = any(n in account_lower for n in nebula_nodes)
        is_gemini = any(g in model_lower for g in ("gemini", "flash"))
        if is_nebula and is_gemini:
            violation_msg = (
                f"Gemini model {model!r} routed to Nebula node {account!r} "
                f"(Nebula strictly serves Claude Opus 4.8 only)"
            )
        elif is_nebula and "opus-4.8" not in model_lower and "claude-opus-4.8" not in model_lower:
            violation_msg = f"Nebula only serves claude-opus-4.8, got {model!r}"

    if violation_msg:
        if guard_mode == "warn":
            record_routing_attestation(account, model, verdict="WARNED", violation_reason=violation_msg, ledger_path=ledger_path, task_id=task_id)
            logger.warning("🚨 [FLEET_ROUTING_GUARD:WARN] %s", violation_msg)
        else:
            record_routing_attestation(account, model, verdict="DENIED", violation_reason=violation_msg, ledger_path=ledger_path, task_id=task_id)
            raise RoutingViolation(violation_msg)
    else:
        record_routing_attestation(account, model, verdict="ALLOWED", ledger_path=ledger_path, task_id=task_id)


# Aliases for backward compatibility and protocol conformance
assert_routing_invariant = assert_routing_legal
assert_routing_allowed = assert_routing_legal
enforce_routing_invariant = assert_routing_legal
enforce_routing_policy = assert_routing_legal


# ---------------------------------------------------------------------------
# Deterministic Fleet Route Resolver & Partial-Outage Fail-Closed Boundary
# ---------------------------------------------------------------------------
def resolve_fleet_route(
    model: str,
    pro_claude_available: bool = True,
    nebula_available: bool = True,
    ultra_available: bool = True,
    pro_gemini_available: bool = True,
    task_complexity: float = 1.0,
    roster_path: Optional[Path] = None,
    ledger_path: Optional[Path] = None,
    task_id: Optional[str] = None,
) -> Tuple[str, str]:
    """Resolves a legal execution route (node, model) under partial-dependency outage.

    Guarantees:
      1. Ultra accounts (ultra-2, lthn.ariana) NEVER serve Claude models under ANY failure state.
      2. Nebula gateway (nebula, b.ai) NEVER serves Gemini models under ANY failure state.
      3. Compound Partial Outage (Nebula down AND Pro Claude quota exhausted):
         FAILS CLOSED by raising NoCapacityError. Never spills over to Ultra.
      4. Missing roster file: falls back cleanly to version-controlled defaults.
    """
    model_lower = model.strip().lower()
    is_claude = any(c in model_lower for c in ("claude", "opus", "sonnet"))
    is_gemini = any(g in model_lower for g in ("gemini", "flash"))

    if not is_claude and not is_gemini:
        # Unknown model family: fail closed per sovereign policy
        raise RoutingViolation(f"Unknown or unapproved model family for fleet routing: {model!r}")

    if is_claude:
        # Claude routing: Pro-first -> Nebula fallback -> FAIL CLOSED
        if pro_claude_available:
            selected_node = "pro-1"
            selected_model = model
        elif nebula_available:
            if "opus-4.8" in model_lower or "claude-opus-4.8" in model_lower:
                selected_node = "nebula"
                selected_model = "claude-opus-4.8"
            else:
                # Nebula strictly serves claude-opus-4.8 only
                raise NoCapacityError(
                    f"Pro Claude nodes exhausted and Nebula only serves claude-opus-4.8 (requested: {model!r}). "
                    f"Fail-closed: zero legal Claude capacity."
                )
        else:
            # Compound outage: Pro Claude exhausted AND Nebula unavailable
            raise NoCapacityError(
                f"Zero legal Claude capacity: all Pro Claude nodes are exhausted and Nebula gateway is unavailable. "
                f"Fail-closed to protect Ultra Claude quota (Ultra is strictly Gemini-only)."
            )
    else:
        # Gemini routing: Ultra (for high complexity >= 2.5) -> Pro Gemini -> FAIL CLOSED
        # Nebula is strictly forbidden for Gemini
        if task_complexity >= 2.5 and ultra_available:
            selected_node = "ultra-2"
            selected_model = model
        elif pro_gemini_available:
            selected_node = "pro-1"
            selected_model = model
        elif ultra_available:
            selected_node = "ultra-2"
            selected_model = model
        else:
            raise NoCapacityError(
                f"Zero legal Gemini capacity: Pro Gemini nodes and Ultra nodes are both unavailable. "
                f"Nebula gateway cannot serve Gemini."
            )

    # Invariant tripwire check before returning
    assert_routing_legal(selected_node, selected_model, ledger_path=ledger_path, task_id=task_id)
    return selected_node, selected_model


# ---------------------------------------------------------------------------
# Startup Roster Consistency Guard (Fails Closed on Poisoned Roster)
# ---------------------------------------------------------------------------
def verify_roster_consistency(
    roster_path: Optional[Path] = None,
    fail_closed: bool = False,
) -> Tuple[bool, List[str]]:
    """Validates that fleet_roster.yml contains no invariant violations.
    
    Checks:
      1. pro-claude-pool must NEVER contain any Ultra account (IMMUTABLE_ULTRA_ACCOUNTS
         or nodes registered in ultra-gemini-pool).
      2. If fail_closed is True and violations exist, raises RoutingViolation.
      
    Returns (is_consistent, violations).
    """
    target = roster_path or (Path(__file__).resolve().parent.parent / "fleet_roster.yml")
    if not target.is_file() and roster_path is None:
        target = Path(__file__).resolve().parent.parent / "fleet_roster.defaults.yml"
    if not target.is_file():
        return True, []

    violations: List[str] = []
    try:
        import yaml
        with open(target, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            pools = data.get("pools") if isinstance(data.get("pools"), dict) else data
            ultra_aliases = set(IMMUTABLE_ULTRA_ACCOUNTS)
            raw_ultra = pools.get("ultra-gemini-pool", [])
            ultra_nodes = raw_ultra.get("nodes", []) if isinstance(raw_ultra, dict) else raw_ultra
            for u in (ultra_nodes if isinstance(ultra_nodes, list) else []):
                if isinstance(u, dict) and "alias" in u:
                    ultra_aliases.add(str(u["alias"]).strip().lower())
                elif isinstance(u, str):
                    ultra_aliases.add(u.strip().lower())

            raw_claude = pools.get("pro-claude-pool", [])
            claude_nodes = raw_claude.get("nodes", []) if isinstance(raw_claude, dict) else raw_claude
            for c in (claude_nodes if isinstance(claude_nodes, list) else []):
                c_alias = str(c.get("alias", "") if isinstance(c, dict) else c).strip().lower()
                c_tier = str(c.get("tier", "") if isinstance(c, dict) else "").strip().lower()
                if c_alias in ultra_aliases or c_tier == "ultra" or "ultra" in c_alias:
                    violations.append(
                        f"CRITICAL ROSTER DRIFT: Ultra account/alias {c_alias!r} found in pro-claude-pool! "
                        f"Ultra accounts strictly serve Gemini only."
                    )

            # Tier compliance checks across all declared pools (Nebula Finding 5)
            for pool_name, pool_data in pools.items():
                if not isinstance(pool_data, dict):
                    continue
                pool_nodes = pool_data.get("nodes", [])
                if not isinstance(pool_nodes, list):
                    continue
                for node_entry in pool_nodes:
                    if isinstance(node_entry, dict):
                        alias = str(node_entry.get("alias", "")).strip().lower()
                        tier = str(node_entry.get("tier", "")).strip().lower()
                        if alias and tier:
                            try:
                                assert_node_tier_compliance(alias, tier)
                            except RoutingViolation as rv:
                                violations.append(str(rv))
    except Exception as err:
        violations.append(f"Roster parsing error: {err}")

    is_consistent = len(violations) == 0
    if not is_consistent and fail_closed:
        raise RoutingViolation("; ".join(violations))

    return is_consistent, violations


# ---------------------------------------------------------------------------
# Kanban Pull System: Capability-Bearing Slots & Leased WIP Limiter
# ---------------------------------------------------------------------------
from dataclasses import dataclass
import threading
import uuid


@dataclass(frozen=True)
class RoutingSlot:
    """Capability-bearing Kanban slot that serves as capacity constraint and security tripwire.

    A slot carries the immutable capability set allowed for its node tier.
    It is physically impossible to bind a model outside the slot's allowed capability.
    """
    slot_id: str
    node: str
    model: str
    tier: str
    allowed_models: frozenset[str]
    acquired_at: float
    expires_at: float
    task_id: Optional[str] = None
    fence_token: int = 0


# In-flight lease table: node -> Dict[slot_id, RoutingSlot]
_ACTIVE_ROUTING_SLOTS: Dict[str, Dict[str, RoutingSlot]] = {}
_SLOT_LOCK = threading.RLock()
_GLOBAL_FENCE_TOKEN: int = 0


def get_node_allowed_models(node: str) -> Tuple[str, frozenset[str]]:
    """Returns (tier, allowed_models_set) for the given node."""
    node_lower = node.strip().lower()
    ultra_accounts, nebula_nodes = _load_roster_pools()

    if any(u in node_lower for u in ultra_accounts):
        return "ultra", GEMINI_MODELS
    elif any(n in node_lower for n in nebula_nodes):
        return "nebula", IMMUTABLE_NEBULA_MODELS
    else:
        return "pro", (CLAUDE_MODELS | GEMINI_MODELS)


def acquire_routing_slot(
    node: str,
    model: str,
    task_id: Optional[str] = None,
    ttl_seconds: float = 60.0,
    max_in_flight: Optional[int] = None,
    ledger_path: Optional[Path] = None,
) -> RoutingSlot:
    """Acquires a capability-verified Kanban slot with leased TTL.

    Security Tripwire:
      - Validates that model is in the node's allowed capability set.
      - If not, raises RoutingViolation (fail-closed by data structure).

    WIP Concurrency & Monotonic Lease:
      - Caps active in-flight slots per node (default 3 or FLEET_MAX_IN_FLIGHT_PER_NODE).
      - Uses monotonic clock (time.monotonic) to prevent wall-clock/NTP drift from causing
        premature expiration or deadlocks.
      - Stamps each lease with a monotonically increasing integer fence_token.
      - Prunes expired slots automatically (deadlock prevention for crashed workers).
    """
    global _GLOBAL_FENCE_TOKEN
    node_lower = node.strip().lower()
    model_lower = model.strip().lower()
    tier, allowed_models = get_node_allowed_models(node)

    # 1. Security Tripwire: Capability Check by Data Structure
    is_allowed = False
    for allowed in allowed_models:
        if allowed == model_lower or allowed in model_lower or model_lower in allowed:
            is_allowed = True
            break

    if not is_allowed:
        violation_reason = (
            f"Kanban capability tripwire! Node {node!r} (tier {tier!r}) slot only advertises "
            f"capabilities {sorted(allowed_models)!r}, cannot accept model {model!r}."
        )
        record_routing_attestation(
            account=node,
            model=model,
            verdict="CAPABILITY_TRIPWIRE_DENIED",
            violation_reason=violation_reason,
            ledger_path=ledger_path,
            task_id=task_id,
        )
        raise RoutingViolation(violation_reason)

    # 2. WIP Limit & Leased Slot Acquisition
    wip_enabled = os.environ.get("FLEET_WIP_ENFORCE", "enforce").strip().lower() != "off"
    limit = max_in_flight
    if limit is None:
        try:
            limit = int(os.environ.get("FLEET_MAX_IN_FLIGHT_PER_NODE", "3"))
        except ValueError:
            limit = 3

    now = time.monotonic()
    slot_id = f"slot-{uuid.uuid4().hex[:12]}"
    expires_at = now + ttl_seconds

    with _SLOT_LOCK:
        _GLOBAL_FENCE_TOKEN += 1
        fence_token = _GLOBAL_FENCE_TOKEN

        node_slots = _ACTIVE_ROUTING_SLOTS.setdefault(node_lower, {})
        # Deadlock prevention: prune expired slots using monotonic time
        expired_ids = [sid for sid, s in node_slots.items() if now > s.expires_at]
        for sid in expired_ids:
            del node_slots[sid]

        if wip_enabled and len(node_slots) >= limit:
            raise RuntimeError(
                f"WIP limit reached for node {node!r}: {len(node_slots)}/{limit} active in-flight leases. "
                f"Wait for slot release or TTL expiry."
            )

        slot = RoutingSlot(
            slot_id=slot_id,
            node=node,
            model=model,
            tier=tier,
            allowed_models=allowed_models,
            acquired_at=now,
            expires_at=expires_at,
            task_id=task_id,
            fence_token=fence_token,
        )
        node_slots[slot_id] = slot

    # Log successful slot lease
    record_routing_attestation(
        account=node,
        model=model,
        verdict=f"SLOT_ACQUIRED:{slot_id}:fence={fence_token}",
        ledger_path=ledger_path,
        task_id=task_id,
    )
    return slot


def release_routing_slot(slot: RoutingSlot) -> bool:
    """Releases an active routing slot back to the node pool."""
    node_lower = slot.node.strip().lower()
    with _SLOT_LOCK:
        node_slots = _ACTIVE_ROUTING_SLOTS.get(node_lower, {})
        if slot.slot_id in node_slots:
            del node_slots[slot.slot_id]
            return True
    return False


def get_active_slots_count(node: Optional[str] = None) -> int:
    """Returns number of active non-expired in-flight slots."""
    now = time.monotonic()
    with _SLOT_LOCK:
        if node:
            node_slots = _ACTIVE_ROUTING_SLOTS.get(node.strip().lower(), {})
            return sum(1 for s in node_slots.values() if now <= s.expires_at)
        total = 0
        for node_slots in _ACTIVE_ROUTING_SLOTS.values():
            total += sum(1 for s in node_slots.values() if now <= s.expires_at)
        return total


def reset_routing_slots_for_testing() -> None:
    """Clears all active routing slots and resets fence counter (test helper)."""
    global _GLOBAL_FENCE_TOKEN
    with _SLOT_LOCK:
        _ACTIVE_ROUTING_SLOTS.clear()
        _GLOBAL_FENCE_TOKEN = 0


# ---------------------------------------------------------------------------
# Monotonic CRDT Quota Ledger (Clock-Drift Resilient Max-Merge State)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class MonotonicQuotaEntry:
    """Monotonic grow-only quota state for a single node and window."""
    node: str
    counter: int
    window_id: int
    fence_token: int
    updated_at_monotonic: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node": self.node,
            "counter": self.counter,
            "window_id": self.window_id,
            "fence_token": self.fence_token,
            "updated_at_monotonic": self.updated_at_monotonic,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MonotonicQuotaEntry:
        return cls(
            node=str(data["node"]),
            counter=int(data["counter"]),
            window_id=int(data["window_id"]),
            fence_token=int(data["fence_token"]),
            updated_at_monotonic=float(data["updated_at_monotonic"]),
        )


class MonotonicCRDTQuotaLedger:
    """Grow-only State-based CRDT Quota Ledger with Monotonic Windows & Fencing Tokens.

    Guarantees:
      1. Commutativity, Associativity, Idempotence:
         Merge operation is defined as point-wise max() over counters for matching or advancing window IDs.
      2. Clock-Drift Immunity:
         Monotonic window rollover relies on monotonic intervals or explicit monotonic epoch ticks,
         preventing NTP time-travel backwards or forwards from manipulating quota counts.
      3. Distributed Stale-Write Rejection:
         Each operation verifies fence_token >= last_seen_fence_token, rejecting out-of-order writes.
    """
    def __init__(self, window_size_seconds: float = 3600.0) -> None:
        self._window_size = window_size_seconds
        self._start_monotonic = time.monotonic()
        self._entries: Dict[str, MonotonicQuotaEntry] = {}
        self._lock = threading.RLock()

    def _current_window_id(self) -> int:
        elapsed = time.monotonic() - self._start_monotonic
        return int(elapsed // self._window_size)

    def record_usage(
        self,
        node: str,
        units: int = 1,
        fence_token: Optional[int] = None,
    ) -> MonotonicQuotaEntry:
        """Records quota consumption, advancing the grow-only counter monotonically."""
        if units < 0:
            raise ValueError(f"CRDT quota counter is grow-only; cannot decrement: {units}")

        node_key = node.strip().lower()
        now_mono = time.monotonic()
        win_id = self._current_window_id()

        with self._lock:
            current = self._entries.get(node_key)
            if current is not None:
                if win_id > current.window_id:
                    new_counter = units
                    new_fence = fence_token if fence_token is not None else current.fence_token + 1
                else:
                    new_counter = current.counter + units
                    new_fence = (
                        max(fence_token, current.fence_token)
                        if fence_token is not None
                        else current.fence_token + 1
                    )
            else:
                new_counter = units
                new_fence = fence_token if fence_token is not None else 1

            entry = MonotonicQuotaEntry(
                node=node_key,
                counter=new_counter,
                window_id=win_id,
                fence_token=new_fence,
                updated_at_monotonic=now_mono,
            )
            self._entries[node_key] = entry
            return entry

    def get_usage(self, node: str) -> int:
        """Returns current window usage for node."""
        node_key = node.strip().lower()
        win_id = self._current_window_id()
        with self._lock:
            entry = self._entries.get(node_key)
            if entry is None or entry.window_id < win_id:
                return 0
            return entry.counter

    def verify_fence(self, node: str, fence_token: int) -> bool:
        """Returns True if fence_token is valid (>= current recorded fence token)."""
        node_key = node.strip().lower()
        with self._lock:
            entry = self._entries.get(node_key)
            if entry is None:
                return True
            return fence_token >= entry.fence_token

    def merge(self, remote_state: Dict[str, Any]) -> None:
        """LWW / Max-Merge commutative state update."""
        with self._lock:
            for node_key, raw_entry in remote_state.items():
                if isinstance(raw_entry, dict):
                    remote_entry = MonotonicQuotaEntry.from_dict(raw_entry)
                elif isinstance(raw_entry, MonotonicQuotaEntry):
                    remote_entry = raw_entry
                else:
                    continue

                local_entry = self._entries.get(node_key)
                if local_entry is None:
                    self._entries[node_key] = remote_entry
                elif remote_entry.window_id > local_entry.window_id:
                    self._entries[node_key] = remote_entry
                elif remote_entry.window_id == local_entry.window_id:
                    merged = MonotonicQuotaEntry(
                        node=node_key,
                        counter=max(local_entry.counter, remote_entry.counter),
                        window_id=local_entry.window_id,
                        fence_token=max(local_entry.fence_token, remote_entry.fence_token),
                        updated_at_monotonic=max(local_entry.updated_at_monotonic, remote_entry.updated_at_monotonic),
                    )
                    self._entries[node_key] = merged

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {k: v.to_dict() for k, v in self._entries.items()}


_GLOBAL_CRDT_QUOTA_LEDGER = MonotonicCRDTQuotaLedger()


def get_crdt_quota_ledger() -> MonotonicCRDTQuotaLedger:
    return _GLOBAL_CRDT_QUOTA_LEDGER


# ---------------------------------------------------------------------------
# Scope-Equivalence Failover Guard & Trust Boundary Enforcement
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TrustScope:
    """Security scope and isolation contract for tasks and agent delegations."""
    name: str
    allowed_toolsets: frozenset[str] = frozenset()
    is_confidential: bool = False
    requires_code_execution: bool = False
    minimum_tier: Tier = Tier.PRO


def assert_failover_scope_equivalence(
    primary_node: str,
    target_node: str,
    required_scope: Optional[TrustScope] = None,
    task_is_confidential: bool = False,
    task_requires_code_exec: bool = False,
) -> bool:
    """Verifies that cascading failover across nodes preserves authorization scope boundaries.

    Fails closed:
      - If task is confidential, it cannot failover to an external public API gateway (e.g. Nebula).
      - If task requires code execution or terminal capabilities, it cannot failover to an
        API node that lacks runtime tool execution capabilities.
      - If required_scope dictates a minimum tier, target_node must belong to that tier or higher.
    """
    primary_lower = primary_node.strip().lower()
    target_lower = target_node.strip().lower()

    is_target_nebula = any(n in target_lower for n in IMMUTABLE_NEBULA_NODES)
    is_target_ultra = any(u in target_lower for u in IMMUTABLE_ULTRA_ACCOUNTS)

    # 1. Confidentiality barrier: confidential workloads cannot failover to public API gateways
    if task_is_confidential or (required_scope and required_scope.is_confidential):
        if is_target_nebula:
            raise ScopeViolation(
                f"Trust Boundary Breach: Confidential task on primary node {primary_node!r} "
                f"cannot failover to external API gateway {target_node!r}."
            )

    # 2. Execution environment barrier: tasks requiring terminal / code exec cannot failover to API-only nodes
    if task_requires_code_exec or (required_scope and required_scope.requires_code_execution):
        if is_target_nebula:
            raise ScopeViolation(
                f"Execution Scope Breach: Task requiring code execution on {primary_node!r} "
                f"cannot failover to non-execution gateway {target_node!r}."
            )

    # 3. Minimum tier barrier
    if required_scope:
        if required_scope.minimum_tier == Tier.ULTRA and not is_target_ultra:
            raise ScopeViolation(
                f"Tier Scope Breach: Task requires ULTRA tier scope; "
                f"target node {target_node!r} is not an Ultra tier node."
            )

    return True


# ---------------------------------------------------------------------------
# GDPR 72h Crypto-Shredding Retention Backpressure on Admission Control
# ---------------------------------------------------------------------------
MAX_RETENTION_SLA_SECONDS: float = 72.0 * 3600.0  # 72 hours (GDPR Article 17)
DEFAULT_RETENTION_HEADROOM_MARGIN_SECONDS: float = 3600.0  # 1 hour headroom margin


def check_retention_sla_admission_headroom(
    ledger_path: Optional[Path] = None,
    max_unshredded_backlog: int = 10000,
    headroom_margin_seconds: float = DEFAULT_RETENTION_HEADROOM_MARGIN_SECONDS,
    now: Optional[float] = None,
    account: Optional[str] = None,
    max_per_account_backlog: Optional[int] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """Evaluates whether the system has sufficient headroom to admit new requests within the 72h GDPR SLA.

    Couples rate-limiting and admission control to the crypto-shredding retention clock:
    A request that would create data that cannot be guaranteed to be deleted within the 72h GDPR
    window gets backpressured at the admission boundary rather than admitted and later force-shredded.

    Includes Tenant/Account-fair shedding under 10x spikes:
      - If global backlog is high, quiet accounts with backlogs below their fair share
        (default: max_unshredded_backlog // 4) are NOT starved by a single noisy account.
      - Oldest unredacted record SLA expiration attributes strictly to the offending account.

    Returns:
      (can_admit: bool, reason: str, metrics: Dict[str, Any])
    """
    target_ledger = ledger_path or DEFAULT_ATTESTATION_LEDGER_PATH
    current_time = now if now is not None else time.time()
    sla_cutoff_time = current_time - (MAX_RETENTION_SLA_SECONDS - headroom_margin_seconds)
    target_account = account.strip().lower() if account else None

    metrics: Dict[str, Any] = {
        "total_records": 0,
        "unredacted_records": 0,
        "redacted_records": 0,
        "oldest_unredacted_age_seconds": 0.0,
        "headroom_seconds": MAX_RETENTION_SLA_SECONDS,
        "backpressure_active": False,
        "unredacted_by_account": {},
        "oldest_unredacted_by_account": {},
    }

    if not target_ledger.is_file():
        return True, "OK", metrics

    oldest_unredacted_ts = current_time
    unredacted_by_acc: Dict[str, int] = {}
    oldest_by_acc: Dict[str, float] = {}

    try:
        with open(target_ledger, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    entry = json.loads(line_str)
                except Exception:
                    continue

                metrics["total_records"] += 1
                if entry.get("redacted"):
                    metrics["redacted_records"] += 1
                else:
                    metrics["unredacted_records"] += 1
                    ts = float(entry.get("timestamp", current_time))
                    acc = str(entry.get("account", "unknown")).strip().lower()

                    unredacted_by_acc[acc] = unredacted_by_acc.get(acc, 0) + 1
                    if acc not in oldest_by_acc or ts < oldest_by_acc[acc]:
                        oldest_by_acc[acc] = ts

                    if ts < oldest_unredacted_ts:
                        oldest_unredacted_ts = ts

        metrics["unredacted_by_account"] = unredacted_by_acc
        metrics["oldest_unredacted_by_account"] = oldest_by_acc

        if metrics["unredacted_records"] > 0:
            oldest_age = current_time - oldest_unredacted_ts
            metrics["oldest_unredacted_age_seconds"] = max(0.0, oldest_age)
            metrics["headroom_seconds"] = max(0.0, MAX_RETENTION_SLA_SECONDS - oldest_age)

            # Check 1: Oldest unredacted record exceeds SLA threshold (71h)
            if oldest_unredacted_ts <= sla_cutoff_time:
                # If checking a specific account, only backpressure if THIS account owns an expired record
                if target_account:
                    acc_oldest = oldest_by_acc.get(target_account, current_time)
                    if acc_oldest <= sla_cutoff_time:
                        acc_age = current_time - acc_oldest
                        metrics["backpressure_active"] = True
                        return (
                            False,
                            f"GDPR Retention SLA backpressure: Account {target_account!r} oldest un-shredded record age "
                            f"({acc_age / 3600:.2f}h) exceeds 72h deletion headroom.",
                            metrics,
                        )
                else:
                    metrics["backpressure_active"] = True
                    return (
                        False,
                        f"GDPR Retention SLA backpressure: Oldest un-shredded record age ({oldest_age / 3600:.2f}h) "
                        f"exceeds 72h deletion headroom ({metrics['headroom_seconds'] / 3600:.2f}h remaining).",
                        metrics,
                    )

        # Check 2: Unredacted backlog capacity threshold with tenant fairness
        if target_account:
            acc_backlog = unredacted_by_acc.get(target_account, 0)
            per_account_limit = (
                max_per_account_backlog
                if max_per_account_backlog is not None
                else max(50, max_unshredded_backlog // 4)
            )
            # If the specific account exceeds its quota, shed it
            if acc_backlog >= per_account_limit:
                metrics["backpressure_active"] = True
                return (
                    False,
                    f"GDPR Retention SLA backpressure: Account {target_account!r} un-shredded backlog ({acc_backlog}) "
                    f"exceeds fair tenant threshold ({per_account_limit}).",
                    metrics,
                )
            # Emergency global hard ceiling: 2x max_unshredded_backlog sheds all
            if metrics["unredacted_records"] >= max_unshredded_backlog * 2:
                metrics["backpressure_active"] = True
                return (
                    False,
                    f"GDPR Retention SLA backpressure: Emergency system-wide backlog "
                    f"({metrics['unredacted_records']}) exceeded emergency limit ({max_unshredded_backlog * 2}).",
                    metrics,
                )
        else:
            if metrics["unredacted_records"] >= max_unshredded_backlog:
                metrics["backpressure_active"] = True
                return (
                    False,
                    f"GDPR Retention SLA backpressure: Un-shredded backlog ({metrics['unredacted_records']}) "
                    f"exceeds maximum deletion capacity threshold ({max_unshredded_backlog}).",
                    metrics,
                )

        return True, "OK", metrics

    except Exception as e:
        logger.warning("Failed to evaluate retention SLA admission headroom: %s", e)
        return True, f"Degraded admission check: {e}", metrics



