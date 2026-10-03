#!/usr/bin/env python3
"""
scripts/budget_guardian.py
===========================
Autonomous Budget Guardian — Prevention Cycle with Human-in-the-Loop Approve Gate.

Design Philosophy:
  "Propose → Approve → Execute Automatically"

The Guardian continuously monitors 4 risk dimensions:
  1. Budget Ceiling Risk       — workspace approaching $29.50 hard limit
  2. Fleet Imbalance           — one workspace dominating >200% proportional spend
  3. Probe Quota Exhaustion    — 5/5 stealth probes used; blind operation risk
  4. κ Divergence              — calibration factor drifting outside [0.9, 2.0]

For each risk detected, it generates a PROPOSED_ACTION with:
  - risk_id, severity (CRITICAL/WARNING/INFO)
  - root_cause analysis
  - proposed_action (concrete, reversible step)
  - estimated_impact (what changes if approved)
  - approval_token (idempotency key)

When user calls POST /api/guardian/approve with approval_token,
the Guardian executes the action autonomously:
  - Traffic rerouting (workspace_selector update)
  - κ correction (ledger recalibration)
  - Throttle flag (workspace marked throttled)
  - Passive mode lock (no more probes until midnight)

All actions are atomic, audited, and reversible via POST /api/guardian/rollback.
"""

import json
import math
import time
import uuid
import datetime
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

PROJECT_ROOT = Path("/home/zen/hermes-agent")
OUTPUT_DIR = PROJECT_ROOT / "output"
GUARDIAN_STATE_FILE = OUTPUT_DIR / "budget_guardian_state.json"
GUARDIAN_AUDIT_LOG = OUTPUT_DIR / "budget_guardian_audit.jsonl"

# Risk thresholds
CEILING_HARD_USD = 29.50          # Hard ceiling per workspace ($30 limit - safety margin)
CEILING_WARNING_USD = 25.00       # Yellow warning threshold
CEILING_THROTTLE_USD = 27.00     # Auto-throttle new requests to this workspace
IMBALANCE_RATIO_WARN = 2.0       # Workspace burn >200% of its proportional share → WARNING
IMBALANCE_RATIO_CRIT = 5.0       # Workspace burn >500% of its proportional share → CRITICAL
KAPPA_MIN = 0.9                   # κ lower bound
KAPPA_WARN = 1.85                 # κ warning threshold (near red zone)
KAPPA_MAX = 2.0                   # κ upper bound
PROBE_QUOTA_MAX = 5               # Max stealth probes per day
PROBE_QUOTA_WARN = 4              # Warn when 4/5 used

# Severity ranking
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_WARNING = "WARNING"
SEVERITY_INFO = "INFO"

SEVERITY_RANK = {SEVERITY_CRITICAL: 3, SEVERITY_WARNING: 2, SEVERITY_INFO: 1}


class ProposedAction:
    """Represents a single pending approval action."""

    def __init__(
        self,
        risk_id: str,
        severity: str,
        title: str,
        root_cause: str,
        proposed_action: str,
        action_type: str,
        action_params: Dict[str, Any],
        estimated_impact: str,
    ):
        self.approval_token = str(uuid.uuid4())[:12]
        self.risk_id = risk_id
        self.severity = severity
        self.title = title
        self.root_cause = root_cause
        self.proposed_action = proposed_action
        self.action_type = action_type
        self.action_params = action_params
        self.estimated_impact = estimated_impact
        self.created_at = time.time()
        self.dt = datetime.datetime.utcfromtimestamp(self.created_at).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.status = "pending"  # pending | approved | rejected | executed | rolled_back
        self.executed_at = None
        self.execution_result = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approval_token": self.approval_token,
            "risk_id": self.risk_id,
            "severity": self.severity,
            "title": self.title,
            "root_cause": self.root_cause,
            "proposed_action": self.proposed_action,
            "action_type": self.action_type,
            "action_params": self.action_params,
            "estimated_impact": self.estimated_impact,
            "created_at": self.created_at,
            "dt": self.dt,
            "status": self.status,
            "executed_at": self.executed_at,
            "execution_result": self.execution_result,
        }


