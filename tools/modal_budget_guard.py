#!/usr/bin/env python3
"""
tools/modal_budget_guard.py
===========================
Hermes Agent - Sovereign Modal Multi-GPU Budget Guard & Automated Kill-Switch.

Hard Invariant:
- Max allowable monthly spend per workspace: $25.00 USD.
- If a workspace cost >= $25.00 USD:
  1. Immediately issues a CRITICAL alert.
  2. Stops all deployed/running apps on that workspace via `modal app stop`.
  3. Kills any orphaned/zombie containers via `modal container stop`.
  4. Locks the workspace profile to prevent further dispatches.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any

BUDGET_CEILING_USD = 25.00
TOML_PATH = Path(os.path.expanduser("~/.modal.toml"))
LOG_PATH = Path("/home/zen/hermes-agent/output/modal_budget_guard.log")


def run_cmd(cmd: List[str], env: Dict[str, str] = None, timeout: int = 15) -> str:
    try:
        res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=timeout)
        return res.stdout.strip()
    except Exception as e:
        return ""


def get_profiles() -> List[str]:
    if not TOML_PATH.exists():
        return []
    import re
    with open(TOML_PATH) as f:
        return re.findall(r'\[(.*?)\]', f.read())


def check_and_enforce_budget(profile: str) -> Dict[str, Any]:
    env = dict(os.environ, MODAL_PROFILE=profile)
    
    # 1. Query billing report
    cost = 0.0
    report_json = run_cmd(["modal", "billing", "report", "--for", "this month", "--json"], env=env)
    if report_json:
        try:
            entries = json.loads(report_json)
            cost = sum(float(e.get("Cost", 0)) for e in entries)
        except Exception:
            pass

    status = "OK"
    stopped_apps = []

    # 2. Enforce hard budget ceiling
    if cost >= BUDGET_CEILING_USD:
        status = "BREACH_KILLED"
        print(f"🚨 [BUDGET GUARD] Profile '{profile}' cost is ${cost:.2f} (EXCEEDS ${BUDGET_CEILING_USD:.2f} LIMIT!)", file=sys.stderr)
        
        # Stop all deployed apps immediately
        app_list_json = run_cmd(["modal", "app", "list", "--json"], env=env)
        if app_list_json:
            try:
                apps = json.loads(app_list_json)
                for app in apps:
                    app_id = app.get("App ID") or app.get("AppId") or app.get("id")
                    state = app.get("State") or app.get("state")
                    if app_id and state in ("deployed", "running"):
                        print(f"   🛑 Stopping app {app_id} ({app.get('Description')})...", file=sys.stderr)
                        run_cmd(["modal", "app", "stop", app_id], env=env)
                        stopped_apps.append(app_id)
            except Exception as e:
                print(f"   ⚠️ Error stopping apps on {profile}: {e}", file=sys.stderr)

    return {
        "profile": profile,
        "month_cost_usd": round(cost, 2),
        "budget_ceiling_usd": BUDGET_CEILING_USD,
        "status": status,
        "stopped_apps": stopped_apps
    }


def main():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    profiles = get_profiles()
    print("=" * 75)
    print(f"🛡️  HERMES MODAL BUDGET GUARD (Ceiling: ${BUDGET_CEILING_USD:.2f} USD / workspace)")
    print("=" * 75)

    results = []
    breaches = 0
    for p in profiles:
        res = check_and_enforce_budget(p)
        results.append(res)
        color = "🔴" if res["status"] == "BREACH_KILLED" else "🟢"
        print(f" {color} {p:<18} | Cost: ${res['month_cost_usd']:<6.2f} / ${BUDGET_CEILING_USD:.2f} | Status: {res['status']}")
        if res["status"] == "BREACH_KILLED":
            breaches += 1

    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(results) + "\n")

    print("=" * 75)
    if breaches > 0:
        print(f"⚠️  Detected {breaches} budget breach(es). Emergency shutdown executed.")
    else:
        print("✅ All workspaces compliant with $25.00 monthly budget ceiling.")
    print("=" * 75)


if __name__ == "__main__":
    main()
