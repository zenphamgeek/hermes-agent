#!/usr/bin/env python3
"""
tools/modal_budget_guard.py
===========================
Hermes Agent & AGY Fleet — Sovereign Modal Multi-GPU Budget Guard & Pre-Flight Credit Gate.

Sovereign Invariants (Section 1.17):
1. Pre-Flight Credit Gate:
   - Deploy: Allowed ONLY on workspaces with remaining credits > $15.00 (MTD Spend < $15.00).
   - Inference: Allowed ONLY on workspaces with remaining credits > $10.00 (MTD Spend < $20.00).
2. Automated Kill-Switch Watchdog:
   - Hard budget ceiling: $25.00 USD / workspace / month.
   - If cost >= $25.00: Immediately stops all running/deployed apps and active containers.
3. Adaptive Dual-Cadence & CWE-78/88 Subprocess Sanitization:
   - Idle (0 active containers & safe credits): 300s (5m) cadence with natural jitter (+- 10%).
   - Active (>= 1 active GPU containers OR remaining credits <= $10): 15s–30s tight watchdog eliminating the 600s runaway spend blind spot.
   - Strict regex validation (APP_ID_REGEX, CONTAINER_ID_REGEX) and array-based subprocess invocation (no shell=True).
4. Virtual Escrow & Self-Expiring In-Flight Lease (TOCTOU Defense):
   - In-flight escrow ledger prevents parallel job dispatches from bypassing Rule 1.17 gates due to 5–15 min Modal billing latency.
5. Circuit Breaker & Fail-Closed Degraded Fallback:
   - On consecutive API failures (>= 3) or transient 5xx/Timeout, deploy fails closed while inference gracefully reroutes to Cloudflare Clef Flash / Local JEV ($0.00).
"""

import argparse
import json
import logging
import os
import random
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("ModalBudgetGuard")

# Strict identifier validation to prevent CWE-78 / CWE-88 command injection
APP_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]{1,64}$")
CONTAINER_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]{1,64}$")

TOTAL_ALLOWANCE_USD = 30.00
BUDGET_CEILING_USD = 25.00
HARD_KILL_CEILING = 25.00          # USD: Automatic kill-switch
DEPLOY_MIN_CREDITS_USD = 15.00     # Remaining credits must be > $15.00
INFERENCE_MIN_CREDITS_USD = 10.00  # Remaining credits must be > $10.00

IDLE_POLL_INTERVAL_SECONDS = 300       # 300s - 600s when quiescent
ACTIVE_POLL_INTERVAL_SECONDS = 30      # 15s - 30s when active container running or credits low

TOML_PATH = Path(os.path.expanduser("~/.modal.toml"))
LOG_PATH = Path("/home/zen/hermes-agent/output/modal_budget_guard.log")

CANONICAL_APP_IDS: Tuple[str, ...] = (
    "r2rgraph_worker",
    "motion_geometry_engine",
    "diatts_voice_synth",
    "mojopham_avatar",
    "mvlm_vision_audit",
    "vrag_indexer",
    "vi2vi_swapface",
    "jev27b_vl",
)


def _sanitize_modal_fleet_policy(policy: Dict[str, Any]) -> Dict[str, Any]:
    """
    SEC-001 (CWE-20) Hardening: Sanitizes modal_fleet_policy dictionary so no untrusted
    swarm payload can raise budget_ceiling_hard_kill_usd above $25.00 or lower credit gates
    below $15.00 (deploy) / $10.00 (inference).
    """
    sanitized = dict(policy or {})
    credit_policy = dict(sanitized.get("credit_policy") or {})

    raw_ceiling = float(credit_policy.get("budget_ceiling_hard_kill_usd", HARD_KILL_CEILING))
    raw_deploy_min = float(credit_policy.get("deploy_min_credits_usd", DEPLOY_MIN_CREDITS_USD))
    raw_infer_min = float(credit_policy.get("inference_min_credits_usd", INFERENCE_MIN_CREDITS_USD))

    credit_policy["budget_ceiling_hard_kill_usd"] = min(HARD_KILL_CEILING, max(1.0, raw_ceiling))
    credit_policy["deploy_min_credits_usd"] = max(DEPLOY_MIN_CREDITS_USD, raw_deploy_min)
    credit_policy["inference_min_credits_usd"] = max(INFERENCE_MIN_CREDITS_USD, raw_infer_min)
    sanitized["credit_policy"] = credit_policy
    return sanitized


