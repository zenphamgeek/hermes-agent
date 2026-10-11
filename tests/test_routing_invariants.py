"""Routing Conformance Property Tests (CI Machine-Enforced Invariants).

Compiles the natural-language routing invariants from AGENTS.md and
05_fleet_delegation_enforcement.md into machine-enforced property tests:
1. Claude models MUST NEVER route to Ultra accounts (protects Ultra Claude quota).
2. Gemini models MUST NEVER route to Nebula gateway (Nebula has zero Gemini).
3. Nebula gateway ONLY serves claude-opus-4.8.
4. Standard Pro nodes can serve both Gemini and Claude models.
"""

import pytest
from pathlib import Path

from hermes_cli.routing_policy import (
    IMMUTABLE_ULTRA_ACCOUNTS,
    IMMUTABLE_NEBULA_NODES,
    IMMUTABLE_NEBULA_MODELS,
    CLAUDE_MODELS,
    GEMINI_MODELS,
    assert_routing_legal,
    RoutingViolation,
    record_routing_attestation,
)


@pytest.mark.parametrize("model", sorted(CLAUDE_MODELS))
@pytest.mark.parametrize("account", sorted(IMMUTABLE_ULTRA_ACCOUNTS))
def test_claude_never_routes_to_ultra(model: str, account: str, tmp_path: Path):
    """Property Invariant: No Claude model may EVER be routed to an Ultra account."""
    ledger = tmp_path / "test_ledger.jsonl"
    with pytest.raises(RoutingViolation, match=r"Claude model.*routed to Ultra account"):
        assert_routing_legal(account=account, model=model, ledger_path=ledger)


@pytest.mark.parametrize("model", sorted(GEMINI_MODELS))
@pytest.mark.parametrize("node", sorted(IMMUTABLE_NEBULA_NODES))
def test_gemini_never_routes_to_nebula(model: str, node: str, tmp_path: Path):
    """Property Invariant: No Gemini model may EVER be routed to Nebula."""
    ledger = tmp_path / "test_ledger.jsonl"
    with pytest.raises(RoutingViolation, match=r"Gemini model.*routed to Nebula node"):
        assert_routing_legal(account=node, model=model, ledger_path=ledger)


def test_nebula_only_serves_opus_48(tmp_path: Path):
    """Property Invariant: Nebula gateway strictly serves claude-opus-4.8 exclusively."""
    ledger = tmp_path / "test_ledger.jsonl"

    # Legal dispatch
    assert_routing_legal("nebula", "claude-opus-4.8", ledger_path=ledger)
    assert_routing_legal("b.ai", "claude-opus-4.8", ledger_path=ledger)

    # Illegal non-Opus-4.8 Claude models on Nebula
    illegal_models = [
        "claude-sonnet-5-5-high",
        "claude-opus-5-5-high",
        "claude-opus-4-6-thinking",
        "claude-3-5-sonnet",
    ]
    for m in illegal_models:
        with pytest.raises(RoutingViolation, match=r"Nebula only serves claude-opus-4.8"):
            assert_routing_legal("nebula", m, ledger_path=ledger)


@pytest.mark.parametrize("pro_node", ["pro-1", "sunward", "insilos", "binhthuong", "justaskgao", "team-3"])
def test_pro_nodes_can_serve_both_gemini_and_claude(pro_node: str, tmp_path: Path):
    """Pro-first mandate: Standard Pro nodes are eligible to serve both Gemini and Claude."""
    ledger = tmp_path / "test_ledger.jsonl"

    # Both Gemini and Claude dispatches must pass
    assert_routing_legal(pro_node, "gemini-3.8-flash-high", ledger_path=ledger)
    assert_routing_legal(pro_node, "gemini-3.1-pro-high", ledger_path=ledger)
    assert_routing_legal(pro_node, "claude-opus-5-5-high", ledger_path=ledger)
    assert_routing_legal(pro_node, "claude-sonnet-5-5-high", ledger_path=ledger)


def test_task_id_and_policy_version_in_attestation_digest(tmp_path: Path):
    """Deterministic Lockstep: attestation records include policy_version and task_id."""
    ledger = tmp_path / "test_lockstep_ledger.jsonl"
    record = record_routing_attestation(
        account="pro-1",
        model="claude-opus-5-5-high",
        verdict="ALLOWED",
        ledger_path=ledger,
        task_id="task-42-security-audit",
        policy_version="1.0.0",
    )
    assert record["policy_version"] == "1.0.0"
    assert record["task_id"] == "task-42-security-audit"
    assert "digest" in record
    assert len(record["digest"]) == 64  # SHA256 hex digest


