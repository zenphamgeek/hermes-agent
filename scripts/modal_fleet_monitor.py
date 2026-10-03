#!/usr/bin/env python3
"""
scripts/modal_fleet_monitor.py
==============================
Hermes Agent - Modal.com Multi-Profile Fleet Monitor & Telemetry Engine.

Features:
- Reads all 15 Workspace Profiles from modal_token_profile.md and ~/.modal.toml
- Queries Modal CLI in parallel (ThreadPoolExecutor) for:
  * Deployed & Running Apps
  * Active Containers / Workers
  * Current Month Billing / Usage Cost (USD)
- Generates structured JSON output for UI Dashboard and terminal reports
"""

import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List

WORKSPACE_ROOT = Path("/home/zen/hermes-agent")
TOML_PATH = Path(os.path.expanduser("~/.modal.toml"))
MD_PATH = WORKSPACE_ROOT / "modal_token_profile.md"
OUTPUT_JSON = WORKSPACE_ROOT / "output" / "modal_fleet_status.json"


def load_toml_profiles() -> Dict[str, Dict[str, Any]]:
    if not TOML_PATH.exists():
        return {}
    import toml
    try:
        with open(TOML_PATH) as f:
            return toml.load(f)
    except Exception as e:
        print(f"[!] Warning reading ~/.modal.toml: {e}", file=sys.stderr)
        return {}


def load_md_profiles() -> List[Dict[str, Any]]:
    if not MD_PATH.exists():
        return []
    records = []
    current_account = "just.ask.mr.zen@gmail.com"
    with open(MD_PATH) as f:
        for idx, line in enumerate(f, 1):
            line_s = line.strip()
            if line_s.startswith("# -----") or line_s.startswith("# ----"):
                current_account = re.sub(r"^[#\s\-]+", "", line_s).strip()
            elif "modal token set" in line_s:
                tid_m = re.search(r"--token-id\s+([^\s]+)", line_s)
                tsec_m = re.search(r"--token-secret\s+([^\s]+)", line_s)
                prof_m = re.search(r"--profile=([^\s]+)", line_s)
                records.append({
                    "line": idx,
                    "account": current_account,
                    "profile": prof_m.group(1) if prof_m else "default",
                    "token_id": tid_m.group(1) if tid_m else None,
                    "token_secret": tsec_m.group(1) if tsec_m else None,
                })
    return records


def inspect_profile(profile_name: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    t0 = time.time()
    env = dict(os.environ, MODAL_PROFILE=profile_name)
    
    # 1. Inspect Apps
    apps = []
    try:
        res = subprocess.run(
            ["modal", "app", "list", "--json"],
            env=env,
            capture_output=True,
            text=True,
            timeout=12
        )
        if res.returncode == 0 and res.stdout.strip():
            apps = json.loads(res.stdout)
    except Exception as e:
        pass

    # 2. Inspect Running Containers / Workers
    containers = []
    try:
        res = subprocess.run(
            ["modal", "container", "list", "--json"],
            env=env,
            capture_output=True,
            text=True,
            timeout=12
        )
        if res.returncode == 0 and res.stdout.strip():
            containers = json.loads(res.stdout)
    except Exception as e:
        pass

    # 3. Inspect Billing Report
    cost = 0.0
    billing_entries = []
    try:
        res = subprocess.run(
            ["modal", "billing", "report", "--for", "this month", "--json"],
            env=env,
            capture_output=True,
            text=True,
            timeout=12
        )
        if res.returncode == 0 and res.stdout.strip():
            billing_entries = json.loads(res.stdout)
            cost = sum(float(b.get("Cost", 0)) for b in billing_entries)
    except Exception as e:
        pass

    return {
        "profile": profile_name,
        "token_id": cfg.get("token_id"),
        "is_active_default": cfg.get("active", False),
        "apps_total": len(apps),
        "deployed_apps": [a.get("Description") for a in apps if a.get("State") == "deployed"],
        "deployed_count": sum(1 for a in apps if a.get("State") == "deployed"),
        "workers_running": len(containers),
        "worker_details": containers,
        "month_cost_usd": round(cost, 2),
        "billing_entries_count": len(billing_entries),
        "query_latency_sec": round(time.time() - t0, 2),
        "status": "online"
    }


def collect_fleet_telemetry() -> Dict[str, Any]:
    toml_profiles = load_toml_profiles()
    md_records = load_md_profiles()
    
    # Run inspections in parallel across active profiles
    telemetry_profiles = []
    with ThreadPoolExecutor(max_workers=max(1, len(toml_profiles))) as executor:
        futures = [
            executor.submit(inspect_profile, p, cfg)
            for p, cfg in toml_profiles.items()
        ]
        telemetry_profiles = [f.result() for f in futures]
    
    total_cost = sum(p["month_cost_usd"] for p in telemetry_profiles)
    total_workers = sum(p["workers_running"] for p in telemetry_profiles)
    total_apps_deployed = sum(p["deployed_count"] for p in telemetry_profiles)
    
    fleet_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": {
            "total_registered_workspaces": 15,
            "profiles_in_toml": len(toml_profiles),
            "total_workers_active": total_workers,
            "total_deployed_apps": total_apps_deployed,
            "total_month_cost_usd": round(total_cost, 2),
            "active_default_profile": next((p["profile"] for p in telemetry_profiles if p["is_active_default"]), "r2rgraph")
        },
        "toml_profiles": telemetry_profiles,
        "all_workspace_registry": md_records
    }
    
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w") as f:
        json.dump(fleet_data, f, indent=2)
        
    return fleet_data


def print_cli_report(data: Dict[str, Any]):
    summary = data["summary"]
    print("=" * 80)
    print(" 🚀 HERMES AGENT - MODAL.COM MULTI-GPU FLEET TELEMETRY")
    print("=" * 80)
    print(f" Total Registered Workspaces : {summary['total_registered_workspaces']}")
    print(f" Loaded Profiles in TOML     : {summary['profiles_in_toml']}")
    print(f" Active Default Profile      : {summary['active_default_profile']}")
    print(f" Total Active Workers        : {summary['total_workers_active']}")
    print(f" Total Deployed Apps         : {summary['total_deployed_apps']}")
    print(f" Fleet MTD Cost (USD)        : ${summary['total_month_cost_usd']:.2f}")
    print("-" * 80)
    print(f" {'Profile':<12} | {'Token ID':<26} | {'Apps':<6} | {'Workers':<8} | {'Cost (USD)':<10} | {'Status'}")
    print("-" * 80)
    for p in data["toml_profiles"]:
        act = " [ACTIVE]" if p["is_active_default"] else ""
        print(f" {p['profile']:<12} | {str(p['token_id']):<26} | {p['deployed_count']:<6} | {p['workers_running']:<8} | ${p['month_cost_usd']:<9.2f} | {p['status']}{act}")
    print("=" * 80)
    print(f" [✓] Status snapshot cached to: {OUTPUT_JSON}\n")


if __name__ == "__main__":
    data = collect_fleet_telemetry()
    print_cli_report(data)