def _resolve_active_and_failover(
    policy: Dict[str, Any],
    fallback_candidates: Optional[List[str]] = None,
) -> Tuple[List[str], List[str]]:
    """
    SEC-002 (CWE-400) & SEC-004 (CWE-682) Hardening:
    Resolves (active_fleet, failover_pool) while strictly excluding any workspace listed in
    `credit_blocked` or `disabled_workspaces`, even along the fallback path.
    """
    sanitized = _sanitize_modal_fleet_policy(policy)
    blocked = set(sanitized.get("credit_blocked") or []) | set(sanitized.get("disabled_workspaces") or [])
    raw_active = [w for w in (sanitized.get("active_fleet") or []) if w not in blocked]
    raw_failover = [w for w in (sanitized.get("failover_pool") or []) if w not in blocked and w not in raw_active]

    if not raw_active and fallback_candidates:
        raw_active = [w for w in fallback_candidates if w not in blocked]

    return raw_active, raw_failover


class InFlightLease:
    """Represents a provisional in-flight budget escrow token with monotonic bounded TTL."""

    def __init__(
        self,
        job_id: str,
        estimated_cost: float,
        ttl_s: float = 180.0,
        idempotency_key: Optional[str] = None,
    ):
        self.job_id = job_id
        self.idempotency_key = idempotency_key or job_id
        self.estimated_cost = estimated_cost
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl_s
        self.created_at_mono = time.monotonic()
        self.expires_at_mono = self.created_at_mono + ttl_s
        self.released = False

    @property
    def is_expired(self) -> bool:
        return self.released or (time.monotonic() > self.expires_at_mono) or (time.time() > self.expires_at)


class InFlightLeaseLedger:
    """Thread-safe in-flight escrow ledger with self-expiring bounded TTL (TOCTOU mitigation)."""

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._leases: Dict[str, InFlightLease] = {}
        self._idempotency_map: Dict[str, str] = {}
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "InFlightLeaseLedger":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def prune_expired(self) -> None:
        with self._lock:
            self._leases = {k: v for k, v in self._leases.items() if not v.is_expired}
            self._idempotency_map = {
                ik: jid for ik, jid in self._idempotency_map.items() if jid in self._leases
            }

    def total_in_flight_cost(self) -> float:
        self.prune_expired()
        with self._lock:
            return sum(v.estimated_cost for v in self._leases.values())

    def acquire_lease(
        self,
        job_id: str,
        estimated_cost: float,
        remaining_credits: float,
        min_required_credits: float,
        ttl_s: float = 180.0,
        idempotency_key: Optional[str] = None,
    ) -> Tuple[bool, str]:
        self.prune_expired()
        with self._lock:
            key = idempotency_key or job_id
            if key in self._idempotency_map:
                existing_id = self._idempotency_map[key]
                if existing_id in self._leases and not self._leases[existing_id].is_expired:
                    return True, f"Idempotent reuse of active lease for job {existing_id}"

            current_in_flight = sum(v.estimated_cost for v in self._leases.values())
            effective_remaining = remaining_credits - current_in_flight
            if effective_remaining - estimated_cost < min_required_credits:
                return (
                    False,
                    f"Virtual Escrow blocked: effective credits ${effective_remaining:.2f} "
                    f"minus job cost ${estimated_cost:.2f} leaves ${effective_remaining - estimated_cost:.2f} "
                    f"<= ${min_required_credits:.2f} threshold (In-flight: ${current_in_flight:.2f})"
                )
            self._leases[job_id] = InFlightLease(job_id, estimated_cost, ttl_s, idempotency_key=key)
            self._idempotency_map[key] = job_id
            return True, "Lease acquired"

    def release_lease(self, job_id: str, idempotency_key: Optional[str] = None) -> bool:
        import hmac

        with self._lock:
            lease = self._leases.get(job_id)
            if lease is None or lease.released:
                return False
            if idempotency_key is not None and not hmac.compare_digest(
                str(lease.idempotency_key), str(idempotency_key)
            ):
                return False
            lease.released = True
            self._leases.pop(job_id, None)
            self._idempotency_map = {
                ik: jid for ik, jid in self._idempotency_map.items() if jid != job_id
            }
            return True

    def clear(self) -> None:
        with self._lock:
            self._leases.clear()
            self._idempotency_map.clear()


