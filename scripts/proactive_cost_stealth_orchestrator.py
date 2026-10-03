#!/usr/bin/env python3
"""
scripts/proactive_cost_stealth_orchestrator.py
==============================================
Proactive Cost Engine, Adaptive Error Calibrator, 3-Hour Lookahead Forecaster,
and Autonomous Workspace Headroom Rebalancer for Modal Fleet Stealth Mode.

Mathematical Formulation:
-------------------------
1. In-Flight Micro-Cost:
   Request Cost = Execution Duration (s) * Modal Hardware Rate ($/s)
   Calibrated Cost = Request Cost * Dynamic Multiplier (kappa)

2. Proactive vs Real Usage:
   Proactive Usage(t) = Real Usage Baseline + Sum(Calibrated Cost)
   Drift (Delta) = Real Usage (Modal Sync) - Proactive Usage
   Adaptive Calibration Factor:
     kappa_{k+1} = kappa_k * (1.0 + alpha * (Real_Delta / Estimated_Delta - 1.0))

3. 3-Hour Lookahead Predictive Forecasting:
   D_3h = Integral_{t}^{t+3h} lambda(tau) * T_service dtau
   If Demand > Active Capacity OR Projected 3h Cost > Remaining Workspace Balance:
     Deficit Flag = True

4. Emptiest Workspace Selection:
   HeadroomScore(W_j) = w1 * Balance(W_j) - w2 * ActiveWorkers(W_j) - w3 * ProbesUsed(W_j)
   Target W* = argmax HeadroomScore(W_j)
"""

import os
import json
import time
import math
import uuid
import datetime
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

PROJECT_ROOT = Path("/home/zen/hermes-agent")
OUTPUT_DIR = PROJECT_ROOT / "output"
LEDGER_FILE = OUTPUT_DIR / "modal_proactive_cost_ledger.json"
WORKSPACE_REGISTRY_FILE = OUTPUT_DIR / "modal_workspace_headroom_status.json"

# Modal Official Pricing (USD per second)
# Based on Modal public pricing table:
# A100-80GB: $4.43/hr = $0.00123056/sec
# A10G: $1.10/hr = $0.00030556/sec
# L4: $0.80/hr = $0.00022222/sec
# T4: $0.59/hr = $0.00016389/sec
# CPU (per core): $0.048/hr = $0.00001333/sec
MODAL_RATES_PER_SEC: Dict[str, float] = {
    "A100-80GB": 4.43 / 3600.0,
    "A100": 4.43 / 3600.0,
    "A10G": 1.10 / 3600.0,
    "L4": 0.80 / 3600.0,
    "T4": 0.59 / 3600.0,
    "RTX-5000": 0.0,  # Local ThinkPad P15 GPU (Zero Cloud Cost)
    "CPU": 0.048 / 3600.0,
}

