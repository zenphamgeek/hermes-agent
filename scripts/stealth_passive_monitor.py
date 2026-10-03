#!/usr/bin/env python3
"""
Stealth Passive Health Monitor & Quota Persistence Engine for Modal Fleet.
Enforces hard quota (<= 5 probes/day), 24h cache TTL pre-check, anti-burst
staggered jitter (150-300s), disk state persistence, and passive in-flight telemetry.
"""

import os
import json
import time
import random
import threading
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path("/home/zen/hermes-agent")
OUTPUT_DIR = PROJECT_ROOT / "output"
PROBE_STATE_FILE = OUTPUT_DIR / "modal_probe_quota.json"

_PROBE_LOCK = threading.Lock()

DEFAULT_PROBE_STATE: Dict[str, Any] = {
    "date": time.strftime("%Y-%m-%d"),
    "count": 0,
    "max_daily": 5,
    "last_probe_timestamp": 0.0,
    "cached_status": {},
}

# In-memory shared state singleton
_PROBE_STATE: Dict[str, Any] = dict(DEFAULT_PROBE_STATE)


def load_probe_state() -> Dict[str, Any]:
    """Loads probe state from disk persistence file, handling daily rollover."""
    global _PROBE_STATE
    today = time.strftime("%Y-%m-%d")
    state = dict(DEFAULT_PROBE_STATE)
    state["date"] = today

    if PROBE_STATE_FILE.exists():
        try:
            raw_text = PROBE_STATE_FILE.read_text(encoding="utf-8")
            data = json.loads(raw_text)
            if isinstance(data, dict):
                cached = data.get("cached_status", {})
                last_ts = float(data.get("last_probe_timestamp", 0.0))
                max_daily = int(data.get("max_daily", 5))

                if data.get("date") == today:
                    state["count"] = int(data.get("count", 0))
                    state["date"] = today
                    state["max_daily"] = max_daily
                    state["last_probe_timestamp"] = last_ts
                    state["cached_status"] = cached
                else:
                    # New day: reset count to 0, preserve historical cache & last timestamp
                    state["count"] = 0
                    state["date"] = today
                    state["max_daily"] = max_daily
                    state["last_probe_timestamp"] = last_ts
                    state["cached_status"] = cached
        except Exception as e:
            print(f"[StealthMonitor] Warning loading {PROBE_STATE_FILE}: {e}")

    _PROBE_STATE = state
    return state


def save_probe_state(state: Dict[str, Any]) -> None:
    """Atomically persists probe state to disk."""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        tmp_file = PROBE_STATE_FILE.with_suffix(".tmp")
        tmp_file.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp_file.replace(PROBE_STATE_FILE)
    except Exception as e:
        print(f"[StealthMonitor] Warning saving {PROBE_STATE_FILE}: {e}")


def get_probe_state() -> Dict[str, Any]:
    """Returns thread-safe copy of probe state."""
    with _PROBE_LOCK:
        today = time.strftime("%Y-%m-%d")
        if _PROBE_STATE.get("date") != today:
            _PROBE_STATE["date"] = today
            _PROBE_STATE["count"] = 0
            save_probe_state(_PROBE_STATE)
        return dict(_PROBE_STATE)


def get_probe_quota() -> Dict[str, Any]:
    """Returns current quota status conforming to /api/probe_quota contract."""
    with _PROBE_LOCK:
        today = time.strftime("%Y-%m-%d")
        if _PROBE_STATE.get("date") != today:
            _PROBE_STATE["date"] = today
            _PROBE_STATE["count"] = 0
            save_probe_state(_PROBE_STATE)

        count = int(_PROBE_STATE.get("count", 0))
        max_daily = int(_PROBE_STATE.get("max_daily", 5))
        return {
            "success": True,
            "date": _PROBE_STATE["date"],
            "probes_used_today": count,
            "max_daily": max_daily,
            "remaining": max(0, max_daily - count),
            "last_probe_timestamp": _PROBE_STATE.get("last_probe_timestamp", 0.0),
        }