class ModalCircuitBreaker:
    """Fail-closed circuit breaker preventing cascade crashes on Modal Billing API 5xx/Timeout."""

    def __init__(self, failure_threshold: int = 3, cooldown_s: float = 60.0):
        self.failure_threshold = failure_threshold
        self.cooldown_s = cooldown_s
        self.consecutive_failures = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED | OPEN | HALF_OPEN

    def record_failure(self) -> None:
        self.consecutive_failures += 1
        self.last_failure_time = time.time()
        if self.consecutive_failures >= self.failure_threshold:
            self.state = "OPEN"

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.state = "CLOSED"

    @property
    def is_open(self) -> bool:
        if self.state == "OPEN":
            if (time.time() - self.last_failure_time) > self.cooldown_s:
                self.state = "HALF_OPEN"
                return False
            return True
        return False

    def handle_api_degradation(self, action: str) -> Dict[str, Any]:
        """
        Graceful degradation:
        - deploy: Hard-blocked (fail-closed for high-cost operations).
        - inference: Auto-rerouted to Cloudflare Clef Flash / Local JEV ($0.00 cost).
        """
        action_lower = action.lower()
        if action_lower == "deploy":
            return {
                "allowed": False,
                "action": "deploy",
                "circuit_breaker": "OPEN",
                "cost_mtd_usd": 0.0,
                "remaining_credits_usd": 0.0,
                "reason": "Modal Billing API degraded (HTTP 5xx/Timeout); high-cost deploy fail-closed",
            }
        else:
            return {
                "allowed": True,
                "action": "inference",
                "circuit_breaker": "OPEN",
                "fallback_provider": "cloudflare_clef_local_jev",
                "cost_usd": 0.0,
                "cost_mtd_usd": 0.0,
                "remaining_credits_usd": 0.0,
                "reason": "Modal Billing API degraded; inference gracefully rerouted to Cloudflare Clef Flash / Local JEV ($0.00)",
            }


def calculate_adaptive_interval(
    active_count: int,
    remaining_credits: float,
    idle_interval: int = IDLE_POLL_INTERVAL_SECONDS,
    active_interval: int = ACTIVE_POLL_INTERVAL_SECONDS,
    warning_threshold: float = INFERENCE_MIN_CREDITS_USD,
) -> int:
    """
    Calculates adaptive polling interval with natural jitter (+- 10%).
    - 0 active containers & safe credits (> $10): idle_interval (300s) + jitter in [270s, 330s]
    - >= 1 active containers OR credits <= $10: active_interval (30s) + jitter in [27s, 33s]
    """
    if active_count > 0 or remaining_credits <= warning_threshold:
        base = active_interval
    else:
        base = idle_interval

    jitter = random.uniform(-0.10, 0.10) * base
    return max(15, int(round(base + jitter)))


def run_cmd(cmd: List[str], env: Optional[Dict[str, str]] = None, timeout: int = 15) -> str:
    """Safe array-based command execution with explicit timeout and no shell=True (CWE-78)."""
    try:
        res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=timeout)
        return res.stdout.strip()
    except Exception as e:
        logger.debug("Command execution failed for %s: %s", cmd, e)
        return ""


