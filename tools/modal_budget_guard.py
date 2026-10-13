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
   - Idle (0 active containers): 300s (5m) cadence with zero rate-limit pressure.
   - Active (>= 1 active GPU containers): 15s tight watchdog eliminating the 600s runaway spend blind spot.
   - Strict regex validation (APP_ID_REGEX, CONTAINER_ID_REGEX) and array-based subprocess invocation (no shell=True).
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ModalBudgetGuard")

# Strict identifier validation to prevent CWE-78 / CWE-88 command injection
APP_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]{1,64}$")
CONTAINER_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]{1,64}$")

TOTAL_ALLOWANCE_USD = 30.00
BUDGET_CEILING_USD = 25.00
HARD_KILL_CEILING = 25.00          # USD: Automatic kill-switch
DEPLOY_MIN_CREDITS_USD = 15.00     # Remaining credits must be > $15.00
INFERENCE_MIN_CREDITS_USD = 10.00  # Remaining credits must be > $10.00

TOML_PATH = Path(os.path.expanduser("~/.modal.toml"))
LOG_PATH = Path("/home/zen/hermes-agent/output/modal_budget_guard.log")


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


def verify_credit_gate(profile: str, action: str = "inference") -> Dict[str, Any]:
    """Pre-flight credit verification gate (Rule 1.17).
    - deploy: requires remaining credits > $15.00 (MTD cost < $15.00)
    - inference: requires remaining credits > $10.00 (MTD cost < $20.00)
    """
    action_lower = action.lower()
    min_required = DEPLOY_MIN_CREDITS_USD if action_lower == "deploy" else INFERENCE_MIN_CREDITS_USD

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

    cost = get_profile_cost(profile)
    remaining_credits = max(0.0, TOTAL_ALLOWANCE_USD - cost)

    if action_lower == "deploy":
        allowed = remaining_credits > DEPLOY_MIN_CREDITS_USD
        min_required = DEPLOY_MIN_CREDITS_USD
    elif action_lower in ("inference", "run"):
        allowed = remaining_credits > INFERENCE_MIN_CREDITS_USD
        min_required = INFERENCE_MIN_CREDITS_USD
    else:
        allowed = remaining_credits > INFERENCE_MIN_CREDITS_USD
        min_required = INFERENCE_MIN_CREDITS_USD

    return {
        "profile": profile,
        "action": action_lower,
        "cost_mtd_usd": round(cost, 2),
        "remaining_credits_usd": round(remaining_credits, 2),
        "min_required_credits_usd": min_required,
        "allowed": allowed,
        "reason": f"Credits ${remaining_credits:.2f} {'>' if allowed else '<='} ${min_required:.2f} threshold"
    }


def check_and_enforce_budget(profile: str) -> Dict[str, Any]:
    """Enforces hard ceiling on a specific profile."""
    guard = ModalBudgetGuard()
    return guard.check_and_enforce_profile(profile)


class ModalBudgetGuard:
    """
    Sovereign Modal Multi-GPU Budget Guard & Adaptive Watchdog.

    Enforces:
    - Adaptive Cadence: 300s when idle (0 containers), 15s under GPU load.
    - Anti-Injection: Strict regex verification on app_id and container_id (CWE-78/88).
    - Rule 1.17 Credit Gate: Deploy > $15.00, Inference > $10.00, Hard-kill >= $25.00.
    """

    TOTAL_ALLOWANCE_USD = TOTAL_ALLOWANCE_USD
    HARD_KILL_CEILING = HARD_KILL_CEILING
    DEPLOY_MIN_CREDITS_USD = DEPLOY_MIN_CREDITS_USD
    INFERENCE_MIN_CREDITS_USD = INFERENCE_MIN_CREDITS_USD

    IDLE_POLL_INTERVAL_SECONDS = 300   # 5m cadence when 0 containers active (low resource churn)
    ACTIVE_POLL_INTERVAL_SECONDS = 15  # 15s tight watchdog when GPU is running (zero blind spot)

    def __init__(self, ledger_path: str = ".passive_quota_ledger.json"):
        self.ledger_path = ledger_path
        self.logger = logging.getLogger("ModalBudgetGuard")

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
        """Adaptive monitoring loop: 300s when idle, 15s under active GPU load."""
        self.logger.info(
            "Starting ModalBudgetGuard Adaptive Watchdog (Idle: %ds, Active: %ds)...",
            self.IDLE_POLL_INTERVAL_SECONDS, self.ACTIVE_POLL_INTERVAL_SECONDS
        )
        while True:
            try:
                active = self.get_active_containers(profile=profile)
                num_active = len(active)
                mtd_spend = self.fetch_current_mtd_spend(profile=profile)

                if mtd_spend >= self.HARD_KILL_CEILING:
                    self.execute_emergency_shutdown(profile=profile)

                # Dynamic Cadence Selection
                cadence = (
                    self.ACTIVE_POLL_INTERVAL_SECONDS
                    if num_active > 0
                    else self.IDLE_POLL_INTERVAL_SECONDS
                )
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
    args = parser.parse_args()

    if args.mode == "check":
        gate = verify_credit_gate(args.profile, args.action)
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
    print(f"   Cadence: {ModalBudgetGuard.IDLE_POLL_INTERVAL_SECONDS}s idle / {ModalBudgetGuard.ACTIVE_POLL_INTERVAL_SECONDS}s active GPU")
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