def test_kanban_slot_capability_tripwire_rejects_claude_on_ultra(tmp_path: Path):
    """Kanban Capability Guard: physically impossible to acquire Claude slot on Ultra node."""
    from hermes_cli.routing_policy import acquire_routing_slot, reset_routing_slots_for_testing

    reset_routing_slots_for_testing()
    ledger = tmp_path / "test_kanban_ledger.jsonl"

    with pytest.raises(RoutingViolation, match=r"(?i)Kanban capability tripwire.*ultra"):
        acquire_routing_slot(node="ultra-2", model="claude-opus-5-5-high", ledger_path=ledger)


def test_kanban_slot_capability_tripwire_rejects_gemini_on_nebula(tmp_path: Path):
    """Kanban Capability Guard: physically impossible to acquire Gemini slot on Nebula node."""
    from hermes_cli.routing_policy import acquire_routing_slot, reset_routing_slots_for_testing

    reset_routing_slots_for_testing()
    ledger = tmp_path / "test_kanban_ledger.jsonl"

    with pytest.raises(RoutingViolation, match=r"(?i)Kanban capability tripwire.*nebula"):
        acquire_routing_slot(node="nebula", model="gemini-3.8-flash-high", ledger_path=ledger)


def test_kanban_slot_wip_concurrency_limit_and_release(tmp_path: Path):
    """Kanban WIP Limiter: enforces max_in_flight per node and recovers on slot release."""
    from hermes_cli.routing_policy import (
        acquire_routing_slot,
        release_routing_slot,
        get_active_slots_count,
        reset_routing_slots_for_testing,
    )

    reset_routing_slots_for_testing()
    ledger = tmp_path / "test_kanban_ledger.jsonl"

    slot1 = acquire_routing_slot("pro-1", "gemini-3.8-flash-high", max_in_flight=2, ledger_path=ledger)
    slot2 = acquire_routing_slot("pro-1", "claude-opus-5-5-high", max_in_flight=2, ledger_path=ledger)

    assert get_active_slots_count("pro-1") == 2

    # 3rd slot should breach WIP limit
    with pytest.raises(RuntimeError, match=r"WIP limit reached for node 'pro-1': 2/2"):
        acquire_routing_slot("pro-1", "claude-sonnet-5-5-high", max_in_flight=2, ledger_path=ledger)

    # Releasing slot1 frees up capacity
    assert release_routing_slot(slot1) is True
    assert get_active_slots_count("pro-1") == 1

    slot3 = acquire_routing_slot("pro-1", "claude-sonnet-5-5-high", max_in_flight=2, ledger_path=ledger)
    assert get_active_slots_count("pro-1") == 2

    release_routing_slot(slot2)
    release_routing_slot(slot3)
    assert get_active_slots_count("pro-1") == 0


def test_kanban_slot_ttl_expiry_prevents_deadlock(tmp_path: Path):
    """Kanban Leased Semaphore: expired slots auto-pruned to prevent deadlocks from crashed workers."""
    import time
    from hermes_cli.routing_policy import (
        acquire_routing_slot,
        get_active_slots_count,
        reset_routing_slots_for_testing,
    )

    reset_routing_slots_for_testing()
    ledger = tmp_path / "test_kanban_ledger.jsonl"

    # Acquire slot with short 0.1s TTL
    slot = acquire_routing_slot("pro-1", "gemini-3.8-flash-high", ttl_seconds=0.1, max_in_flight=1, ledger_path=ledger)
    assert get_active_slots_count("pro-1") == 1

    time.sleep(0.15)
    assert get_active_slots_count("pro-1") == 0

    # Auto-prune on next acquire allows new slot despite crashed previous worker
    slot2 = acquire_routing_slot("pro-1", "claude-opus-5-5-high", ttl_seconds=60.0, max_in_flight=1, ledger_path=ledger)
    assert slot2.slot_id != slot.slot_id
    assert get_active_slots_count("pro-1") == 1