# 20 Sovereign Workspaces across 4 accounts
DEFAULT_WORKSPACES: List[Dict[str, Any]] = [
    # Nhóm 1: just.ask.mr.zen@gmail.com
    {"workspace": "just-ask-mr-zen", "account": "just.ask.mr.zen@gmail.com", "tier": "A100-80GB", "budget": 30.0, "active_workers": 0},
    {"workspace": "zenpeace", "account": "just.ask.mr.zen@gmail.com", "tier": "T4", "budget": 30.0, "active_workers": 0},
    {"workspace": "mindful", "account": "just.ask.mr.zen@gmail.com", "tier": "A100-80GB", "budget": 30.0, "active_workers": 1},
    {"workspace": "zenguru", "account": "just.ask.mr.zen@gmail.com", "tier": "T4", "budget": 30.0, "active_workers": 0},
    {"workspace": "zenmaster", "account": "just.ask.mr.zen@gmail.com", "tier": "A100-80GB", "budget": 30.0, "active_workers": 0},

    # Nhóm 2: nhatrophamvu@gmail.com
    {"workspace": "nhatrophamvu", "account": "nhatrophamvu@gmail.com", "tier": "T4", "budget": 30.0, "active_workers": 0},
    {"workspace": "asmr", "account": "nhatrophamvu@gmail.com", "tier": "T4", "budget": 30.0, "active_workers": 1},
    {"workspace": "vi2vi", "account": "nhatrophamvu@gmail.com", "tier": "T4", "budget": 30.0, "active_workers": 1},
    {"workspace": "pvvsf", "account": "nhatrophamvu@gmail.com", "tier": "T4", "budget": 30.0, "active_workers": 0},
    {"workspace": "phi4", "account": "nhatrophamvu@gmail.com", "tier": "L4", "budget": 30.0, "active_workers": 0},

    # Nhóm 3: mojopham@gmail.com
    {"workspace": "mojopham", "account": "mojopham@gmail.com", "tier": "A100-80GB", "budget": 30.0, "active_workers": 1},
    {"workspace": "diatts", "account": "mojopham@gmail.com", "tier": "T4", "budget": 30.0, "active_workers": 1},
    {"workspace": "mvlm", "account": "mojopham@gmail.com", "tier": "A100-80GB", "budget": 30.0, "active_workers": 1},
    {"workspace": "vrag", "account": "mojopham@gmail.com", "tier": "T4", "budget": 30.0, "active_workers": 1},

    # Nhóm 4: zenonmind@gmail.com
    {"workspace": "lovenovel", "account": "zenonmind@gmail.com", "tier": "A100-80GB", "budget": 30.0, "active_workers": 0},
    {"workspace": "vieturbo", "account": "zenonmind@gmail.com", "tier": "T4", "budget": 30.0, "active_workers": 0},
    {"workspace": "zenonmind", "account": "zenonmind@gmail.com", "tier": "A100-80GB", "budget": 30.0, "active_workers": 0},
    {"workspace": "insimind", "account": "zenonmind@gmail.com", "tier": "L4", "budget": 30.0, "active_workers": 0},
    {"workspace": "zenonts", "account": "zenonmind@gmail.com", "tier": "T4", "budget": 30.0, "active_workers": 1},
]


