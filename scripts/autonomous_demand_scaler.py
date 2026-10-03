#!/usr/bin/env python3
"""
scripts/autonomous_demand_scaler.py
====================================
Autonomous Request Logger, Demand Analyzer & Capacity Auto-Scaler
for Modal Fleet Stealth Engine.

Core Principle: Log every request → Analyze demand patterns per template/service
→ Predict resource shortages → Auto-deploy workers to emptiest workspace.

Mathematical Formulation:
-------------------------
1. Request Stream Logger:
   Every request is logged atomically with:
   {timestamp, endpoint, template_id, service, hardware_tier, duration_sec,
    cost_usd, workspace, status, client_ip_hash}

2. Demand Velocity (per template/service):
   V_template(t) = |requests in [t-W, t]| / W  (requests/sec in sliding window W)
   Acceleration: A_template(t) = V_template(t) - V_template(t - W)

3. Hot Template Detection:
   Template is "hot" if:
     V_template > V_fleet_mean + 2σ   (demand spike above 2 standard deviations)
     OR A_template > 0 for 3+ consecutive windows (sustained acceleration)

4. Capacity Gap Analysis (per template's GPU tier):
   Active_Workers(tier) = count active workers matching tier
   Required_Concurrency = ceil(V_template * mean_duration_template)
   Capacity_Gap = Required_Concurrency - Active_Workers(tier)

5. Autonomous Actions (Self-Completing):
   If Capacity_Gap > 0 AND headroom_budget > min_threshold:
     → Select emptiest workspace matching tier
     → Generate `modal deploy` command for the template's app
     → Record action in autonomous_actions_log
     → Mark workspace as +1 active_workers
"""

import os
import json
import math
import time
import hashlib
import threading
import datetime
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

PROJECT_ROOT = Path("/home/zen/hermes-agent")
OUTPUT_DIR = PROJECT_ROOT / "output"
REQUEST_LOG_FILE = OUTPUT_DIR / "modal_request_stream.jsonl"
DEMAND_ANALYSIS_FILE = OUTPUT_DIR / "modal_demand_analysis.json"
AUTONOMOUS_ACTIONS_LOG = OUTPUT_DIR / "modal_autonomous_actions.jsonl"

# Configurable thresholds
SLIDING_WINDOW_SEC = 900.0       # 15-minute sliding window for velocity
HOT_TEMPLATE_SIGMA = 2.0        # Z-score threshold for "hot" detection
SUSTAINED_ACCEL_WINDOWS = 3     # Consecutive acceleration windows to trigger
MIN_WORKSPACE_HEADROOM = 5.0    # $5 minimum remaining budget to auto-deploy
HARD_CEILING_USD = 29.50        # Hard ceiling per workspace
MAX_AUTO_ACTIONS_PER_HOUR = 3   # Rate limit autonomous deploy actions
MAX_REQUEST_LOG_LINES = 10000   # Max lines in request stream log before rotation
ABS_HOT_VELOCITY = 5.0 / 60.0  # 5 req/min expressed as req/sec — absolute hot threshold


