#!/usr/bin/env python3
"""
Unit and Counterfactual Chaos Test Suite for Hybrid Logical Clocks (HLC),
300s Clock-Skew Token Validation, Monotonic Lease Fencing, and CWE-20 Node ID Guard.
"""

import pytest

from tools.hlc_clock_drift_guard import (
    AuthTokenValidator,
    DistributedLeaseGuard,
    HLCTimestamp,
    HybridLogicalClock,
    validate_fleet_node_id,
)


def test_oauth2_jwt_validation_under_5min_clock_drift() -> None:
    # Node B (+300s ahead) issues token with nbf=10300, exp=10900; Node A is at t=10000
    token = {"nbf": 10300.0, "exp": 10900.0}
    naive = AuthTokenValidator(clock_skew_leeway=0)
    ok_naive, reason_naive = naive.validate_token(token, current_time=10000.0)
    assert ok_naive is False
    assert "TokenNotYetValid" in reason_naive

    hardened = AuthTokenValidator(clock_skew_leeway=300)
    ok_hardened, reason_hardened = hardened.validate_token(token, current_time=10000.0)
    assert ok_hardened is True
    assert reason_hardened == "Valid"

    # Beyond 300s leeway (e.g. 301s drift) must still reject
    ok_excess, _ = hardened.validate_token(token, current_time=9998.0)
    assert ok_excess is False


def test_causal_ordering_under_5min_clock_skew() -> None:
    # Node A at t=10000 emits E1; Node B has clock lagging by -300s (t=9700) and receives E1 -> emits E2
    node_a = HybridLogicalClock()
    node_b = HybridLogicalClock()

    e1 = node_a.now(wall_time=10000.0)
    e2 = node_b.receive(remote_hlc=e1, wall_time=9700.0)

    assert e1 == HLCTimestamp(10000.0, 0)
    assert e2 == HLCTimestamp(10000.0, 1)
    assert e2 > e1


def test_distributed_lease_split_brain_fencing() -> None:
    guard = DistributedLeaseGuard()
    # Active epoch 42, elapsed 120s < 300s TTL -> valid
    assert guard.is_valid(grant_epoch_seq=42, current_epoch_seq=42, monotonic_elapsed=120.0, ttl=300.0) is True
    # Stale epoch 41 attempting concurrent write after epoch fenced to 42 -> rejected
    assert guard.is_valid(grant_epoch_seq=41, current_epoch_seq=42, monotonic_elapsed=10.0, ttl=300.0) is False
    # Expired monotonic elapsed >= ttl -> rejected
    assert guard.is_valid(grant_epoch_seq=42, current_epoch_seq=42, monotonic_elapsed=300.0, ttl=300.0) is False


def test_cwe20_validate_fleet_node_id() -> None:
    assert validate_fleet_node_id("coderedgen") == "coderedgen"
    assert validate_fleet_node_id("node-4_pro") == "node-4_pro"
    for malicious in ["node-4; rm -rf /", "node$(id)", "../etc/passwd", ""]:
        with pytest.raises(ValueError, match="CWE-20"):
            validate_fleet_node_id(malicious)


def test_whatif_3g_virtual_escrow_retry_storm_deadlock_mitigation() -> None:
    from tools.modal_budget_guard import InFlightLeaseLedger

    ledger = InFlightLeaseLedger()
    ledger.clear()

    # 5 consecutive 3G network retries with distinct job_ids but identical idempotency_key
    for attempt in range(1, 6):
        ok, msg = ledger.acquire_lease(
            job_id=f"job-3g-attempt-{attempt}",
            estimated_cost=1.50,
            remaining_credits=12.00,
            min_required_credits=10.00,
            ttl_s=180.0,
            idempotency_key="req-3g-edge-001",
        )
        assert ok is True
        if attempt == 1:
            assert msg == "Lease acquired"
        else:
            assert "Idempotent reuse of active lease for job job-3g-attempt-1" in msg

    assert ledger.total_in_flight_cost() == pytest.approx(1.50)


def test_inflight_lease_monotonic_expiration_under_ntp_step() -> None:
    from tools.modal_budget_guard import InFlightLease

    lease = InFlightLease("job-mono-001", estimated_cost=1.25, ttl_s=0.01, idempotency_key="payload-hash-abc")
    assert lease.idempotency_key == "payload-hash-abc"
    # Even if wall-clock expires_at is pushed +300s into the future by an NTP backward jump,
    # monotonic expiration must still expire the lease after 10ms.
    lease.expires_at += 300.0
    lease.expires_at_mono -= 1.0
    assert lease.is_expired is True


def test_atomic_release_lease_and_model_resolver() -> None:
    from tools.hlc_clock_drift_guard import resolve_model_for_node
    from tools.modal_budget_guard import InFlightLeaseLedger

    ledger = InFlightLeaseLedger()
    ledger.clear()
    ok, _ = ledger.acquire_lease(
        job_id="job-cas-1",
        estimated_cost=1.50,
        remaining_credits=20.0,
        min_required_credits=10.0,
        idempotency_key="payload-sha256-xyz",
    )
    assert ok is True
    # Wrong idempotency_key must fail atomic release
    assert ledger.release_lease("job-cas-1", idempotency_key="wrong-key") is False
    # Exact idempotency_key succeeds once, and duplicate release returns False
    assert ledger.release_lease("job-cas-1", idempotency_key="payload-sha256-xyz") is True
    assert ledger.release_lease("job-cas-1", idempotency_key="payload-sha256-xyz") is False

    # Group B model resolution: native Argon support + Claude 5.5 -> 4.6 adaptation
    m1, adapted1 = resolve_model_for_node("insilos", "gemini-4-argon-high")
    assert m1 == "gemini-4-argon-high" and adapted1 is False
    m2, adapted2 = resolve_model_for_node("insilos", "claude-opus-5-5-high")
    assert m2 == "claude-opus-4-6-thinking" and adapted2 is True
    m3, adapted3 = resolve_model_for_node("insilos", "gemini-4-argon-high", adapt_argon_to_flash=True)
    assert m3 == "gemini-3.8-flash-high" and adapted3 is True


def test_acoustic_clause_guard_and_passive_credit_rule() -> None:
    from pathlib import Path
    from assets.scripts_video.tts_v0_sense_synthesizer import _segment_acoustic_clauses

    sample = (
        "Trong thế giới tối ưu hóa phi lồi... các điểm yên ngựa xuất hiện dày đặc hơn cực tiểu cục bộ "
        "theo cấp số nhân khi số chiều không gian tăng lên hàng triệu tham số."
    )
    clauses = _segment_acoustic_clauses(sample, max_chars=75)
    assert len(clauses) >= 2
    assert all(len(c) <= 75 for c in clauses)
    assert all("..." not in c for c in clauses)

    rule_path = Path(__file__).resolve().parents[1] / ".agents" / "rules" / "05_modal_gpu_fleet_and_token_invariants.md"
    rule_text = rule_path.read_text(encoding="utf-8")
    assert "Passive Mathematical Credit Calculation (0 Outbound Scraping)" in rule_text
    assert ".modal_billing_ledger.json" in rule_text
