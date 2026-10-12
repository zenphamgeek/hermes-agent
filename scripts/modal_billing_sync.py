#!/usr/bin/env python3
"""
modal_billing_sync.py
======================
Production Modal Billing & Workspace Usage Sync Engine for Hermes Agent & AgyRouter.

Context:
1. Modal CLI: `modal billing report --for "this month" --json` with MODAL_PROFILE=<workspace_profile>.
   Returns JSON array of items: [{"Object ID": "ap-...", "Description": "...", "Cost": "3.42249039", ...}].
2. Total spend is the sum of float(item["Cost"]).
3. App breakdown is: dict mapping Description -> round(sum(Cost), 4).
4. Supports 20 canonical workspaces with baseline spend and metadata.
   Preserves special baseline for `just-ask-mr-zen` ($25.00 overdue invoice).
5. Interacts with profiles configured in ~/.modal.toml.
6. Persistence files:
   - Ledger: /home/zen/hermes-agent/output/modal_billing_ledger.json (fallback .modal_billing_ledger.json)
   - Workspace Headroom Status: /home/zen/hermes-agent/output/modal_workspace_headroom_status.json

Architecture & Operational Invariants:
- Thread-safe operations via threading.Lock.
- Cache TTL: 1800s (30 minutes) default. Instant response if cache is fresh without CLI execution.
- Stochastic delay & jitter for stealth compliance.
- Background rotating sync daemon thread for staggered probing.
- Singleton pattern via get_billing_sync_engine().
"""

import datetime
import json
import logging
import os
import random
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Attempt to load TOML parser (tomllib in 3.11+, fallback to toml/tomli or regex parser)
try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib  # type: ignore
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            tomllib = None  # Handled with internal regex fallback

logger = logging.getLogger("modal_billing_sync")
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(
        logging.Formatter("[%(asctime)s] [%(levelname)s] [ModalBillingSync] %(message)s")
    )
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)

# Default File Paths
PRIMARY_OUTPUT_DIR = Path("/home/zen/hermes-agent/output")
PRIMARY_LEDGER_PATH = PRIMARY_OUTPUT_DIR / "modal_billing_ledger.json"
FALLBACK_LEDGER_PATH = Path(".modal_billing_ledger.json")

PRIMARY_HEADROOM_PATH = PRIMARY_OUTPUT_DIR / "modal_workspace_headroom_status.json"
FALLBACK_HEADROOM_PATH = Path(".modal_workspace_headroom_status.json")

# Special Baselines (MTD minimum overrides)
SPECIAL_BASELINES: Dict[str, float] = {
    "just-ask-mr-zen": 25.00,  # Overdue invoice baseline
}

# 20 Canonical Workspaces Specifications
CANONICAL_20_METADATA: List[Dict[str, Any]] = [
    {"workspace": "just-ask-mr-zen", "account": "just.ask.mr.zen@gmail.com", "tier": "A100-80GB", "budget": 30.0},
    {"workspace": "zenpeace", "account": "just.ask.mr.zen@gmail.com", "tier": "T4", "budget": 30.0},
    {"workspace": "mindful", "account": "just.ask.mr.zen@gmail.com", "tier": "A100-80GB", "budget": 30.0},
    {"workspace": "zenguru", "account": "just.ask.mr.zen@gmail.com", "tier": "T4", "budget": 30.0},
    {"workspace": "zenmaster", "account": "just.ask.mr.zen@gmail.com", "tier": "A100-80GB", "budget": 30.0},
    {"workspace": "nhatrophamvu", "account": "nhatrophamvu@gmail.com", "tier": "T4", "budget": 30.0},
    {"workspace": "asmr", "account": "nhatrophamvu@gmail.com", "tier": "T4", "budget": 30.0},
    {"workspace": "vi2vi", "account": "nhatrophamvu@gmail.com", "tier": "T4", "budget": 30.0},
    {"workspace": "pvvsf", "account": "nhatrophamvu@gmail.com", "tier": "T4", "budget": 30.0},
    {"workspace": "phi4", "account": "nhatrophamvu@gmail.com", "tier": "L4", "budget": 30.0},
    {"workspace": "mojopham", "account": "mojopham@gmail.com", "tier": "A100-80GB", "budget": 30.0},
    {"workspace": "diatts", "account": "mojopham@gmail.com", "tier": "T4", "budget": 30.0},
    {"workspace": "mvlm", "account": "mojopham@gmail.com", "tier": "A100-80GB", "budget": 30.0},
    {"workspace": "vrag", "account": "mojopham@gmail.com", "tier": "T4", "budget": 30.0},
    {"workspace": "zenonmind", "account": "zenonmind@gmail.com", "tier": "A100-80GB", "budget": 30.0},
    {"workspace": "lovenovel", "account": "zenonmind@gmail.com", "tier": "A100-80GB", "budget": 30.0},
    {"workspace": "vieturbo", "account": "zenonmind@gmail.com", "tier": "T4", "budget": 30.0},
    {"workspace": "insimind", "account": "zenonmind@gmail.com", "tier": "L4", "budget": 30.0},
    {"workspace": "zenonts", "account": "zenonmind@gmail.com", "tier": "T4", "budget": 30.0},
]