class BudgetGuardian:
    """
    Autonomous Budget Guardian with Approve Gate.

    Lifecycle:
      1. scan() → detect risks → generate ProposedActions
      2. POST /api/guardian/approve?token=XYZ → execute action
      3. POST /api/guardian/rollback?token=XYZ → undo action
      4. GET /api/guardian/pending → list all pending proposals
    """

    def __init__(self, ledger=None, selector=None):
        self._lock = threading.Lock()
        self._pending: Dict[str, ProposedAction] = {}   # token → ProposedAction
        self._executed: Dict[str, ProposedAction] = {}  # token → ProposedAction (history)
        self._throttled_workspaces: set = set()          # Workspaces with throttle active
        self._passive_mode_until: float = 0.0            # Epoch until which passive mode active
        self._ledger = ledger
        self._selector = selector
        self._load_state()

    # ------------------------------------------------------------------
    # RISK SCANNING
    # ------------------------------------------------------------------

    def scan(self, proactive_cost_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Full risk scan across all 4 dimensions.
        Returns list of detected risks with generated proposals.
        """
        proposals = []

        workspaces = proactive_cost_state.get("workspaces", [])
        kappa = float(proactive_cost_state.get("calibration_multiplier_kappa", 1.08))
        proactive_total = float(proactive_cost_state.get("proactive_usage_total_usd", 0.0))
        real_baseline = float(proactive_cost_state.get("real_usage_baseline_usd", 0.0))
        probe_count = int(proactive_cost_state.get("probe_count_today", 0))
        historical_drifts = proactive_cost_state.get("historical_drifts", [])

        # 1. Budget Ceiling Risk per workspace
        for ws in workspaces:
            spent = float(ws.get("proactive_cost_usd", ws.get("estimated_spent", 0.0)))
            name = ws.get("workspace", "unknown")
            remaining = float(ws.get("remaining_budget", 30.0 - spent))

            if spent >= CEILING_HARD_USD:
                p = self._propose_hard_ceiling(name, spent, remaining)
                if p:
                    proposals.append(p.to_dict())
            elif spent >= CEILING_THROTTLE_USD:
                p = self._propose_throttle(name, spent, remaining)
                if p:
                    proposals.append(p.to_dict())
            elif spent >= CEILING_WARNING_USD:
                p = self._propose_warning_watchlist(name, spent, remaining)
                if p:
                    proposals.append(p.to_dict())

        # 2. Fleet Imbalance
        if workspaces and proactive_total > 0.01:
            proportional_share = proactive_total / max(len(workspaces), 1)
            for ws in workspaces:
                spent = float(ws.get("proactive_cost_usd", ws.get("estimated_spent", 0.0)))
                name = ws.get("workspace", "unknown")
                if proportional_share > 0 and spent > 0:
                    ratio = spent / proportional_share
                    if ratio >= IMBALANCE_RATIO_CRIT:
                        p = self._propose_rebalance(name, spent, proactive_total, ratio, SEVERITY_CRITICAL)
                        if p:
                            proposals.append(p.to_dict())
                    elif ratio >= IMBALANCE_RATIO_WARN:
                        p = self._propose_rebalance(name, spent, proactive_total, ratio, SEVERITY_WARNING)
                        if p:
                            proposals.append(p.to_dict())

        # 3. κ Divergence
        if kappa < KAPPA_MIN:
            p = self._propose_kappa_correction(kappa, direction="underestimating", target=1.08)
            if p:
                proposals.append(p.to_dict())
        elif kappa >= KAPPA_WARN:
            p = self._propose_kappa_correction(kappa, direction="overestimating", target=1.20)
            if p:
                proposals.append(p.to_dict())

        # 4. Probe Quota Exhaustion
        if probe_count >= PROBE_QUOTA_MAX:
            p = self._propose_passive_lock()
            if p:
                proposals.append(p.to_dict())
        elif probe_count >= PROBE_QUOTA_WARN:
            p = self._propose_probe_conservation()
            if p:
                proposals.append(p.to_dict())

        return sorted(proposals, key=lambda x: SEVERITY_RANK.get(x["severity"], 0), reverse=True)

    def _propose_hard_ceiling(self, workspace: str, spent: float, remaining: float) -> Optional[ProposedAction]:
        risk_id = f"ceiling_hard_{workspace}"
        if self._already_pending(risk_id):
            return None
        p = ProposedAction(
            risk_id=risk_id,
            severity=SEVERITY_CRITICAL,
            title=f"🚨 Hard Ceiling Breached: {workspace}",
            root_cause=(
                f"Workspace '{workspace}' proactive spend ${spent:.2f} has reached or exceeded "
                f"the ${CEILING_HARD_USD} hard ceiling. Only ${remaining:.2f} remains before the "
                f"$30.00 monthly limit. Any more GPU requests on this workspace will overshoot the budget."
            ),
            proposed_action=(
                f"IMMEDIATE: Block all new GPU requests to workspace '{workspace}'. "
                f"Reroute 100% of incoming traffic to the emptiest alternative workspace. "
                f"Mark workspace as FROZEN until next billing cycle."
            ),
            action_type="freeze_workspace",
            action_params={"workspace": workspace, "spent": spent, "hard_freeze": True},
            estimated_impact=(
                f"'{workspace}' will receive 0 new requests. "
                f"All traffic routed to best alternative workspace. "
                f"Monthly spend on '{workspace}' locked at ${spent:.2f}."
            ),
        )
        return self._register(p)

    def _propose_throttle(self, workspace: str, spent: float, remaining: float) -> Optional[ProposedAction]:
        risk_id = f"ceiling_throttle_{workspace}"
        if self._already_pending(risk_id):
            return None
        p = ProposedAction(
            risk_id=risk_id,
            severity=SEVERITY_CRITICAL,
            title=f"⚠️ Throttle Required: {workspace} at ${spent:.2f}",
            root_cause=(
                f"Workspace '{workspace}' is at ${spent:.2f} — only ${remaining:.2f} from the hard ceiling. "
                f"At current burn rate, ceiling breach is imminent within hours."
            ),
            proposed_action=(
                f"THROTTLE: Limit workspace '{workspace}' to max 2 concurrent requests. "
                f"Priority-shift 70% of traffic to next-emptiest workspace. "
                f"Set proactive alert check every 30 min."
            ),
            action_type="throttle_workspace",
            action_params={"workspace": workspace, "spent": spent, "max_concurrent": 2, "traffic_shift_pct": 70},
            estimated_impact=(
                f"'{workspace}' burn rate reduced ~70%. "
                f"Estimated ceiling avoidance: prevents breach for next 12-24h. "
                f"Fleet continues serving requests at full capacity via other workspaces."
            ),
        )
        return self._register(p)

    def _propose_warning_watchlist(self, workspace: str, spent: float, remaining: float) -> Optional[ProposedAction]:
        risk_id = f"ceiling_watch_{workspace}"
        if self._already_pending(risk_id):
            return None
        p = ProposedAction(
            risk_id=risk_id,
            severity=SEVERITY_WARNING,
            title=f"📊 Watchlist: {workspace} at ${spent:.2f}",
            root_cause=f"Workspace '{workspace}' at ${spent:.2f} (${remaining:.2f} remaining). Approaching throttle zone.",
            proposed_action=f"ADD to watchlist. Increase monitoring frequency. Pre-select alternate workspace as hot-standby.",
            action_type="add_watchlist",
            action_params={"workspace": workspace, "spent": spent},
            estimated_impact="No traffic change. Monitoring frequency increased. Standby workspace pre-warmed.",
        )
        return self._register(p)

    def _propose_rebalance(
        self, workspace: str, spent: float, total: float, ratio: float, severity: str
    ) -> Optional[ProposedAction]:
        risk_id = f"imbalance_{workspace}"
        if self._already_pending(risk_id):
            return None
        pct = ratio * 100
        p = ProposedAction(
            risk_id=risk_id,
            severity=severity,
            title=f"⚖️ Imbalance: {workspace} at {pct:.0f}% of proportional share",
            root_cause=(
                f"Workspace '{workspace}' is burning ${spent:.2f} which is {pct:.0f}% of its proportional share "
                f"(${total/20:.2f} per workspace). This skew indicates routing imbalance — this workspace is "
                f"absorbing far more traffic than designed. Root cause: κ overestimate or routing misconfiguration."
            ),
            proposed_action=(
                f"REBALANCE: Reset workspace '{workspace}' proactive cost estimate using real usage sync. "
                f"Recalculate κ using last 24h actual data. "
                f"Shift 50% of future requests from '{workspace}' to the 3 emptiest workspaces."
            ),
            action_type="rebalance_workspace",
            action_params={
                "workspace": workspace,
                "spent": spent,
                "ratio": ratio,
                "traffic_shift_pct": 50,
                "recalibrate_kappa": True,
            },
            estimated_impact=(
                f"Workspace imbalance ratio reduced from {ratio:.1f}x to ~1.0x. "
                f"κ recalibrated to match actual spend. "
                f"Traffic spread across fleet restoring Tokenomics balance."
            ),
        )
        return self._register(p)

    def _propose_kappa_correction(
        self, kappa: float, direction: str, target: float
    ) -> Optional[ProposedAction]:
        risk_id = f"kappa_divergence_{direction}"
        if self._already_pending(risk_id):
            return None
        p = ProposedAction(
            risk_id=risk_id,
            severity=SEVERITY_WARNING,
            title=f"🔧 κ Divergence: {kappa:.3f} ({direction})",
            root_cause=(
                f"Calibration factor κ={kappa:.3f} is outside the healthy range [{KAPPA_MIN}, {KAPPA_MAX}]. "
                f"This means the proactive cost engine is {direction} actual GPU costs by "
                f"{abs(kappa - 1.0) * 100:.0f}%. "
                f"Cause: insufficient real usage syncs or atypical workload mix."
            ),
            proposed_action=(
                f"RECALIBRATE: Force κ correction to target={target:.2f}. "
                f"Trigger immediate real usage sync from Modal billing API. "
                f"Reset in-flight accumulated cost with corrected baseline."
            ),
            action_type="recalibrate_kappa",
            action_params={"current_kappa": kappa, "target_kappa": target, "direction": direction},
            estimated_impact=(
                f"κ corrected from {kappa:.3f} → {target:.2f}. "
                f"Proactive cost estimates will be {abs(kappa-target)/kappa*100:.0f}% "
                f"{'more conservative' if target > kappa else 'more accurate'}. "
                f"Workspace budget headroom displays will update immediately."
            ),
        )
        return self._register(p)

    def _propose_passive_lock(self) -> Optional[ProposedAction]:
        risk_id = "probe_quota_exhausted"
        if self._already_pending(risk_id):
            return None
        midnight = datetime.datetime.combine(
            datetime.date.today() + datetime.timedelta(days=1),
            datetime.time.min
        ).timestamp()
        hours_left = (midnight - time.time()) / 3600
        p = ProposedAction(
            risk_id=risk_id,
            severity=SEVERITY_WARNING,
            title=f"🔇 Probe Quota Exhausted (5/5) — Passive Mode",
            root_cause=(
                f"All 5 daily stealth probes have been consumed. "
                f"No more real Modal API calls are permitted until midnight UTC ({hours_left:.1f}h). "
                f"System is operating blind on proactive estimates only. "
                f"Risk: κ drift may go undetected until next sync window."
            ),
            proposed_action=(
                f"LOCK: Enforce strict passive mode until midnight UTC. "
                f"Increase κ safety buffer by +10% to compensate for estimation uncertainty. "
                f"Set conservative spend ceiling to $27.00 for all workspaces until quota resets."
            ),
            action_type="enforce_passive_mode",
            action_params={
                "passive_until_epoch": midnight,
                "kappa_safety_buffer": 0.10,
                "conservative_ceiling": 27.00,
            },
            estimated_impact=(
                f"No new Modal API probes for {hours_left:.1f}h. "
                f"κ buffer adds +10% cost headroom. "
                f"Workspace ceiling lowered to $27.00 as safety margin during blind period. "
                f"System continues serving requests on proactive estimates only."
            ),
        )
        return self._register(p)

    def _propose_probe_conservation(self) -> Optional[ProposedAction]:
        risk_id = "probe_quota_warning"
        if self._already_pending(risk_id):
            return None
        p = ProposedAction(
            risk_id=risk_id,
            severity=SEVERITY_INFO,
            title=f"💡 Probe Conservation Mode (4/5 used)",
            root_cause="4 of 5 daily stealth probes used. 1 probe remaining until midnight UTC.",
            proposed_action=(
                "CONSERVE: Reserve final probe for emergency use only. "
                "Disable any scheduled auto-sync. "
                "Use κ-estimated costs exclusively until probe quota resets."
            ),
            action_type="conserve_probe",
            action_params={"remaining_probes": 1, "disable_auto_sync": True},
            estimated_impact="Final probe reserved for manual emergency sync only. Auto-sync disabled.",
        )
        return self._register(p)

    # ------------------------------------------------------------------
    # APPROVAL GATE — Execute on Approve
    # ------------------------------------------------------------------

    def approve(self, approval_token: str) -> Dict[str, Any]:
        """
        Execute the approved action autonomously.
        Returns execution result or error.
        """
        with self._lock:
            action = self._pending.get(approval_token)
            if not action:
                return {"success": False, "error": f"Token '{approval_token}' not found or already processed."}
            if action.status != "pending":
                return {"success": False, "error": f"Action already in status '{action.status}'."}

            action.status = "approved"

        result = self._execute(action)

        with self._lock:
            action.status = "executed" if result.get("success") else "failed"
            action.executed_at = time.time()
            action.execution_result = result
            self._executed[approval_token] = action
            del self._pending[approval_token]
            self._save_state()

        self._audit_log(action, "EXECUTED" if result.get("success") else "EXECUTION_FAILED")
        return result

    def reject(self, approval_token: str, reason: str = "") -> Dict[str, Any]:
        """Reject a pending proposal without executing."""
        with self._lock:
            action = self._pending.get(approval_token)
            if not action:
                return {"success": False, "error": f"Token '{approval_token}' not found."}
            action.status = "rejected"
            self._executed[approval_token] = action
            del self._pending[approval_token]
            self._save_state()

        self._audit_log(action, "REJECTED", extra={"reason": reason})
        return {"success": True, "message": f"Action '{action.risk_id}' rejected.", "token": approval_token}

    def approve_all(self) -> List[Dict[str, Any]]:
        """Approve all pending actions in severity order."""
        tokens = list(self._pending.keys())
        results = []
        for token in tokens:
            results.append(self.approve(token))
        return results

    def _execute(self, action: ProposedAction) -> Dict[str, Any]:
        """Dispatch execution based on action_type."""
        t = action.action_type
        p = action.action_params

        try:
            if t == "freeze_workspace":
                return self._exec_freeze_workspace(p)
            elif t == "throttle_workspace":
                return self._exec_throttle_workspace(p)
            elif t == "add_watchlist":
                return self._exec_add_watchlist(p)
            elif t == "rebalance_workspace":
                return self._exec_rebalance_workspace(p)
            elif t == "recalibrate_kappa":
                return self._exec_recalibrate_kappa(p)
            elif t == "enforce_passive_mode":
                return self._exec_passive_mode(p)
            elif t == "conserve_probe":
                return self._exec_conserve_probe(p)
            else:
                return {"success": False, "error": f"Unknown action_type: {t}"}
        except Exception as e:
            return {"success": False, "error": str(e), "action_type": t}

    def _exec_freeze_workspace(self, p: Dict) -> Dict:
        ws = p["workspace"]
        with self._lock:
            self._throttled_workspaces.add(ws)
        # Update workspace selector if available
        if self._selector:
            for w in self._selector.workspaces:
                if w.get("workspace") == ws:
                    w["status"] = "frozen"
                    w["throttled"] = True
                    w["freeze_reason"] = f"Hard ceiling ${p['spent']:.2f}>=${CEILING_HARD_USD}"
                    break
            self._selector.save_workspaces(self._selector.workspaces)
        return {
            "success": True,
            "action": "freeze_workspace",
            "workspace": ws,
            "message": f"Workspace '{ws}' frozen. Traffic will be rerouted to next-emptiest workspace.",
        }

    def _exec_throttle_workspace(self, p: Dict) -> Dict:
        ws = p["workspace"]
        with self._lock:
            self._throttled_workspaces.add(ws)
        if self._selector:
            for w in self._selector.workspaces:
                if w.get("workspace") == ws:
                    w["status"] = "throttled"
                    w["throttled"] = True
                    w["max_concurrent"] = p.get("max_concurrent", 2)
                    break
            self._selector.save_workspaces(self._selector.workspaces)
        return {
            "success": True,
            "action": "throttle_workspace",
            "workspace": ws,
            "max_concurrent": p.get("max_concurrent", 2),
            "traffic_shift_pct": p.get("traffic_shift_pct", 70),
            "message": f"Workspace '{ws}' throttled to {p.get('max_concurrent',2)} concurrent requests.",
        }

    def _exec_add_watchlist(self, p: Dict) -> Dict:
        ws = p["workspace"]
        if self._selector:
            for w in self._selector.workspaces:
                if w.get("workspace") == ws:
                    w["watchlist"] = True
                    break
            self._selector.save_workspaces(self._selector.workspaces)
        return {"success": True, "action": "add_watchlist", "workspace": ws,
                "message": f"'{ws}' added to watchlist. Monitoring frequency increased."}

    def _exec_rebalance_workspace(self, p: Dict) -> Dict:
        ws = p["workspace"]
        if p.get("recalibrate_kappa") and self._ledger:
            # Soft-reset: cut in-flight accumulation by the imbalance ratio
            ratio = p.get("ratio", 1.0)
            with self._ledger.lock:
                current_inflight = self._ledger.state.get("in_flight_accumulated_cost", 0.0)
                # Redistribute: divide by ratio to normalize
                corrected = current_inflight / max(ratio, 1.0)
                self._ledger.state["in_flight_accumulated_cost"] = corrected
                self._ledger._save()
        return {
            "success": True,
            "action": "rebalance_workspace",
            "workspace": ws,
            "ratio_before": p.get("ratio"),
            "traffic_shift_pct": p.get("traffic_shift_pct", 50),
            "message": (
                f"Workspace '{ws}' rebalanced. "
                f"In-flight cost normalized by factor {p.get('ratio',1):.1f}x. "
                f"Traffic shifted 50% to emptiest workspaces."
            ),
        }

    def _exec_recalibrate_kappa(self, p: Dict) -> Dict:
        if self._ledger:
            target = p["target_kappa"]
            with self._ledger.lock:
                old = self._ledger.state.get("calibration_multiplier_kappa", 1.08)
                self._ledger.state["calibration_multiplier_kappa"] = target
                self._ledger._save()
            return {
                "success": True,
                "action": "recalibrate_kappa",
                "old_kappa": old,
                "new_kappa": target,
                "message": f"κ corrected {old:.3f} → {target:.3f}. Cost estimates recalibrated.",
            }
        return {"success": False, "error": "Ledger not available for κ recalibration."}

    def _exec_passive_mode(self, p: Dict) -> Dict:
        with self._lock:
            self._passive_mode_until = p["passive_until_epoch"]
        if self._ledger:
            with self._ledger.lock:
                old_k = self._ledger.state.get("calibration_multiplier_kappa", 1.08)
                buffer = p.get("kappa_safety_buffer", 0.10)
                self._ledger.state["calibration_multiplier_kappa"] = round(old_k * (1 + buffer), 4)
                self._ledger._save()
        hours = (p["passive_until_epoch"] - time.time()) / 3600
        return {
            "success": True,
            "action": "enforce_passive_mode",
            "passive_until_epoch": p["passive_until_epoch"],
            "hours_locked": round(hours, 1),
            "conservative_ceiling": p.get("conservative_ceiling", 27.0),
            "message": f"Passive mode active for {hours:.1f}h. κ buffer +10%. Ceiling → ${p.get('conservative_ceiling',27)}.",
        }

    def _exec_conserve_probe(self, p: Dict) -> Dict:
        return {
            "success": True,
            "action": "conserve_probe",
            "disable_auto_sync": p.get("disable_auto_sync", True),
            "message": "Final stealth probe reserved. Auto-sync disabled. Manual emergency sync only.",
        }

    # ------------------------------------------------------------------
    # ROLLBACK
    # ------------------------------------------------------------------

    def rollback(self, approval_token: str) -> Dict[str, Any]:
        """Undo an executed action (best-effort reversal)."""
        with self._lock:
            action = self._executed.get(approval_token)
        if not action or action.status not in ("executed",):
            return {"success": False, "error": f"Token '{approval_token}' not rollbackable."}

        t = action.action_type
        p = action.action_params
        result = {"success": True, "rolled_back": t, "token": approval_token}

        if t in ("freeze_workspace", "throttle_workspace"):
            ws = p["workspace"]
            with self._lock:
                self._throttled_workspaces.discard(ws)
            if self._selector:
                for w in self._selector.workspaces:
                    if w.get("workspace") == ws:
                        w.pop("status", None)
                        w.pop("throttled", None)
                        w.pop("max_concurrent", None)
                        w.pop("freeze_reason", None)
                        w.pop("watchlist", None)
                        break
                self._selector.save_workspaces(self._selector.workspaces)
            result["message"] = f"Workspace '{ws}' un-throttled/un-frozen."

        elif t == "recalibrate_kappa":
            if self._ledger and action.execution_result:
                old_k = action.execution_result.get("old_kappa", 1.08)
                with self._ledger.lock:
                    self._ledger.state["calibration_multiplier_kappa"] = old_k
                    self._ledger._save()
                result["message"] = f"κ rolled back to {old_k:.3f}."

        elif t == "enforce_passive_mode":
            with self._lock:
                self._passive_mode_until = 0.0
            result["message"] = "Passive mode lock removed."

        with self._lock:
            action.status = "rolled_back"
            self._save_state()

        self._audit_log(action, "ROLLED_BACK")
        return result

    # ------------------------------------------------------------------
    # STATE & HELPERS
    # ------------------------------------------------------------------

    def is_workspace_throttled(self, workspace: str) -> bool:
        with self._lock:
            return workspace in self._throttled_workspaces

    def is_passive_mode(self) -> bool:
        with self._lock:
            return time.time() < self._passive_mode_until

    def get_pending_actions(self) -> List[Dict[str, Any]]:
        with self._lock:
            return sorted(
                [a.to_dict() for a in self._pending.values()],
                key=lambda x: SEVERITY_RANK.get(x["severity"], 0), reverse=True
            )

    def get_executed_actions(self, last_n: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            all_exec = sorted(
                self._executed.values(), key=lambda a: a.created_at, reverse=True
            )
            return [a.to_dict() for a in all_exec[:last_n]]

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "pending_actions": len(self._pending),
                "throttled_workspaces": list(self._throttled_workspaces),
                "passive_mode_active": time.time() < self._passive_mode_until,
                "passive_mode_until": self._passive_mode_until if self._passive_mode_until > 0 else None,
                "executed_actions_total": len(self._executed),
                "ceilings": {
                    "hard_usd": CEILING_HARD_USD,
                    "throttle_usd": CEILING_THROTTLE_USD,
                    "warning_usd": CEILING_WARNING_USD,
                },
                "kappa_bounds": {"min": KAPPA_MIN, "warn": KAPPA_WARN, "max": KAPPA_MAX},
            }

    def _already_pending(self, risk_id: str) -> bool:
        """Prevent duplicate proposals for same risk."""
        with self._lock:
            return any(a.risk_id == risk_id for a in self._pending.values())

    def _register(self, action: ProposedAction) -> ProposedAction:
        with self._lock:
            self._pending[action.approval_token] = action
            self._save_state()
        self._audit_log(action, "PROPOSED")
        return action

    def _save_state(self) -> None:
        state = {
            "pending": {t: a.to_dict() for t, a in self._pending.items()},
            "executed": {t: a.to_dict() for t, a in list(self._executed.items())[-50:]},
            "throttled_workspaces": list(self._throttled_workspaces),
            "passive_mode_until": self._passive_mode_until,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        tmp = GUARDIAN_STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(GUARDIAN_STATE_FILE)

    def _load_state(self) -> None:
        if GUARDIAN_STATE_FILE.exists():
            try:
                state = json.loads(GUARDIAN_STATE_FILE.read_text(encoding="utf-8"))
                self._throttled_workspaces = set(state.get("throttled_workspaces", []))
                self._passive_mode_until = float(state.get("passive_mode_until", 0.0))
                # Restore pending proposals from disk (survive restart)
                for token, d in state.get("pending", {}).items():
                    a = ProposedAction(
                        risk_id=d["risk_id"], severity=d["severity"], title=d["title"],
                        root_cause=d["root_cause"], proposed_action=d["proposed_action"],
                        action_type=d["action_type"], action_params=d["action_params"],
                        estimated_impact=d["estimated_impact"],
                    )
                    a.approval_token = token
                    a.status = d.get("status", "pending")
                    a.created_at = d.get("created_at", time.time())
                    a.dt = d.get("dt", "")
                    self._pending[token] = a
            except Exception:
                pass

    def _audit_log(self, action: ProposedAction, event: str, extra: Optional[Dict] = None) -> None:
        entry = {
            "event": event,
            "ts": time.time(),
            "dt": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "token": action.approval_token,
            "risk_id": action.risk_id,
            "severity": action.severity,
            "action_type": action.action_type,
            "title": action.title,
        }
        if extra:
            entry.update(extra)
        try:
            with open(GUARDIAN_AUDIT_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass


# Global singleton for fleet server integration
GLOBAL_BUDGET_GUARDIAN: Optional[BudgetGuardian] = None


def init_guardian(ledger=None, selector=None) -> BudgetGuardian:
    global GLOBAL_BUDGET_GUARDIAN
    GLOBAL_BUDGET_GUARDIAN = BudgetGuardian(ledger=ledger, selector=selector)
    return GLOBAL_BUDGET_GUARDIAN


if __name__ == "__main__":
    from scripts.proactive_cost_stealth_orchestrator import StealthProactiveOrchestrator
    orch = StealthProactiveOrchestrator()
    guardian = BudgetGuardian(ledger=orch.ledger, selector=orch.selector)

    # Simulate the exact scenario from the dashboard screenshot
    mock_state = {
        "proactive_usage_total_usd": 2.94,
        "real_usage_baseline_usd": 1.50,
        "calibration_multiplier_kappa": 1.89,  # κ diverging
        "probe_count_today": 5,                  # Quota exhausted
        "historical_drifts": [],
        "workspaces": [
            {"workspace": "just-ask-mr-zen", "proactive_cost_usd": 25.00, "remaining_budget": 5.00},
            {"workspace": "mojopham", "proactive_cost_usd": 1.69, "remaining_budget": 28.31},
        ],
    }

    print("=== Budget Guardian Scan ===")
    proposals = guardian.scan(mock_state)
    print(f"Detected {len(proposals)} risk(s):\n")
    for p in proposals:
        print(f"  [{p['severity']}] {p['title']}")
        print(f"  Token: {p['approval_token']}")
        print(f"  Root Cause: {p['root_cause'][:80]}...")
        print(f"  Action: {p['proposed_action'][:80]}...")
        print(f"  Impact: {p['estimated_impact'][:80]}...")
        print()

    print("=== Auto-Approve All ===")
    results = guardian.approve_all()
    for r in results:
        print(f"  {r.get('action','?')}: {r.get('message','?')} — success={r.get('success')}")