class ProactiveCostLedger:
    """Maintains proactive in-flight cost state with atomic disk persistence and thread safety."""

    def __init__(self, ledger_file: Optional[Path] = None):
        self.ledger_file = ledger_file or LEDGER_FILE
        self.lock = threading.Lock()
        self._lock = self.lock
        with self.lock:
            self.state: Dict[str, Any] = self._load()

    def _default_state(self) -> Dict[str, Any]:
        return {
            "date": datetime.date.today().isoformat(),
            "real_usage_baseline": 0.0,
            "last_real_sync_timestamp": 0.0,
            "real_syncs_today": 0,
            "max_daily_real_syncs": 2,  # Strict Stealth Rule: max 1-2 real checks/day
            "calibration_multiplier_kappa": 1.08,  # Default 8% warmup/idle buffer
            "historical_drifts": [],
            "in_flight_accumulated_cost": 0.0,
            "request_records": [],
            "service_telemetry": {
                "video_wan22": {"count": 0, "total_seconds": 0.0, "total_cost": 0.0},
                "video_ltx": {"count": 0, "total_seconds": 0.0, "total_cost": 0.0},
                "image_dit": {"count": 0, "total_seconds": 0.0, "total_cost": 0.0},
                "tts_vieneu": {"count": 0, "total_seconds": 0.0, "total_cost": 0.0},
                "llm_chat": {"count": 0, "total_seconds": 0.0, "total_cost": 0.0},
            }
        }

    def _load(self) -> Dict[str, Any]:
        if self.ledger_file.exists():
            try:
                data = json.loads(self.ledger_file.read_text(encoding="utf-8"))
                today = datetime.date.today().isoformat()
                if data.get("date") != today:
                    # New day rollover: preserve calibration & baseline, reset daily counters
                    data["date"] = today
                    data["real_syncs_today"] = 0
                return data
            except Exception:
                pass
        state = self._default_state()
        self._save(state)
        return state

    def _save(self, state: Optional[Dict[str, Any]] = None) -> None:
        if state is None:
            state = self.state
        self.ledger_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.ledger_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.ledger_file)

    def save(self, state: Optional[Dict[str, Any]] = None) -> None:
        """Thread-safe public save method."""
        with self.lock:
            self._save(state)

    def record_request_cost(
        self,
        service: str,
        hardware_tier: str,
        duration_sec: float,
        workspace: str = "default",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculates and records in-flight request cost: Time Cost * Price of Modal."""
        req_id = request_id or str(uuid.uuid4())[:8]
        rate = MODAL_RATES_PER_SEC.get(hardware_tier, MODAL_RATES_PER_SEC["CPU"])
        nominal_cost = duration_sec * rate

        with self.lock:
            kappa = float(self.state.get("calibration_multiplier_kappa", 1.08))
            calibrated_cost = nominal_cost * kappa

            self.state["in_flight_accumulated_cost"] += calibrated_cost

            # Update service telemetry
            svc_entry = self.state["service_telemetry"].setdefault(
                service, {"count": 0, "total_seconds": 0.0, "total_cost": 0.0}
            )
            svc_entry["count"] += 1
            svc_entry["total_seconds"] += duration_sec
            svc_entry["total_cost"] += calibrated_cost

            record = {
                "request_id": req_id,
                "timestamp": time.time(),
                "service": service,
                "hardware_tier": hardware_tier,
                "duration_sec": round(duration_sec, 3),
                "nominal_cost": round(nominal_cost, 6),
                "calibrated_cost": round(calibrated_cost, 6),
                "workspace": workspace,
            }
            self.state["request_records"].append(record)
            # Keep sliding log of last 500 records
            if len(self.state["request_records"]) > 500:
                self.state["request_records"] = self.state["request_records"][-500:]

            self._save()
        return record

    def get_proactive_usage(self) -> float:
        """Returns Proactive Usage = Real Usage Baseline + In-Flight Accumulated Cost."""
        with self.lock:
            baseline = float(self.state.get("real_usage_baseline", 0.0))
            in_flight = float(self.state.get("in_flight_accumulated_cost", 0.0))
            return round(baseline + in_flight, 5)

    def calibrate_with_real_usage(self, modal_real_usage: float) -> Dict[str, Any]:
        """
        Synchronizes with real Modal usage (1-2 times daily).
        Calculates drift: Drift = Real Usage - Proactive Usage.
        If large discrepancy is detected, adaptively recalibrates kappa.
        """
        with self.lock:
            baseline = float(self.state.get("real_usage_baseline", 0.0))
            in_flight = float(self.state.get("in_flight_accumulated_cost", 0.0))
            proactive_est = round(baseline + in_flight, 5)
            drift = modal_real_usage - proactive_est
            old_kappa = float(self.state.get("calibration_multiplier_kappa", 1.08))

            # Check if we had non-zero in-flight activity to calibrate
            new_kappa = old_kappa
            adjustment_made = False

            if in_flight > 0.001:
                ratio = (modal_real_usage - baseline) / in_flight
                # Bound ratio between 0.8x and 2.5x to prevent extreme runaway spikes
                ratio_bounded = max(0.8, min(2.5, ratio))
                # Exponential smoothing update: alpha = 0.5
                alpha = 0.5
                new_kappa = round(old_kappa * (1.0 - alpha) + (old_kappa * ratio_bounded) * alpha, 4)
                adjustment_made = True

            self.state["calibration_multiplier_kappa"] = new_kappa
            self.state["real_usage_baseline"] = modal_real_usage
            self.state["in_flight_accumulated_cost"] = 0.0
            self.state["last_real_sync_timestamp"] = time.time()
            self.state["real_syncs_today"] += 1

            drift_record = {
                "timestamp": time.time(),
                "modal_real_usage": modal_real_usage,
                "proactive_est_before_sync": proactive_est,
                "drift_amount": round(drift, 5),
                "old_kappa": old_kappa,
                "new_kappa": new_kappa,
                "adjusted": adjustment_made,
            }
            self.state["historical_drifts"].append(drift_record)
            self._save()
        return drift_record


class Predictive3HForecaster:
    """
    Applies statistical forecasting (Poisson arrival rate + mean duration)
    to predict fleet demand and cost over the upcoming 3-hour lookahead window.
    """

    def __init__(self, ledger: ProactiveCostLedger):
        self.ledger = ledger

    def predict_3h_demand(self) -> Dict[str, Any]:
        """
        Calculates expected demand in the next 3 hours (10800s).
        Returns projected requests, GPU hours, and projected dollar cost.
        """
        records = self.ledger.state.get("request_records", [])
        now = time.time()
        # Look back 2 hours (7200s) to calculate current arrival rate
        window_sec = 7200.0
        recent = [r for r in records if now - r["timestamp"] <= window_sec]

        # Calculate arrival rate lambda (requests/sec)
        effective_window = max(60.0, min(window_sec, (now - records[0]["timestamp"])) if records else window_sec)
        lambda_overall = len(recent) / effective_window if recent else 0.02  # Default 0.02 req/s (~72 req/hr)

        # Baseline per-service distributions
        service_counts: Dict[str, int] = {}
        service_durations: Dict[str, List[float]] = {}
        for r in recent:
            svc = r["service"]
            service_counts[svc] = service_counts.get(svc, 0) + 1
            service_durations.setdefault(svc, []).append(r["duration_sec"])

        lookahead_sec = 3 * 3600.0  # 3 hours
        expected_total_requests = max(5, int(math.ceil(lambda_overall * lookahead_sec)))

        # Average duration fallback
        avg_durations = {
            "video_wan22": 45.0,
            "video_ltx": 30.0,
            "image_dit": 8.0,
            "tts_vieneu": 5.0,
            "llm_chat": 2.0,
        }

        projected_service_requests: Dict[str, int] = {}
        projected_3h_cost = 0.0
        projected_gpu_seconds = 0.0

        for svc, default_dur in avg_durations.items():
            durations = service_durations.get(svc, [default_dur])
            mean_dur = sum(durations) / len(durations)
            weight = service_counts.get(svc, 1) / max(1, len(recent)) if recent else 0.2
            svc_reqs = max(1, int(round(expected_total_requests * weight)))
            projected_service_requests[svc] = svc_reqs

            # Hardware tier mapping
            tier = "A100-80GB" if "wan22" in svc or "image" in svc else ("T4" if "video" in svc else "RTX-5000")
            rate = MODAL_RATES_PER_SEC.get(tier, MODAL_RATES_PER_SEC["CPU"])
            svc_cost = svc_reqs * mean_dur * rate * self.ledger.state.get("calibration_multiplier_kappa", 1.08)
            projected_3h_cost += svc_cost
            if tier != "RTX-5000":
                projected_gpu_seconds += svc_reqs * mean_dur

        projected_concurrency_needed = math.ceil(projected_gpu_seconds / lookahead_sec)

        return {
            "window_hours": 3.0,
            "projected_total_requests": expected_total_requests,
            "projected_service_requests": projected_service_requests,
            "projected_gpu_seconds": round(projected_gpu_seconds, 1),
            "projected_concurrency_needed": max(1, projected_concurrency_needed),
            "projected_3h_cost_usd": round(projected_3h_cost, 4),
            "lambda_requests_per_sec": round(lambda_overall, 4),
        }


class WorkspaceHeadroomSelector:
    """
    Evaluates 20 Modal Workspaces and selects the optimal workspace
    ('trống nhiều nhất') for proactive worker deployment.
    """

    def __init__(self, registry_file: Optional[Path] = None):
        self.registry_file = registry_file or WORKSPACE_REGISTRY_FILE
        self.workspaces = self._load_workspaces()
        self.get_enriched_workspaces()

    def get_enriched_workspaces(self, reload_from_disk: bool = False) -> List[Dict[str, Any]]:
        """
        Returns all 20 canonical workspaces with their full tokenomics attributes:
        workspace, account, tier, budget, estimated_spent, remaining_budget,
        active_workers, headroom_score, hard_ceiling (29.50), hard_ceiling_breached, status.
        """
        if reload_from_disk and self.registry_file.exists():
            try:
                self.workspaces = json.loads(self.registry_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        enriched = []
        for ws in self.workspaces:
            budget = float(ws.get("budget", 30.0))
            spent = float(ws.get("estimated_spent", 0.0))
            rem_budget = round(max(0.0, budget - spent), 4)
            active_workers = int(ws.get("active_workers", 0))
            probes = int(ws.get("probes_today", 0))
            hard_ceiling = 29.50
            breached = bool(spent >= hard_ceiling)

            score = round((1.0 * rem_budget) - (15.0 * active_workers) - (5.0 * probes), 2)

            if breached:
                status = "critical"
            elif spent >= 25.0:
                status = "warning"
            else:
                status = ws.get("status", "healthy")

            entry = {
                "workspace": ws.get("workspace"),
                "account": ws.get("account"),
                "tier": ws.get("tier", "T4"),
                "budget": budget,
                "estimated_spent": round(spent, 4),
                "remaining_budget": rem_budget,
                "active_workers": active_workers,
                "headroom_score": score,
                "hard_ceiling": hard_ceiling,
                "hard_ceiling_breached": breached,
                "status": status,
            }
            ws.update(entry)
            enriched.append(entry)

        return enriched

    def _load_workspaces(self) -> List[Dict[str, Any]]:
        if self.registry_file.exists():
            try:
                return json.loads(self.registry_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        data = list(DEFAULT_WORKSPACES)
        self.save_workspaces(data)
        return data

    def save_workspaces(self, workspaces: List[Dict[str, Any]]) -> None:
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.registry_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(workspaces, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.registry_file)

    def select_emptiest_workspace(self, target_tier: str = "A100-80GB") -> Tuple[Dict[str, Any], float]:
        """
        Computes composite Headroom Score:
        Score = 1.0 * Remaining_Budget - 15.0 * Active_Workers - 5.0 * Probe_Count
        Returns (best_workspace, score).
        """
        candidates = [w for w in self.workspaces if w.get("tier") == target_tier or target_tier == "ANY"]
        if not candidates:
            candidates = self.workspaces

        best_score = -float("inf")
        best_ws = candidates[0]

        for ws in candidates:
            budget = float(ws.get("budget", 30.0))
            active_workers = int(ws.get("active_workers", 0))
            probes = int(ws.get("probes_today", 0))
            spent = float(ws.get("estimated_spent", 0.0))
            rem_budget = max(0.0, budget - spent)

            # High remaining budget + low active workers = high headroom score
            score = (1.0 * rem_budget) - (15.0 * active_workers) - (5.0 * probes)

            if score > best_score:
                best_score = score
                best_ws = ws

        return best_ws, round(best_score, 2)


class StealthProactiveOrchestrator:
    """
    Unified Orchestrator:
    - In-flight request cost tracking
    - Daily low-frequency calibration (max 1-2 times)
    - 3-hour capacity forecast
    - Automatic deployment to emptiest workspace when deficit is projected
    """

    def __init__(self):
        self.ledger = ProactiveCostLedger()
        self.forecaster = Predictive3HForecaster(self.ledger)
        self.selector = WorkspaceHeadroomSelector()

    def process_request(self, service: str, hardware_tier: str, duration_sec: float, workspace: str = "default") -> Dict[str, Any]:
        """Record request and check 3h capacity health."""
        cost_record = self.ledger.record_request_cost(service, hardware_tier, duration_sec, workspace)
        forecast = self.forecaster.predict_3h_demand()

        # Check deficit condition
        # If current active capacity across fleet < projected concurrency needed
        current_active_workers = sum(w.get("active_workers", 0) for w in self.selector.workspaces)
        deficit = current_active_workers < forecast["projected_concurrency_needed"]

        action_taken = None
        target_ws = None
        if deficit:
            target_ws, score = self.selector.select_emptiest_workspace(hardware_tier)
            # Auto-scale: assign +1 worker to emptiest workspace
            target_ws["active_workers"] = target_ws.get("active_workers", 0) + 1
            self.selector.save_workspaces(self.selector.workspaces)
            action_taken = f"Auto-deployed standby worker to emptiest workspace '{target_ws['workspace']}' (Headroom Score: {score})"

        return {
            "cost_record": cost_record,
            "proactive_usage_total": self.ledger.get_proactive_usage(),
            "3h_forecast": forecast,
            "deficit_detected": deficit,
            "action_taken": action_taken,
            "allocated_workspace": target_ws["workspace"] if target_ws else workspace,
        }

    def sync_daily_real_usage(self, modal_real_usage: float) -> Dict[str, Any]:
        """Performs scheduled low-frequency real usage check."""
        sync_result = self.ledger.calibrate_with_real_usage(modal_real_usage)
        return sync_result


if __name__ == "__main__":
    orchestrator = StealthProactiveOrchestrator()
    print("[ProactiveCostEngine] Initialized. Current Proactive Usage:", orchestrator.ledger.get_proactive_usage())
    res = orchestrator.process_request(service="video_wan22", hardware_tier="A100-80GB", duration_sec=42.5)
    print("[ProactiveCostEngine] Sample Request Result:", json.dumps(res, indent=2))