def _find_modal_config_file() -> Path:
    """Locates the active .modal.toml configuration file."""
    env_path = os.environ.get("MODAL_CONFIG_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    candidates = [
        Path.home() / ".modal.toml",
        Path("/home/zen/.modal.toml"),
        Path("/root/.modal.toml"),
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


class ModalBillingSyncEngine:
    """
    Core synchronization engine for Modal.com workspaces billing data.
    Thread-safe, TTL cached, resilient to CLI failures, and compliant with stealth quotas.
    """

    def __init__(
        self,
        ledger_file: Optional[Path] = None,
        headroom_file: Optional[Path] = None,
        cache_ttl_seconds: int = 1800,
        modal_config_path: Optional[Path] = None,
        fleet_policy_path: Optional[Path] = None,
    ) -> None:
        self.ledger_file = Path(ledger_file) if ledger_file else PRIMARY_LEDGER_PATH
        self.headroom_file = Path(headroom_file) if headroom_file else PRIMARY_HEADROOM_PATH
        self.cache_ttl = int(cache_ttl_seconds)
        self.modal_config_path = Path(modal_config_path) if modal_config_path else _find_modal_config_file()
        self.fleet_policy_path = Path(fleet_policy_path) if fleet_policy_path else None

        self._lock = threading.Lock()
        self._last_sync_timestamp: float = 0.0
        self._memory_cache: Optional[Dict[str, Any]] = None
        self._background_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Pre-load cache from disk if available
        self._load_ledger_from_disk()

    def _get_configured_profiles(self) -> List[str]:
        """Profiles from ~/.modal.toml minus fleet-excluded workspaces (output/modal_fleet_policy.json)."""
        from scripts.modal_fleet_server import load_fleet_policy  # single source of truth
        policy_path = getattr(self, "fleet_policy_path", None) or (Path(__file__).resolve().parent.parent / "output" / "modal_fleet_policy.json")
        policy = load_fleet_policy(policy_path)
        if policy.get("_degraded"):
            raise RuntimeError("Fleet policy degraded (fail-closed): refusing to probe any profiles.")
        excl = set(policy.get("excluded", []))
        return [p for p in self._get_configured_profiles_raw() if p not in excl]


    def _get_configured_profiles_raw(self) -> List[str]:
        """Parses active workspace profiles from ~/.modal.toml."""
        if not self.modal_config_path.exists():
            # Check secondary location
            alt = Path("/home/zen/.modal.toml")
            if alt.exists():
                self.modal_config_path = alt
            else:
                logger.warning(f"Modal configuration file not found at {self.modal_config_path}")
                return []

        try:
            if tomllib is not None:
                # Standard Python tomllib binary read
                with open(self.modal_config_path, "rb") as f:
                    data = tomllib.load(f)
                return list(data.keys())
            else:
                # Regex fallback for [profile_name] sections
                import re
                profiles = []
                with open(self.modal_config_path, "r", encoding="utf-8") as f:
                    for line in f:
                        m = re.match(r"^\s*\[([a-zA-Z0-9_\-]+)\]", line)
                        if m:
                            profiles.append(m.group(1))
                return profiles
        except Exception as e:
            logger.warning(f"Error reading profiles from {self.modal_config_path}: {e}")
            return []

    def _load_ledger_from_disk(self) -> Dict[str, Any]:
        """Loads persistent billing ledger with fallback support."""
        with self._lock:
            target_path = self.ledger_file
            if not target_path.exists() and FALLBACK_LEDGER_PATH.exists():
                target_path = FALLBACK_LEDGER_PATH

            if target_path.exists():
                try:
                    content = target_path.read_text(encoding="utf-8")
                    data = json.loads(content)
                    self._memory_cache = data
                    self._last_sync_timestamp = float(data.get("timestamp", 0.0))
                    return data
                except Exception as e:
                    logger.warning(f"Failed to read ledger from {target_path}: {e}")

            default_ledger: Dict[str, Any] = {
                "timestamp": 0.0,
                "iso_timestamp": "",
                "total_spend_usd": 0.0,
                "total_fleet_spend_usd": 0.0,
                "profiles_synced": 0,
                "workspaces": {},
            }
            self._memory_cache = default_ledger
            return default_ledger

    def _save_ledger_to_disk(self, data: Dict[str, Any]) -> None:
        """Atomically saves billing ledger with fallback support."""
        target_path = self.ledger_file
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            target_path = FALLBACK_LEDGER_PATH
            target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            tmp = target_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(target_path)
            self._memory_cache = data
            self._last_sync_timestamp = float(data.get("timestamp", time.time()))
        except Exception as e:
            logger.error(f"Failed to write ledger file {target_path}: {e}")
            try:
                # Emergency fallback write
                FALLBACK_LEDGER_PATH.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
                )
                self._memory_cache = data
                self._last_sync_timestamp = float(data.get("timestamp", time.time()))
            except Exception as e2:
                logger.error(f"Fallback ledger write failed: {e2}")

    def sync_single_workspace(self, profile: str) -> Dict[str, Any]:
        """
        Runs `modal billing report --for "this month" --json` with MODAL_PROFILE=<profile>.
        Enforces a 15-second timeout, parses stdout JSON, sums Cost, and calculates by_app breakdown.
        Updates internal cache and storage.
        """
        now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Handle special baselines for unconfigured profiles
        configured = self._get_configured_profiles()
        if profile in SPECIAL_BASELINES and profile not in configured:
            baseline_val = SPECIAL_BASELINES[profile]
            ws_entry = {
                "total_spend_usd": baseline_val,
                "items_count": 1,
                "by_app": {"overdue_invoice_baseline": baseline_val},
                "last_synced_at": now_iso,
                "status": "baseline_applied",
            }
            self._apply_single_workspace_update(profile, ws_entry)
            return ws_entry

        env = os.environ.copy()
        env["MODAL_PROFILE"] = profile
        if self.modal_config_path and self.modal_config_path.exists():
            env["MODAL_CONFIG_PATH"] = str(self.modal_config_path)

        cmd = ["modal", "billing", "report", "--for", "this month", "--json"]
        total_spend = 0.0
        by_app: Dict[str, float] = {}
        items_count = 0
        status = "nominal"

        try:
            res = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=15.0,
            )
            if res.returncode == 0:
                raw_items = json.loads(res.stdout) if res.stdout.strip() else []
                items_count = len(raw_items)
                for item in raw_items:
                    cost_val = float(item.get("Cost", 0.0) or 0.0)
                    total_spend += cost_val
                    desc = str(item.get("Description", "unknown")).strip()
                    by_app[desc] = by_app.get(desc, 0.0) + cost_val

                # Preserve baseline override if applicable
                if profile in SPECIAL_BASELINES and total_spend < SPECIAL_BASELINES[profile]:
                    total_spend = SPECIAL_BASELINES[profile]
                    by_app["overdue_invoice_baseline"] = SPECIAL_BASELINES[profile]
                    status = "baseline_applied"
            else:
                err_text = res.stderr.strip()[:100]
                status = f"cli_error: {err_text}" if err_text else f"exit_{res.returncode}"
                logger.warning(f"Billing query failed for profile '{profile}': {status}")
                if profile in SPECIAL_BASELINES:
                    total_spend = SPECIAL_BASELINES[profile]
                    by_app["overdue_invoice_baseline"] = SPECIAL_BASELINES[profile]
                    items_count = 1
                    status = "baseline_applied"
        except subprocess.TimeoutExpired:
            status = "timeout_15s"
            logger.warning(f"Modal billing report timed out after 15s for profile '{profile}'")
            if profile in SPECIAL_BASELINES:
                total_spend = SPECIAL_BASELINES[profile]
                by_app["overdue_invoice_baseline"] = SPECIAL_BASELINES[profile]
                items_count = 1
                status = "baseline_applied"
        except Exception as e:
            status = f"exception: {str(e)[:80]}"
            logger.error(f"Unexpected error querying billing for '{profile}': {e}")
            if profile in SPECIAL_BASELINES:
                total_spend = SPECIAL_BASELINES[profile]
                by_app["overdue_invoice_baseline"] = SPECIAL_BASELINES[profile]
                items_count = 1
                status = "baseline_applied"

        ws_entry = {
            "total_spend_usd": round(total_spend, 4),
            "items_count": items_count,
            "by_app": {k: round(v, 4) for k, v in by_app.items()},
            "last_synced_at": now_iso,
            "status": status,
        }

        self._apply_single_workspace_update(profile, ws_entry)
        return ws_entry

    def _apply_single_workspace_update(self, profile: str, ws_entry: Dict[str, Any]) -> None:
        """Helper to thread-safely update ledger and headroom files with a single workspace."""
        with self._lock:
            ledger = dict(self._memory_cache or self._load_ledger_from_disk())
            workspaces = ledger.setdefault("workspaces", {})
            workspaces[profile] = ws_entry

            now_ts = time.time()
            now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            total_fleet = sum(float(w.get("total_spend_usd", 0.0)) for w in workspaces.values())
            ledger["total_spend_usd"] = round(total_fleet, 4)
            ledger["total_fleet_spend_usd"] = round(total_fleet, 4)
            ledger["timestamp"] = now_ts
            ledger["iso_timestamp"] = now_iso

            self._save_ledger_to_disk(ledger)
            self._update_headroom_status_file(workspaces)

    def sync_all(self, force: bool = False, delay_between_s: float = 0.25) -> Dict[str, Any]:
        """
        Synchronizes all profiles configured in ~/.modal.toml with jitter/delay.
        Preserves special baselines (e.g. just-ask-mr-zen = $25.00).
        Aggregates total fleet spend, updates ledger and headroom status.
        """
        now = time.time()
        # Fast exit if cache is fresh and force is False
        if not force and self._memory_cache and (now - self._last_sync_timestamp) < self.cache_ttl:
            logger.info("Serving Modal billing data from fresh cache (< TTL)")
            return self._memory_cache

        with self._lock:
            # Re-check under lock in case another thread refreshed
            if not force and self._memory_cache and (time.time() - self._last_sync_timestamp) < self.cache_ttl:
                return self._memory_cache

            profiles = self._get_configured_profiles()
            logger.info(f"Initiating Modal Billing sync across {len(profiles)} profiles...")

            ws_results: Dict[str, Any] = {}
            total_fleet_spend = 0.0
            env_base = os.environ.copy()
            if self.modal_config_path and self.modal_config_path.exists():
                env_base["MODAL_CONFIG_PATH"] = str(self.modal_config_path)

            now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            # 1. Query each profile in .modal.toml
            for idx, p in enumerate(profiles):
                env = {**env_base, "MODAL_PROFILE": p}
                cmd = ["modal", "billing", "report", "--for", "this month", "--json"]

                total_spend = 0.0
                by_app: Dict[str, float] = {}
                items_count = 0
                status = "nominal"

                try:
                    res = subprocess.run(
                        cmd,
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=15.0,
                    )
                    if res.returncode == 0:
                        raw_items = json.loads(res.stdout) if res.stdout.strip() else []
                        items_count = len(raw_items)
                        for item in raw_items:
                            cost_val = float(item.get("Cost", 0.0) or 0.0)
                            total_spend += cost_val
                            desc = str(item.get("Description", "unknown")).strip()
                            by_app[desc] = by_app.get(desc, 0.0) + cost_val
                    else:
                        err_text = res.stderr.strip()[:100]
                        status = f"cli_error: {err_text}" if err_text else f"exit_{res.returncode}"
                        logger.warning(f"Profile '{p}' billing returned error: {status}")
                except subprocess.TimeoutExpired:
                    status = "timeout_15s"
                    logger.warning(f"Profile '{p}' billing report timed out (15s)")
                except Exception as e:
                    status = f"exception: {str(e)[:80]}"
                    logger.error(f"Error querying billing for '{p}': {e}")

                # Preserve baseline override if applicable
                if p in SPECIAL_BASELINES and total_spend < SPECIAL_BASELINES[p]:
                    total_spend = SPECIAL_BASELINES[p]
                    by_app["overdue_invoice_baseline"] = SPECIAL_BASELINES[p]
                    status = "baseline_applied"

                ws_entry = {
                    "total_spend_usd": round(total_spend, 4),
                    "items_count": items_count,
                    "by_app": {k: round(v, 4) for k, v in by_app.items()},
                    "last_synced_at": now_iso,
                    "status": status,
                }
                ws_results[p] = ws_entry
                total_fleet_spend += total_spend

                # Small jitter delay between queries to ensure stealth mode compliance
                if delay_between_s > 0 and idx < len(profiles) - 1:
                    jitter = random.uniform(0.05, 0.15)
                    time.sleep(delay_between_s + jitter)

            # 2. Add special baselines for canonical workspaces not in profiles
            for ws_special, baseline_usd in SPECIAL_BASELINES.items():
                if ws_special not in ws_results:
                    ws_results[ws_special] = {
                        "total_spend_usd": baseline_usd,
                        "items_count": 1,
                        "by_app": {"overdue_invoice_baseline": baseline_usd},
                        "last_synced_at": now_iso,
                        "status": "baseline_applied",
                    }
                    total_fleet_spend += baseline_usd

            # 3. Ensure all 20 canonical workspaces exist in output
            for meta in CANONICAL_20_METADATA:
                ws_name = meta["workspace"]
                if ws_name not in ws_results:
                    ws_results[ws_name] = {
                        "total_spend_usd": 0.0,
                        "items_count": 0,
                        "by_app": {},
                        "last_synced_at": now_iso,
                        "status": "nominal",
                    }

            ledger_payload = {
                "timestamp": time.time(),
                "iso_timestamp": now_iso,
                "total_spend_usd": round(total_fleet_spend, 4),
                "total_fleet_spend_usd": round(total_fleet_spend, 4),
                "profiles_synced": len(profiles),
                "workspaces": ws_results,
            }

            self._save_ledger_to_disk(ledger_payload)
            self._update_headroom_status_file(ws_results)
            logger.info(
                f"Billing sync complete: Total Fleet Spend = ${total_fleet_spend:.4f} across {len(ws_results)} workspaces"
            )
            return ledger_payload

    def _update_headroom_status_file(self, ws_billing: Dict[str, Any]) -> None:
        """
        Updates modal_workspace_headroom_status.json with latest estimated_spent and headroom score.
        Formula:
          remaining_budget = max(0.0, budget - estimated_spent)
          headroom_score = (1.0 * remaining_budget) - (15.0 * active_workers) - (5.0 * probes_today)
        """
        target_path = self.headroom_file
        existing_list: List[Dict[str, Any]] = []

        # Try reading primary or fallback headroom file
        read_path = target_path if target_path.exists() else (
            FALLBACK_HEADROOM_PATH if FALLBACK_HEADROOM_PATH.exists() else None
        )
        if read_path and read_path.exists():
            try:
                existing_list = json.loads(read_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Could not parse existing headroom file {read_path}: {e}")
                existing_list = []

        existing_map = {
            item.get("workspace"): item for item in existing_list if isinstance(item, dict)
        }

        updated_list: List[Dict[str, Any]] = []

        for meta in CANONICAL_20_METADATA:
            ws_name = meta["workspace"]
            existing = existing_map.get(ws_name, {})

            budget = float(existing.get("budget", meta.get("budget", 30.0)))
            active_workers = int(existing.get("active_workers", 0))
            probes_today = int(existing.get("probes_today", 0))

            billing = ws_billing.get(ws_name, {})
            spent = float(billing.get("total_spend_usd", existing.get("estimated_spent", 0.0)))

            remaining_budget = round(max(0.0, budget - spent), 4)
            headroom_score = round(
                (1.0 * remaining_budget) - (15.0 * active_workers) - (5.0 * probes_today), 2
            )

            hard_ceiling = float(existing.get("hard_ceiling", 29.50))
            hard_ceiling_breached = bool(spent >= hard_ceiling)

            # Determine operational health status
            if hard_ceiling_breached:
                status = "critical"
            elif spent >= 25.0:
                status = "warning"
            else:
                status = existing.get("status", "healthy")

            entry: Dict[str, Any] = {
                "workspace": ws_name,
                "account": meta.get("account"),
                "tier": meta.get("tier"),
                "budget": budget,
                "active_workers": active_workers,
                "estimated_spent": round(spent, 4),
                "remaining_budget": remaining_budget,
                "headroom_score": headroom_score,
                "hard_ceiling": hard_ceiling,
                "hard_ceiling_breached": hard_ceiling_breached,
                "status": status,
            }

            if existing.get("watchlist") or ws_name == "just-ask-mr-zen":
                entry["watchlist"] = True

            if billing.get("by_app"):
                entry["app_breakdown"] = billing.get("by_app")

            updated_list.append(entry)

        # Preserve any non-canonical entries present in existing_list or in ws_billing
        canonical_names = {m["workspace"] for m in CANONICAL_20_METADATA}
        all_extra_keys = (set(existing_map.keys()) | set(ws_billing.keys())) - canonical_names
        for extra_ws in sorted(all_extra_keys):
            extra_entry = dict(existing_map.get(extra_ws, {
                "workspace": extra_ws,
                "account": "unknown",
                "tier": "unknown",
                "budget": 30.0,
                "active_workers": 0,
                "probes_today": 0,
                "hard_ceiling": 29.50,
                "status": "healthy",
            }))
            billing = ws_billing.get(extra_ws, {})
            extra_spent = float(billing.get("total_spend_usd", extra_entry.get("estimated_spent", 0.0)))
            extra_budget = float(extra_entry.get("budget", 30.0))
            active_workers = int(extra_entry.get("active_workers", 0))
            probes_today = int(extra_entry.get("probes_today", 0))
            hard_ceiling = float(extra_entry.get("hard_ceiling", 29.50))
            hard_ceiling_breached = bool(extra_spent >= hard_ceiling)

            if hard_ceiling_breached:
                status = "critical"
            elif extra_spent >= 25.0:
                status = "warning"
            else:
                status = extra_entry.get("status", "healthy")

            extra_entry["estimated_spent"] = round(extra_spent, 4)
            extra_entry["remaining_budget"] = round(max(0.0, extra_budget - extra_spent), 4)
            extra_entry["headroom_score"] = round(
                (1.0 * extra_entry["remaining_budget"])
                - (15.0 * active_workers)
                - (5.0 * probes_today),
                2,
            )
            extra_entry["hard_ceiling"] = hard_ceiling
            extra_entry["hard_ceiling_breached"] = hard_ceiling_breached
            extra_entry["status"] = status
            if billing.get("by_app"):
                extra_entry["app_breakdown"] = billing.get("by_app")
            updated_list.append(extra_entry)

        # Write to disk atomically
        write_target = target_path
        try:
            write_target.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            write_target = FALLBACK_HEADROOM_PATH
            write_target.parent.mkdir(parents=True, exist_ok=True)

        try:
            tmp = write_target.with_suffix(".tmp")
            tmp.write_text(json.dumps(updated_list, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(write_target)
        except Exception as e:
            logger.error(f"Failed to update headroom file {write_target}: {e}")
            try:
                FALLBACK_HEADROOM_PATH.write_text(
                    json.dumps(updated_list, indent=2, ensure_ascii=False), encoding="utf-8"
                )
            except Exception as e2:
                logger.error(f"Fallback headroom file write failed: {e2}")

    def get_billing_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Returns cached billing ledger data or triggers refresh if stale or force_refresh is True."""
        now = time.time()
        if not force_refresh and self._memory_cache and (now - self._last_sync_timestamp) < self.cache_ttl:
            return self._memory_cache
        return self.sync_all(force=force_refresh)

    def get_workspace_spend(self, workspace_name: str) -> float:
        """Returns MTD dollar spend for a specific workspace."""
        data = self.get_billing_data(force_refresh=False)
        workspaces = data.get("workspaces", {})
        ws = workspaces.get(workspace_name, {})
        return float(ws.get("total_spend_usd", 0.0))

    def get_workspace_breakdown(self, workspace_name: str) -> Dict[str, float]:
        """Returns itemized app spend breakdown for a specific workspace."""
        data = self.get_billing_data(force_refresh=False)
        workspaces = data.get("workspaces", {})
        ws = workspaces.get(workspace_name, {})
        return dict(ws.get("by_app", {}))

    def start_background_rotating_sync(self, interval_minutes: int = 15) -> None:
        """
        Starts a background daemon thread that updates 1 workspace every (interval_minutes / 20) minutes
        under stealth mode (ensures compliant probe frequency).
        """
        if self._background_thread and self._background_thread.is_alive():
            logger.info("Background rotating sync daemon is already running.")
            return

        def _rotating_worker() -> None:
            # interval_minutes / 20 in seconds
            base_sleep_s = max(10.0, (float(interval_minutes) * 60.0) / 20.0)
            logger.info(
                f"Modal Billing Background Rotating Sync started (cycle: {interval_minutes}m, step: {base_sleep_s:.1f}s)"
            )

            while not self._stop_event.is_set():
                try:
                    profiles = self._get_configured_profiles()
                    if profiles:
                        ledger = self._memory_cache or self._load_ledger_from_disk()
                        workspaces = ledger.get("workspaces", {})

                        def _parse_ts(p: str) -> float:
                            item = workspaces.get(p, {})
                            ts_str = item.get("last_synced_at", "")
                            if not ts_str:
                                return 0.0
                            try:
                                return datetime.datetime.fromisoformat(
                                    ts_str.replace("Z", "+00:00")
                                ).timestamp()
                            except Exception:
                                return 0.0

                        oldest_profile = min(profiles, key=_parse_ts)
                        logger.debug(f"[StealthRotatingSync] Probing oldest workspace: {oldest_profile}")
                        self.sync_single_workspace(oldest_profile)
                except Exception as e:
                    logger.error(f"[StealthRotatingSync] Error during rotating probe: {e}")

                # Sleep step with minor jitter
                step_jitter = random.uniform(-1.0, 1.0)
                actual_sleep = max(5.0, base_sleep_s + step_jitter)
                self._stop_event.wait(actual_sleep)

        self._stop_event.clear()
        self._background_thread = threading.Thread(
            target=_rotating_worker,
            name="ModalBillingRotatingSyncDaemon",
            daemon=True,
        )
        self._background_thread.start()

    def stop_background_sync(self) -> None:
        """Stops background rotating sync daemon gracefully."""
        self._stop_event.set()
        if self._background_thread:
            if self._background_thread.is_alive():
                self._background_thread.join(timeout=3.0)
            self._background_thread = None


# Singleton Accessor
_GLOBAL_BILLING_ENGINE: Optional[ModalBillingSyncEngine] = None
_GLOBAL_ENGINE_LOCK = threading.Lock()


def get_billing_sync_engine() -> ModalBillingSyncEngine:
    """Singleton accessor for ModalBillingSyncEngine."""
    global _GLOBAL_BILLING_ENGINE
    with _GLOBAL_ENGINE_LOCK:
        if _GLOBAL_BILLING_ENGINE is None:
            _GLOBAL_BILLING_ENGINE = ModalBillingSyncEngine()
    return _GLOBAL_BILLING_ENGINE


if __name__ == "__main__":
    force_run = "--force" in sys.argv
    single_profile = None
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            single_profile = arg
            break

    engine = get_billing_sync_engine()
    if single_profile:
        print(f"Syncing single workspace profile '{single_profile}'...")
        res = engine.sync_single_workspace(single_profile)
        print(json.dumps(res, indent=2))
    else:
        print(f"Syncing all Modal workspace profiles (force={force_run})...")
        res = engine.sync_all(force=force_run)
        print(json.dumps(res, indent=2))