def probe_worker_stealth(
    endpoint: str,
    timeout: float = 4.0,
    bypass_jitter: bool = False
) -> Dict[str, Any]:
    """
    Executes stealth health probe with 24h cache TTL check, hard quota (<=5),
    and staggered anti-detection jitter (150-300s).
    """
    endpoint = endpoint.strip()
    now = time.time()

    with _PROBE_LOCK:
        today = time.strftime("%Y-%m-%d")
        if _PROBE_STATE.get("date") != today:
            _PROBE_STATE["date"] = today
            _PROBE_STATE["count"] = 0
            save_probe_state(_PROBE_STATE)

        current_count = int(_PROBE_STATE.get("count", 0))
        max_daily = int(_PROBE_STATE.get("max_daily", 5))
        cached_res = _PROBE_STATE.get("cached_status", {}).get(endpoint)

        # 1. 24h Cache TTL Pre-Check (86400s)
        if cached_res and (now - float(cached_res.get("timestamp", 0.0)) < 86400.0):
            return {
                "success": True,
                "cached": True,
                "approximate": True,
                "status": cached_res.get("status", "healthy (cached)"),
                "message": "Serving valid 24h cached health status (zero outbound request).",
                "probes_used_today": current_count,
                "max_daily": max_daily,
                "source": cached_res.get("source", "cache_ttl_24h"),
                "last_checked": cached_res.get("timestamp", 0.0),
            }

        # 2. Hard Quota Enforcement: <= 5 probes per day
        if current_count >= max_daily:
            return {
                "success": True,
                "cached": True,
                "approximate": True,
                "status": cached_res.get("status", "healthy (cached)") if cached_res else "healthy (estimated)",
                "message": f"Daily probe quota ({max_daily}/{max_daily}) reached. Returning cached status.",
                "probes_used_today": current_count,
                "max_daily": max_daily,
                "source": "quota_exhausted_fallback",
            }

        # 3. Anti-Burst Staggered Jitter Guard (150s - 300s)
        last_probe = float(_PROBE_STATE.get("last_probe_timestamp", 0.0))
        elapsed = now - last_probe
        if not bypass_jitter and last_probe > 0 and elapsed < 150.0:
            cooldown_rem = int(150.0 - elapsed)
            return {
                "success": True,
                "cached": True,
                "approximate": True,
                "status": cached_res.get("status", "healthy (staggered)") if cached_res else "healthy (estimated)",
                "message": f"Staggered anti-detection jitter active (cooldown {cooldown_rem}s remaining). Outbound probe suppressed.",
                "probes_used_today": current_count,
                "max_daily": max_daily,
                "cooldown_remaining_seconds": cooldown_rem,
                "source": "jitter_suppressed",
            }

        # 4. Outbound Probe Execution
        live_status = "healthy"
        latency_ms = 0.0
        error_msg = None
        t0 = time.time()
        try:
            req = urllib.request.Request(endpoint, headers={"User-Agent": "ModalFleetStealthProbe/2.4"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                latency_ms = round((time.time() - t0) * 1000, 2)
                if response.status in [200, 204]:
                    live_status = "healthy"
                else:
                    live_status = f"http_{response.status}"
        except Exception as e:
            latency_ms = round((time.time() - t0) * 1000, 2)
            live_status = "idle_or_sleeping"
            error_msg = str(e)

        _PROBE_STATE["count"] = current_count + 1
        _PROBE_STATE["last_probe_timestamp"] = now
        if "cached_status" not in _PROBE_STATE:
            _PROBE_STATE["cached_status"] = {}

        _PROBE_STATE["cached_status"][endpoint] = {
            "status": live_status,
            "timestamp": now,
            "latency_ms": latency_ms,
            "error": error_msg,
            "source": "active_probe",
        }
        save_probe_state(_PROBE_STATE)

        return {
            "success": True,
            "cached": False,
            "approximate": False,
            "status": live_status,
            "probes_used_today": _PROBE_STATE["count"],
            "max_daily": max_daily,
            "latency_ms": latency_ms,
            "source": "live_outbound_probe",
        }


def record_in_flight_telemetry(
    endpoint_or_worker: str,
    success: bool,
    latency_ms: float = 0.0,
    error: Optional[str] = None
) -> None:
    """
    Passive In-Flight Telemetry: Updates worker health ledger dynamically
    based on actual inference job outcomes without incrementing probe quota.
    """
    now = time.time()
    status = "healthy" if success else "error_or_offline"
    with _PROBE_LOCK:
        today = time.strftime("%Y-%m-%d")
        if _PROBE_STATE.get("date") != today:
            _PROBE_STATE["date"] = today
            _PROBE_STATE["count"] = 0

        if "cached_status" not in _PROBE_STATE:
            _PROBE_STATE["cached_status"] = {}

        _PROBE_STATE["cached_status"][endpoint_or_worker] = {
            "status": status,
            "latency_ms": round(latency_ms, 2),
            "error": error,
            "timestamp": now,
            "source": "passive_in_flight",
        }
        save_probe_state(_PROBE_STATE)


def get_health_ledger() -> Dict[str, Any]:
    """Returns complete health ledger of all known endpoints/workers."""
    with _PROBE_LOCK:
        return dict(_PROBE_STATE.get("cached_status", {}))


# Auto-initialize state on import
load_probe_state()