class RequestStreamLogger:
    """
    Append-only JSONL logger for every request hitting the fleet.
    Thread-safe, atomic appends, auto-rotation.
    """

    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or REQUEST_LOG_FILE
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._line_count = self._count_lines()

    def _count_lines(self) -> int:
        if not self.log_file.exists():
            return 0
        try:
            with open(self.log_file, "r") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def log_request(
        self,
        endpoint: str,
        service: str,
        template_id: str = "",
        hardware_tier: str = "CPU",
        duration_sec: float = 0.0,
        cost_usd: float = 0.0,
        workspace: str = "local",
        status: str = "success",
        client_ip: str = "",
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Log a single request to the JSONL stream."""
        now = time.time()
        # Hash client IP for privacy
        ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:8] if client_ip else "local"

        record = {
            "ts": now,
            "dt": datetime.datetime.utcfromtimestamp(now).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endpoint": endpoint,
            "service": service,
            "template_id": template_id or "",
            "hw": hardware_tier,
            "dur_s": round(duration_sec, 3),
            "cost": round(cost_usd, 6),
            "ws": workspace,
            "status": status,
            "ip": ip_hash,
        }
        if extra:
            record["extra"] = extra

        with self._lock:
            # Auto-rotate if too many lines
            if self._line_count >= MAX_REQUEST_LOG_LINES:
                self._rotate()

            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            self._line_count += 1

        return record

    def _rotate(self) -> None:
        """Rotate log: keep last 5000 lines, archive the rest."""
        try:
            with open(self.log_file, "r") as f:
                lines = f.readlines()
            keep = lines[-5000:]
            archive_path = self.log_file.with_suffix(f".{int(time.time())}.jsonl")
            with open(archive_path, "w") as f:
                f.writelines(lines[:-5000])
            with open(self.log_file, "w") as f:
                f.writelines(keep)
            self._line_count = len(keep)
        except Exception:
            pass

    def get_recent_records(self, window_sec: float = 3600.0) -> List[Dict[str, Any]]:
        """Read records from the last `window_sec` seconds."""
        cutoff = time.time() - window_sec
        records = []
        if not self.log_file.exists():
            return records
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                        if r.get("ts", 0) >= cutoff:
                            records.append(r)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        return records


class DemandAnalyzer:
    """
    Analyzes request stream to compute per-template/service demand velocity,
    detect hot templates (demand spikes), and forecast capacity gaps.
    """

    def __init__(self, logger: RequestStreamLogger, window_sec: float = SLIDING_WINDOW_SEC):
        self.logger = logger
        self.window_sec = window_sec
        self._lock = threading.Lock()
        # Historical velocity snapshots for acceleration detection
        self._velocity_history: Dict[str, List[Tuple[float, float]]] = defaultdict(list)  # key -> [(timestamp, velocity)]

    def analyze_demand(self) -> Dict[str, Any]:
        """
        Full demand analysis across all templates and services.
        Returns per-template velocity, hot template detection, and capacity gap report.
        """
        now = time.time()
        records = self.logger.get_recent_records(window_sec=self.window_sec * 4)  # 4x window for acceleration

        # Current window records
        current_cutoff = now - self.window_sec
        current_records = [r for r in records if r["ts"] >= current_cutoff]

        # Previous window records (for acceleration)
        prev_cutoff = now - 2 * self.window_sec
        prev_records = [r for r in records if prev_cutoff <= r["ts"] < current_cutoff]

        # Per-template velocity
        template_stats = self._compute_template_stats(current_records, self.window_sec)
        prev_template_stats = self._compute_template_stats(prev_records, self.window_sec)

        # Per-service velocity
        service_stats = self._compute_service_stats(current_records, self.window_sec)

        # Fleet-wide mean and std for hot detection
        velocities = [s["velocity"] for s in template_stats.values() if s["velocity"] > 0]
        fleet_mean_v = sum(velocities) / len(velocities) if velocities else 0.0

        # Use Bessel-corrected std dev for unbiased estimate (N-1 denominator)
        n_v = len(velocities)
        if n_v >= 2:
            fleet_std_v = math.sqrt(
                sum((v - fleet_mean_v) ** 2 for v in velocities) / (n_v - 1)
            )
        elif n_v == 1:
            fleet_std_v = velocities[0] * 0.1  # 10% of single value
        else:
            fleet_std_v = 0.001

        # Absolute velocity threshold: any template serving >5 req/min is considered hot
        # Dominance ratio: template consumes >60% of total fleet traffic
        total_fleet_velocity = sum(velocities) if velocities else 1.0

        # Hot template detection
        hot_templates = {}
        for tid, stats in template_stats.items():
            z_score = (stats["velocity"] - fleet_mean_v) / max(fleet_std_v, 0.001)
            prev_v = prev_template_stats.get(tid, {}).get("velocity", 0.0)
            acceleration = stats["velocity"] - prev_v

            # Update velocity history
            self._velocity_history[tid].append((now, stats["velocity"]))
            self._velocity_history[tid] = self._velocity_history[tid][-10:]

            # Sustained acceleration check
            recent_accels = []
            hist = self._velocity_history[tid]
            for i in range(1, len(hist)):
                recent_accels.append(hist[i][1] - hist[i-1][1])
            sustained_accel = sum(1 for a in recent_accels[-SUSTAINED_ACCEL_WINDOWS:] if a > 0) >= SUSTAINED_ACCEL_WINDOWS

            # Dominance ratio: template consuming >60% of total fleet traffic
            dominance_ratio = stats["velocity"] / max(total_fleet_velocity, 0.00001)
            is_dominant = dominance_ratio > 0.60

            # Multi-criteria hot detection:
            # (1) Z-score spike: statistically anomalous vs fleet mean
            # (2) Absolute threshold: any template >5 req/min is hot
            # (3) Dominance: template consuming majority of fleet capacity
            # (4) Sustained acceleration: consistently growing over time
            is_hot = (
                z_score > HOT_TEMPLATE_SIGMA or
                stats["velocity"] > ABS_HOT_VELOCITY or
                is_dominant or
                sustained_accel
            )

            stats["z_score"] = round(z_score, 2)
            stats["acceleration"] = round(acceleration, 6)
            stats["sustained_acceleration"] = sustained_accel
            stats["dominance_ratio"] = round(dominance_ratio, 3)
            stats["is_dominant"] = is_dominant
            stats["is_hot"] = is_hot

            if is_hot:
                hot_templates[tid] = stats

        # Capacity gap per hot template
        capacity_gaps = {}
        for tid, stats in hot_templates.items():
            required_concurrency = math.ceil(stats["velocity"] * stats["mean_duration"])
            required_concurrency = max(1, required_concurrency)
            capacity_gaps[tid] = {
                "template_id": tid,
                "required_concurrency": required_concurrency,
                "velocity_req_per_min": round(stats["velocity"] * 60, 2),
                "mean_duration_sec": round(stats["mean_duration"], 2),
                "dominant_hardware": stats["dominant_hw"],
                "z_score": stats["z_score"],
                "acceleration": stats["acceleration"],
                "total_cost_window": round(stats["total_cost"], 4),
            }

        analysis = {
            "timestamp": now,
            "dt": datetime.datetime.utcfromtimestamp(now).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "window_sec": self.window_sec,
            "total_requests_in_window": len(current_records),
            "fleet_velocity_req_per_min": round(fleet_mean_v * 60, 2),
            "fleet_velocity_std": round(fleet_std_v * 60, 4),
            "template_stats": template_stats,
            "service_stats": service_stats,
            "hot_templates": hot_templates,
            "capacity_gaps": capacity_gaps,
            "hot_template_count": len(hot_templates),
        }

        # Persist analysis
        try:
            DEMAND_ANALYSIS_FILE.write_text(
                json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception:
            pass

        return analysis

    def _compute_template_stats(self, records: List[Dict], window: float) -> Dict[str, Dict]:
        stats: Dict[str, Dict] = {}
        by_template: Dict[str, List[Dict]] = defaultdict(list)
        for r in records:
            tid = r.get("template_id") or r.get("service", "unknown")
            by_template[tid].append(r)

        for tid, recs in by_template.items():
            durations = [r.get("dur_s", 0) for r in recs]
            costs = [r.get("cost", 0) for r in recs]
            hw_counts: Dict[str, int] = defaultdict(int)
            for r in recs:
                hw_counts[r.get("hw", "CPU")] += 1

            dominant_hw = max(hw_counts, key=hw_counts.get) if hw_counts else "CPU"
            mean_dur = sum(durations) / len(durations) if durations else 1.0

            stats[tid] = {
                "count": len(recs),
                "velocity": len(recs) / max(window, 1.0),  # req/sec
                "mean_duration": mean_dur,
                "max_duration": max(durations) if durations else 0,
                "total_cost": sum(costs),
                "dominant_hw": dominant_hw,
                "workspaces_used": list(set(r.get("ws", "") for r in recs)),
            }
        return stats

    def _compute_service_stats(self, records: List[Dict], window: float) -> Dict[str, Dict]:
        by_service: Dict[str, List[Dict]] = defaultdict(list)
        for r in records:
            by_service[r.get("service", "unknown")].append(r)

        stats = {}
        for svc, recs in by_service.items():
            durations = [r.get("dur_s", 0) for r in recs]
            costs = [r.get("cost", 0) for r in recs]
            stats[svc] = {
                "count": len(recs),
                "velocity_per_min": round(len(recs) / max(window / 60, 1.0), 2),
                "total_gpu_sec": round(sum(durations), 1),
                "total_cost": round(sum(costs), 4),
                "mean_duration": round(sum(durations) / len(durations), 2) if durations else 0,
            }
        return stats


class AutonomousCapacityManager:
    """
    Autonomous self-healing capacity manager.
    When a template's demand exceeds available workers, this engine:
    1. Identifies the capacity gap
    2. Selects the emptiest workspace with sufficient budget
    3. Generates deploy actions (modal deploy command or hot-plug worker registration)
    4. Logs all autonomous decisions for audit trail
    """

    def __init__(self, analyzer: DemandAnalyzer, workspace_selector=None):
        self.analyzer = analyzer
        self.workspace_selector = workspace_selector
        self._lock = threading.Lock()
        self._actions_this_hour: List[float] = []  # timestamps of actions taken

    def evaluate_and_act(self, active_workers_by_tier: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """
        Run full autonomous cycle:
        1. Analyze demand
        2. Detect capacity gaps for hot templates
        3. Generate autonomous deploy actions
        4. Return report with actions taken
        """
        analysis = self.analyzer.analyze_demand()
        actions = []

        if not analysis["capacity_gaps"]:
            return {
                "analysis_summary": {
                    "total_requests": analysis["total_requests_in_window"],
                    "fleet_velocity": analysis["fleet_velocity_req_per_min"],
                    "hot_templates": 0,
                },
                "actions": [],
                "status": "nominal",
            }

        # Rate limit check
        now = time.time()
        with self._lock:
            self._actions_this_hour = [t for t in self._actions_this_hour if now - t < 3600]
            remaining_actions = MAX_AUTO_ACTIONS_PER_HOUR - len(self._actions_this_hour)

        for tid, gap in analysis["capacity_gaps"].items():
            if remaining_actions <= 0:
                actions.append({
                    "template_id": tid,
                    "action": "rate_limited",
                    "reason": f"Max {MAX_AUTO_ACTIONS_PER_HOUR} autonomous actions/hour reached",
                })
                continue

            required = gap["required_concurrency"]
            hw_tier = gap["dominant_hardware"]
            current_workers = (active_workers_by_tier or {}).get(hw_tier, 0)
            capacity_deficit = required - current_workers

            if capacity_deficit <= 0:
                actions.append({
                    "template_id": tid,
                    "action": "sufficient_capacity",
                    "required": required,
                    "available": current_workers,
                })
                continue

            # Select best workspace for deployment
            target_ws = None
            deploy_reason = ""
            if self.workspace_selector:
                ws, score = self.workspace_selector.select_emptiest_workspace(hw_tier)
                remaining_budget = float(ws.get("remaining_budget", ws.get("budget", 30.0) - ws.get("estimated_spent", 0.0)))
                if remaining_budget >= MIN_WORKSPACE_HEADROOM and remaining_budget < HARD_CEILING_USD:
                    target_ws = ws
                    deploy_reason = (
                        f"Hot template '{tid}' needs {capacity_deficit} more {hw_tier} workers. "
                        f"Deploying to '{ws['workspace']}' (headroom: ${remaining_budget:.2f}, score: {score})"
                    )
                else:
                    deploy_reason = f"No workspace with sufficient headroom (>=${MIN_WORKSPACE_HEADROOM}) for {hw_tier}"

            action_record = {
                "timestamp": now,
                "dt": datetime.datetime.utcfromtimestamp(now).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "template_id": tid,
                "action": "auto_deploy_recommended" if target_ws else "no_suitable_workspace",
                "capacity_deficit": capacity_deficit,
                "required_concurrency": required,
                "current_workers": current_workers,
                "hardware_tier": hw_tier,
                "target_workspace": target_ws["workspace"] if target_ws else None,
                "target_account": target_ws["account"] if target_ws else None,
                "reason": deploy_reason,
                "demand_velocity_per_min": gap["velocity_req_per_min"],
                "z_score": gap["z_score"],
                "deploy_command": self._generate_deploy_command(tid, hw_tier, target_ws) if target_ws else None,
                "hotplug_payload": self._generate_hotplug_payload(tid, hw_tier, target_ws) if target_ws else None,
            }

            if target_ws:
                # Record action and update workspace
                with self._lock:
                    self._actions_this_hour.append(now)
                    remaining_actions -= 1

                # Update workspace active workers
                if self.workspace_selector:
                    target_ws["active_workers"] = target_ws.get("active_workers", 0) + 1
                    self.workspace_selector.save_workspaces(self.workspace_selector.workspaces)

            actions.append(action_record)
            self._log_action(action_record)

        return {
            "analysis_summary": {
                "total_requests": analysis["total_requests_in_window"],
                "fleet_velocity": analysis["fleet_velocity_req_per_min"],
                "hot_templates": analysis["hot_template_count"],
                "hot_template_ids": list(analysis["hot_templates"].keys()),
            },
            "actions": actions,
            "status": "scaling" if any(a.get("action") == "auto_deploy_recommended" for a in actions) else "nominal",
            "actions_remaining_this_hour": remaining_actions,
        }

    def _generate_deploy_command(self, template_id: str, hw_tier: str, workspace: Dict) -> str:
        """Generate modal CLI deploy command for the identified capacity gap."""
        ws_name = workspace.get("workspace", "default")
        # Map template to known app names
        app_map = {
            "video_wan22": "hermes-wan-s2v",
            "video_ltx": "hermes-neural-ltxvideo",
            "image_dit": "hermes-qwen-img-21",
            "tts_vieneu": "vieneu-tts-worker",
            "llm_chat": "hermes-llm-chat",
        }
        # Try to match template to app
        app_name = None
        for key, name in app_map.items():
            if key in template_id.lower():
                app_name = name
                break
        app_name = app_name or f"hermes-{template_id.replace('_', '-')}"

        return f"MODAL_PROFILE={ws_name} modal deploy skills/creative/modal-{template_id}/modal_app.py"

    def _generate_hotplug_payload(self, template_id: str, hw_tier: str, workspace: Dict) -> Dict:
        """Generate hot-plug worker registration payload for the API."""
        ws_name = workspace.get("workspace", "default")
        return {
            "worker_id": f"auto-{template_id}-{ws_name}-{int(time.time())}",
            "workspace": ws_name,
            "gpu_tier": hw_tier,
            "endpoint_url": f"https://{ws_name}--hermes-{template_id.replace('_', '-')}-api.modal.run",
            "app_name": f"hermes-{template_id.replace('_', '-')}",
            "service_category": template_id.split("_")[0] if "_" in template_id else "auxiliary",
            "description": f"Auto-deployed {hw_tier} worker for hot template '{template_id}' on {ws_name}",
            "capabilities": ["auto_scaled"],
        }

    def _log_action(self, action: Dict) -> None:
        """Append autonomous action to JSONL audit log."""
        try:
            with open(AUTONOMOUS_ACTIONS_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(action, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def get_actions_log(self, last_n: int = 50) -> List[Dict]:
        """Read the last N autonomous actions from the log."""
        if not AUTONOMOUS_ACTIONS_LOG.exists():
            return []
        try:
            with open(AUTONOMOUS_ACTIONS_LOG, "r", encoding="utf-8") as f:
                lines = f.readlines()
            return [json.loads(line.strip()) for line in lines[-last_n:] if line.strip()]
        except Exception:
            return []


class AutonomousDemandEngine:
    """
    Top-level autonomous engine combining all 3 components.
    Designed to be instantiated once as a global singleton in modal_fleet_server.py.
    """

    def __init__(self, workspace_selector=None):
        self.logger = RequestStreamLogger()
        self.analyzer = DemandAnalyzer(self.logger)
        self.manager = AutonomousCapacityManager(self.analyzer, workspace_selector)

    def log_and_analyze(
        self,
        endpoint: str,
        service: str,
        template_id: str = "",
        hardware_tier: str = "CPU",
        duration_sec: float = 0.0,
        cost_usd: float = 0.0,
        workspace: str = "local",
        status: str = "success",
        client_ip: str = "",
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Single entry point: log the request, then run lightweight demand check.
        Full autonomous evaluation runs only every N requests to avoid overhead.
        """
        record = self.logger.log_request(
            endpoint=endpoint, service=service, template_id=template_id,
            hardware_tier=hardware_tier, duration_sec=duration_sec,
            cost_usd=cost_usd, workspace=workspace, status=status,
            client_ip=client_ip, extra=extra,
        )
        return record

    def run_autonomous_cycle(self, active_workers_by_tier: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """
        Full autonomous cycle: analyze → detect hot templates → generate deploy actions.
        Should be called periodically (e.g., every 5 minutes or after every 10 requests).
        """
        return self.manager.evaluate_and_act(active_workers_by_tier)

    def get_demand_report(self) -> Dict[str, Any]:
        """Get current demand analysis without triggering actions."""
        return self.analyzer.analyze_demand()

    def get_autonomous_actions_log(self, last_n: int = 50) -> List[Dict]:
        return self.manager.get_actions_log(last_n)


if __name__ == "__main__":
    engine = AutonomousDemandEngine()
    # Simulate requests
    for i in range(5):
        engine.log_and_analyze(
            endpoint="/v1/images/generations",
            service="image_dit",
            template_id="qwen_image_21_api",
            hardware_tier="T4",
            duration_sec=8.5,
            cost_usd=0.0014,
            workspace="mojopham",
        )
    for i in range(15):
        engine.log_and_analyze(
            endpoint="/api/agent/dispatch",
            service="video_wan22",
            template_id="wan22_s2v_talking_avatar_production",
            hardware_tier="A100-80GB",
            duration_sec=45.0,
            cost_usd=0.055,
            workspace="zenonmind",
        )
    result = engine.run_autonomous_cycle(active_workers_by_tier={"A100-80GB": 1, "T4": 2})
    print(json.dumps(result, indent=2))