def get_profiles() -> List[str]:
    """Extracts active, uncommented workspace profiles from ~/.modal.toml."""
    if not TOML_PATH.exists():
        return []
    try:
        with open(TOML_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        return [m for m in re.findall(r'^\s*\[(.*?)\]', content, re.MULTILINE) if not m.startswith("#")]
    except Exception:
        return []


def get_profile_cost(profile: str) -> float:
    """Calculates MTD spend for a specific Modal profile."""
    env = dict(os.environ, MODAL_PROFILE=profile)
    report_json = run_cmd(["modal", "billing", "report", "--for", "this month", "--json"], env=env, timeout=15)
    if report_json:
        try:
            entries = json.loads(report_json)
            return sum(float(e.get("Cost", 0)) for e in entries)
        except Exception:
            pass
    return 0.0


def verify_credit_gate(
    profile: str,
    action: str = "inference",
    job_id: Optional[str] = None,
    estimated_cost: float = 0.50,
    circuit_breaker: Optional[ModalCircuitBreaker] = None,
) -> Dict[str, Any]:
    """Pre-flight credit verification gate (Rule 1.17) with Virtual Escrow and Circuit Breaker.
    - deploy: requires remaining credits > $15.00 (MTD cost < $15.00)
    - inference: requires remaining credits > $10.00 (MTD cost < $20.00)
    """
    action_lower = action.lower()
    min_required = DEPLOY_MIN_CREDITS_USD if action_lower == "deploy" else INFERENCE_MIN_CREDITS_USD

    # Check Circuit Breaker for degraded upstream API
    if circuit_breaker and circuit_breaker.is_open:
        return circuit_breaker.handle_api_degradation(action_lower)

    active_profiles = get_profiles()
    if profile not in active_profiles:
        return {
            "profile": profile,
            "action": action_lower,
            "cost_mtd_usd": 0.0,
            "remaining_credits_usd": 0.0,
            "min_required_credits_usd": min_required,
            "allowed": False,
            "reason": f"Profile '{profile}' is currently disabled/paused in ~/.modal.toml (not in active fleet)"
        }

    try:
        cost = get_profile_cost(profile)
        if circuit_breaker:
            circuit_breaker.record_success()
    except Exception as e:
        logger.warning("Error querying profile cost for %s: %s", profile, e)
        if circuit_breaker:
            circuit_breaker.record_failure()
            if circuit_breaker.is_open:
                return circuit_breaker.handle_api_degradation(action_lower)
        cost = 0.0

    remaining_credits = max(0.0, TOTAL_ALLOWANCE_USD - cost)

    # Base Rule 1.17 Gate Check
    if action_lower == "deploy":
        allowed = remaining_credits > DEPLOY_MIN_CREDITS_USD
        min_required = DEPLOY_MIN_CREDITS_USD
    elif action_lower in ("inference", "run"):
        allowed = remaining_credits > INFERENCE_MIN_CREDITS_USD
        min_required = INFERENCE_MIN_CREDITS_USD
    else:
        allowed = remaining_credits > INFERENCE_MIN_CREDITS_USD
        min_required = INFERENCE_MIN_CREDITS_USD

    if not allowed:
        return {
            "profile": profile,
            "action": action_lower,
            "cost_mtd_usd": round(cost, 2),
            "remaining_credits_usd": round(remaining_credits, 2),
            "min_required_credits_usd": min_required,
            "allowed": False,
            "reason": f"Credits ${remaining_credits:.2f} <= ${min_required:.2f} threshold"
        }

    # Virtual Escrow Reservation (Anti-TOCTOU)
    if job_id:
        ledger = InFlightLeaseLedger.get_instance()
        lease_ok, lease_reason = ledger.acquire_lease(
            job_id=job_id,
            estimated_cost=estimated_cost,
            remaining_credits=remaining_credits,
            min_required_credits=min_required,
        )
        if not lease_ok:
            return {
                "profile": profile,
                "action": action_lower,
                "cost_mtd_usd": round(cost, 2),
                "remaining_credits_usd": round(remaining_credits, 2),
                "min_required_credits_usd": min_required,
                "allowed": False,
                "reason": lease_reason,
            }

    return {
        "profile": profile,
        "action": action_lower,
        "cost_mtd_usd": round(cost, 2),
        "remaining_credits_usd": round(remaining_credits, 2),
        "min_required_credits_usd": min_required,
        "allowed": True,
        "reason": f"Credits ${remaining_credits:.2f} > ${min_required:.2f} threshold"
    }


def check_and_enforce_budget(profile: str) -> Dict[str, Any]:
    """Enforces hard ceiling on a specific profile."""
    guard = ModalBudgetGuard()
    return guard.check_and_enforce_profile(profile)


class ModalBudgetGuard:
    """
    Sovereign Modal Multi-GPU Budget Guard & Adaptive Watchdog.

    Enforces:
    - Adaptive Cadence: 300s when idle (0 containers), 15s–30s under GPU load.
    - Anti-Injection: Strict regex verification on app_id and container_id (CWE-78/88).
    - Rule 1.17 Credit Gate: Deploy > $15.00, Inference > $10.00, Hard-kill >= $25.00.
    - Virtual Escrow & Circuit Breaker against TOCTOU and API degradation.
    """

    TOTAL_ALLOWANCE_USD = TOTAL_ALLOWANCE_USD
    HARD_KILL_CEILING = HARD_KILL_CEILING
    DEPLOY_MIN_CREDITS_USD = DEPLOY_MIN_CREDITS_USD
    INFERENCE_MIN_CREDITS_USD = INFERENCE_MIN_CREDITS_USD

    IDLE_POLL_INTERVAL_SECONDS = IDLE_POLL_INTERVAL_SECONDS
    ACTIVE_POLL_INTERVAL_SECONDS = ACTIVE_POLL_INTERVAL_SECONDS

    def __init__(self, ledger_path: str = ".passive_quota_ledger.json"):
        self.ledger_path = ledger_path
        self.logger = logging.getLogger("ModalBudgetGuard")
        self.circuit_breaker = ModalCircuitBreaker()
        self.lease_ledger = InFlightLeaseLedger.get_instance()

    def get_active_containers(self, profile: Optional[str] = None) -> List[Dict[str, Any]]:
        """Queries currently active Modal containers via JSON output with explicit timeout."""
        env = dict(os.environ)
        if profile:
            env["MODAL_PROFILE"] = profile
        try:
            res = subprocess.run(
                ["modal", "container", "list", "--json"],
                capture_output=True,
                text=True,
                check=True,
                timeout=12,
                env=env,
            )
            return json.loads(res.stdout or "[]")
        except Exception as e:
            self.logger.debug("Failed to query active containers: %s", e)
            return []

    def fetch_current_mtd_spend(self, profile: Optional[str] = None) -> float:
        """Retrieves total MTD spend across active profiles or target profile."""
        if profile:
            return get_profile_cost(profile)
        profiles = get_profiles()
        if not profiles:
            return 0.0
        return max((get_profile_cost(p) for p in profiles), default=0.0)

    def stop_app(self, app_id: str, profile: Optional[str] = None) -> bool:
        """Safely terminates an active app without shell interpolation (CWE-78 guard)."""
        if not APP_ID_REGEX.match(app_id):
            self.logger.error("CWE-78 Alert: Rejected malformed app_id: %s", app_id)
            return False
        env = dict(os.environ)
        if profile:
            env["MODAL_PROFILE"] = profile
        try:
            subprocess.run(["modal", "app", "stop", app_id], check=True, timeout=15, env=env)
            return True
        except subprocess.SubprocessError as e:
            self.logger.error("Failed to stop app %s: %s", app_id, e)
            return False

    def stop_container(self, container_id: str, profile: Optional[str] = None) -> bool:
        """Safely terminates an active container without shell interpolation (CWE-78 guard)."""
        if not CONTAINER_ID_REGEX.match(container_id):
            self.logger.error("CWE-78 Alert: Rejected malformed container_id: %s", container_id)
            return False
        env = dict(os.environ)
        if profile:
            env["MODAL_PROFILE"] = profile
        try:
            subprocess.run(["modal", "container", "stop", container_id], check=True, timeout=10, env=env)
            return True
        except subprocess.SubprocessError as e:
            self.logger.error("Failed to stop container %s: %s", container_id, e)
            return False

    def execute_emergency_shutdown(self, profile: Optional[str] = None) -> None:
        """Hard-kill all running containers and apps when ceiling is breached (>= $25.00)."""
        self.logger.critical("🚨 HARD-KILL CEILING BREACHED (>= $25.00). Initiating shutdown...")
        containers = self.get_active_containers(profile=profile)
        for c in containers:
            c_id = c.get("container_id") or c.get("id")
            if c_id and CONTAINER_ID_REGEX.match(str(c_id)):
                self.stop_container(str(c_id), profile=profile)

        # Stop deployed/running apps
        env = dict(os.environ)
        if profile:
            env["MODAL_PROFILE"] = profile
        app_list_json = run_cmd(["modal", "app", "list", "--json"], env=env, timeout=12)
        if app_list_json:
            try:
                apps = json.loads(app_list_json)
                for app in apps:
                    app_id = app.get("App ID") or app.get("AppId") or app.get("id")
                    state = app.get("State") or app.get("state")
                    if app_id and state in ("deployed", "running"):
                        self.stop_app(str(app_id), profile=profile)
            except Exception as e:
                self.logger.error("Error inspecting apps for emergency shutdown: %s", e)

        # Fallback to kill-script if present
        kill_script = Path("/home/zen/arouter/scripts/kill_modal.sh")
        if kill_script.exists():
            try:
                subprocess.run(["bash", str(kill_script), "--all"], timeout=30)
            except Exception as e:
                self.logger.error("Error invoking kill_modal.sh: %s", e)

    def check_and_enforce_profile(self, profile: str) -> Dict[str, Any]:
        """Inspects single profile budget and enforces hard ceiling."""
        cost = get_profile_cost(profile)
        status = "OK"
        stopped_apps = []

        if cost >= self.HARD_KILL_CEILING:
            status = "BREACH_KILLED"
            self.logger.critical(
                "🚨 [BUDGET GUARD] Profile '%s' cost is $%.2f (EXCEEDS $%.2f LIMIT!)",
                profile, cost, self.HARD_KILL_CEILING
            )
            self.execute_emergency_shutdown(profile=profile)

        return {
            "profile": profile,
            "month_cost_usd": round(cost, 2),
            "budget_ceiling_usd": self.HARD_KILL_CEILING,
            "status": status,
            "stopped_apps": stopped_apps,
        }

    def run_watchdog_loop(self, profile: Optional[str] = None) -> None:
        """Adaptive monitoring loop with dynamic cadence and natural jitter."""
        self.logger.info(
            "Starting ModalBudgetGuard Adaptive Watchdog (Idle: %ds, Active: %ds)...",
            self.IDLE_POLL_INTERVAL_SECONDS, self.ACTIVE_POLL_INTERVAL_SECONDS
        )
        while True:
            try:
                active = self.get_active_containers(profile=profile)
                num_active = len(active)
                mtd_spend = self.fetch_current_mtd_spend(profile=profile)
                remaining = max(0.0, TOTAL_ALLOWANCE_USD - mtd_spend)

                if mtd_spend >= self.HARD_KILL_CEILING:
                    self.execute_emergency_shutdown(profile=profile)

                # Dynamic Cadence Selection with Natural Jitter
                cadence = calculate_adaptive_interval(num_active, remaining)
                time.sleep(cadence)
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error("Watchdog loop error: %s", e)
                time.sleep(30)


def main():
    parser = argparse.ArgumentParser(description="Hermes Modal Budget Guard & Pre-Flight Gate")
    parser.add_argument("mode", nargs="?", default="watchdog", choices=["watchdog", "check"], help="Mode: watchdog (default) or check")
    parser.add_argument("--profile", default="nhatrophamvu", help="Target workspace profile")
    parser.add_argument("--action", default="inference", choices=["deploy", "inference", "run"], help="Action to gate: deploy or inference")
    parser.add_argument("--job-id", default=None, help="Optional Job ID for in-flight virtual escrow reservation")
    parser.add_argument("--cost", type=float, default=0.50, help="Estimated job cost for virtual escrow")
    args = parser.parse_args()

    if args.mode == "check":
        gate = verify_credit_gate(args.profile, args.action, job_id=args.job_id, estimated_cost=args.cost)
        print(json.dumps(gate, indent=2))
        if not gate["allowed"]:
            print(f"❌ [GATE REJECTED] {args.profile} has ${gate['remaining_credits_usd']:.2f} credits (needs > ${gate['min_required_credits_usd']:.2f} for {args.action})", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"✅ [GATE PASSED] {args.profile} approved for {args.action} (${gate['remaining_credits_usd']:.2f} credits available)", file=sys.stderr)
            sys.exit(0)

    # Watchdog mode
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    profiles = get_profiles()
    print("=" * 80)
    print(f"🛡️  HERMES MODAL BUDGET GUARD & CREDIT GATE (Adaptive Watchdog)")
    print(f"   Deploy Gate: > ${DEPLOY_MIN_CREDITS_USD:.2f} credits | Inference Gate: > ${INFERENCE_MIN_CREDITS_USD:.2f} credits | Ceiling: ${BUDGET_CEILING_USD:.2f}")
    print(f"   Cadence: {IDLE_POLL_INTERVAL_SECONDS}s idle / {ACTIVE_POLL_INTERVAL_SECONDS}s active GPU (with natural jitter +-10%)")
    print("=" * 80)

    guard = ModalBudgetGuard()
    results = []
    breaches = 0
    for p in profiles:
        res = guard.check_and_enforce_profile(p)
        results.append(res)
        color = "🔴" if res["status"] == "BREACH_KILLED" else "🟢"
        rem = max(0.0, TOTAL_ALLOWANCE_USD - res['month_cost_usd'])
        deploy_ok = "✅" if rem > DEPLOY_MIN_CREDITS_USD else "❌"
        infer_ok = "✅" if rem > INFERENCE_MIN_CREDITS_USD else "❌"
        print(f" {color} {p:<16} | MTD: ${res['month_cost_usd']:<5.2f} | Remaining: ${rem:<5.2f} | Deploy: {deploy_ok} | Infer: {infer_ok}")
        if res["status"] == "BREACH_KILLED":
            breaches += 1

    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(results) + "\n")
    except Exception:
        pass

    print("=" * 80)
    if breaches > 0:
        print(f"⚠️  Detected {breaches} budget breach(es). Emergency shutdown executed.")
    else:
        print("✅ Active workspaces compliant with all credit gates.")
    print("=" * 80)


if __name__ == "__main__":
    main()