def test_cartesian_product_routing_invariants():
    """Cartesian-product property test over Tier x Family (Nebula Spike Verification)."""
    from itertools import product
    from hermes_cli.routing_policy import Tier, Family, RouteRequest, is_allowed

    sample_models = {
        Family.GEMINI: ["gemini-3.1-pro-high", "gemini-3.8-flash-high"],
        Family.CLAUDE: ["claude-opus-4.8", "claude-opus-5-5-high", "claude-sonnet-5-5-high"],
    }
    for tier, family in product(Tier, Family):
        for model in sample_models[family]:
            req = RouteRequest(tier, family, model)
            allowed = is_allowed(req)
            # Invariant 1: Ultra must never route Claude
            if tier is Tier.ULTRA and family is Family.CLAUDE:
                assert not allowed, f"VIOLATION: Ultra served Claude {model}"
            # Invariant 2: Nebula must never route Gemini
            if tier is Tier.NEBULA and family is Family.GEMINI:
                assert not allowed, f"VIOLATION: Nebula served Gemini {model}"
            # Invariant 3: Nebula Claude limited strictly to opus-4.8
            if tier is Tier.NEBULA and family is Family.CLAUDE:
                assert allowed == (model == "claude-opus-4.8"), f"VIOLATION: Nebula allowed non-Opus-4.8 {model}"
            # Invariant 4: Pro tier can serve both
            if tier is Tier.PRO:
                assert allowed is True


def test_kanban_slot_fence_tokens_and_monotonic_clock(tmp_path):
    """Verifies that RoutingSlots carry monotonically increasing fence tokens."""
    from hermes_cli.routing_policy import (
        acquire_routing_slot,
        reset_routing_slots_for_testing,
    )

    reset_routing_slots_for_testing()
    ledger = tmp_path / "test_fence_ledger.jsonl"

    s1 = acquire_routing_slot("pro-1", "gemini-3.8-flash-high", ttl_seconds=10.0, max_in_flight=5, ledger_path=ledger)
    s2 = acquire_routing_slot("pro-1", "claude-opus-5-5-high", ttl_seconds=10.0, max_in_flight=5, ledger_path=ledger)
    s3 = acquire_routing_slot("node-4", "gemini-3.8-flash-high", ttl_seconds=10.0, max_in_flight=5, ledger_path=ledger)

    assert s1.fence_token >= 1
    assert s2.fence_token > s1.fence_token
    assert s3.fence_token > s2.fence_token
    assert s2.acquired_at >= s1.acquired_at
    assert s3.acquired_at >= s2.acquired_at


def test_monotonic_crdt_quota_ledger_merge_and_fencing():
    """Verifies CRDT grow-only quota ledger max-merge idempotence and fence verification."""
    from hermes_cli.routing_policy import MonotonicCRDTQuotaLedger, MonotonicQuotaEntry

    ledger_local = MonotonicCRDTQuotaLedger(window_size_seconds=100.0)
    ledger_remote = MonotonicCRDTQuotaLedger(window_size_seconds=100.0)

    # Local records 5 requests on pro-1 with fence 10
    e1 = ledger_local.record_usage("pro-1", units=5, fence_token=10)
    assert e1.counter == 5
    assert e1.fence_token == 10
    assert ledger_local.get_usage("pro-1") == 5

    # Remote records 8 requests on pro-1 with fence 12
    e2 = ledger_remote.record_usage("pro-1", units=8, fence_token=12)
    assert e2.counter == 8
    assert e2.fence_token == 12

    # Remote records 3 requests on node-4
    ledger_remote.record_usage("node-4", units=3, fence_token=5)

    # Merge remote into local: pro-1 should take max(5, 8) = 8, fence max(10, 12) = 12
    ledger_local.merge(ledger_remote.to_dict())
    assert ledger_local.get_usage("pro-1") == 8
    assert ledger_local.get_usage("node-4") == 3

    # Idempotent re-merge
    ledger_local.merge(ledger_remote.to_dict())
    assert ledger_local.get_usage("pro-1") == 8

    # Fence verification
    assert ledger_local.verify_fence("pro-1", fence_token=12) is True
    assert ledger_local.verify_fence("pro-1", fence_token=15) is True
    assert ledger_local.verify_fence("pro-1", fence_token=9) is False  # Stale fence token rejected


def test_offline_fallback_cascade_fails_closed():
    """Chaos Property Test: If all nodes in fallback cascade violate policy or are exhausted,
    the dispatch MUST fail closed with RoutingViolation (never silent pass or infinite loop)."""
    from hermes_cli.routing_policy import assert_routing_legal, RoutingViolation

    # Attempting to route Claude to Ultra account in an offline / fallback attempt
    with pytest.raises(RoutingViolation, match="Ultra accounts strictly serve Gemini only"):
        assert_routing_legal("ultra-2", "claude-opus-5-5-high")

    # Attempting to route Gemini to Nebula API in an offline fallback
    with pytest.raises(RoutingViolation, match="Nebula strictly serves Claude Opus 4.8 only"):
        assert_routing_legal("nebula", "gemini-3.8-flash-high")




