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


def test_enforce_routing_invariant_alias_and_unknown_model_fail_closed():
    """Nebula Dialectic Synthesis: enforce_routing_invariant rejects Claude and unknown models on Ultra."""
    from hermes_cli.routing_policy import enforce_routing_invariant, RoutingViolation

    # Ultra rejects Claude
    with pytest.raises(RoutingViolation, match="Ultra accounts strictly serve Gemini only"):
        enforce_routing_invariant("ultra-2", "claude-opus-5-5-high")

    # Ultra rejects unknown/non-approved models (fail-closed on unknown model)
    with pytest.raises(RoutingViolation, match="Non-Gemini model"):
        enforce_routing_invariant("ultra-2", "gpt-4o")

    # Nebula rejects Gemini
    with pytest.raises(RoutingViolation, match="Nebula strictly serves Claude Opus 4.8 only"):
        enforce_routing_invariant("nebula", "gemini-3.1-pro-high")

    # Nebula rejects non-opus-4.8 Claude models
    with pytest.raises(RoutingViolation, match="Nebula only serves claude-opus-4.8"):
        enforce_routing_invariant("nebula", "claude-sonnet-5-5-high")

    # Pro can serve Gemini and Claude
    enforce_routing_invariant("pro-1", "gemini-3.8-flash-high")
    enforce_routing_invariant("pro-1", "claude-opus-5-5-high")


def test_fleet_routing_enforce_flag_and_degrade(monkeypatch):
    """SRE Emergency Degrade: FLEET_ROUTING_ENFORCE=warn logs warning without throwing."""
    from hermes_cli.routing_policy import (
        assert_routing_legal,
        RoutingViolation,
        _reset_guard_override_state,
    )

    _reset_guard_override_state()
    # 1. By default or with block, it raises
    monkeypatch.setenv("FLEET_ROUTING_ENFORCE", "block")
    monkeypatch.delenv("FLEET_ROUTING_GUARD", raising=False)
    with pytest.raises(RoutingViolation):
        assert_routing_legal("ultra-2", "claude-opus-5-5-high")

    # 2. When degraded to warn by SRE, it does not raise
    monkeypatch.setenv("FLEET_ROUTING_ENFORCE", "warn")
    _reset_guard_override_state()
    # Should not raise exception
    assert_routing_legal("ultra-2", "claude-opus-5-5-high")

    _reset_guard_override_state()


def test_sovereign_policy_manifest_invariants():
    """Nebula Finding 5: Sovereign Policy Manifest formal specs."""
    from hermes_cli.routing_policy import (
        SOVEREIGN_POLICY_MANIFEST,
        Tier,
        Family,
        GEMINI_MODELS,
        CLAUDE_MODELS,
        IMMUTABLE_NEBULA_MODELS,
    )

    ultra_spec = SOVEREIGN_POLICY_MANIFEST[Tier.ULTRA]
    assert Family.GEMINI in ultra_spec.allowed_families
    assert Family.CLAUDE in ultra_spec.forbidden_families
    assert ultra_spec.allowed_models == GEMINI_MODELS

    nebula_spec = SOVEREIGN_POLICY_MANIFEST[Tier.NEBULA]
    assert Family.CLAUDE in nebula_spec.allowed_families
    assert Family.GEMINI in nebula_spec.forbidden_families
    assert nebula_spec.allowed_models == IMMUTABLE_NEBULA_MODELS

    pro_spec = SOVEREIGN_POLICY_MANIFEST[Tier.PRO]
    assert Family.CLAUDE in pro_spec.allowed_families
    assert Family.GEMINI in pro_spec.allowed_families
    assert len(pro_spec.forbidden_families) == 0


def test_assert_node_tier_compliance():
    """Nebula Finding 5: Nodes cannot claim unauthorized tiers in untracked rosters."""
    from hermes_cli.routing_policy import assert_node_tier_compliance, RoutingViolation, Tier

    # Valid claims
    assert_node_tier_compliance("ultra-2", "ultra")
    assert_node_tier_compliance("lthn.ariana", Tier.ULTRA)
    assert_node_tier_compliance("nebula", "nebula")
    assert_node_tier_compliance("b.ai", Tier.NEBULA)
    assert_node_tier_compliance("pro-1", "pro")
    assert_node_tier_compliance("sunward", Tier.PRO)

    # Tampered claims fail closed
    with pytest.raises(RoutingViolation, match=r"Config Integrity Violation.*Ultra account"):
        assert_node_tier_compliance("ultra-2", "pro")

    with pytest.raises(RoutingViolation, match=r"Config Integrity Violation.*Ultra account"):
        assert_node_tier_compliance("lthn.ariana", "nebula")

    with pytest.raises(RoutingViolation, match=r"Config Integrity Violation.*Nebula node"):
        assert_node_tier_compliance("nebula", "pro")

    with pytest.raises(RoutingViolation, match=r"Config Integrity Violation.*Nebula node"):
        assert_node_tier_compliance("b.ai", "ultra")


def test_verify_roster_consistency_detects_tier_tampering(tmp_path: Path):
    """Configuration Integrity: Roster consistency fails if an Ultra node claims Pro tier."""
    import yaml
    from hermes_cli.routing_policy import verify_roster_consistency, RoutingViolation

    tampered_roster = tmp_path / "fleet_roster_tampered.yml"
    roster_data = {
        "version": "1.0",
        "pools": {
            "pro-claude-pool": {
                "nodes": [
                    {"alias": "pro-1", "tier": "pro"},
                    {"alias": "ultra-2", "tier": "pro"},  # Tampered tier!
                ]
            }
        }
    }
    with open(tampered_roster, "w", encoding="utf-8") as f:
        yaml.dump(roster_data, f)

    is_consistent, violations = verify_roster_consistency(tampered_roster, fail_closed=False)
    assert not is_consistent
    assert any("Ultra account" in v or "CRITICAL ROSTER DRIFT" in v for v in violations)

    with pytest.raises(RoutingViolation):
        verify_roster_consistency(tampered_roster, fail_closed=True)


@pytest.mark.parametrize("pro_avail", [True, False])
@pytest.mark.parametrize("nebula_avail", [True, False])
@pytest.mark.parametrize("ultra_avail", [True, False])
def test_claude_compound_outage_property_invariants(pro_avail: bool, nebula_avail: bool, ultra_avail: bool):
    """Nebula Finding 6 / Compound Outage Invariant:
    Under ANY node availability state, Claude tasks NEVER route to Ultra accounts.
    If no legal capacity exists (Pro exhausted AND Nebula down), it MUST fail-closed with NoCapacityError.
    """
    from hermes_cli.routing_policy import (
        resolve_fleet_route,
        NoCapacityError,
        IMMUTABLE_ULTRA_ACCOUNTS,
    )

    # 1. Test claude-opus-4.8 (eligible for Nebula fallback)
    if not pro_avail and not nebula_avail:
        with pytest.raises(NoCapacityError, match=r"Zero legal Claude capacity"):
            resolve_fleet_route(
                model="claude-opus-4.8",
                pro_claude_available=pro_avail,
                nebula_available=nebula_avail,
                ultra_available=ultra_avail,
            )
    else:
        node, model = resolve_fleet_route(
            model="claude-opus-4.8",
            pro_claude_available=pro_avail,
            nebula_available=nebula_avail,
            ultra_available=ultra_avail,
        )
        assert node not in IMMUTABLE_ULTRA_ACCOUNTS, f"Claude task breached Ultra boundary: {node}"
        if not pro_avail and nebula_avail:
            assert node == "nebula"
        elif pro_avail:
            assert node == "pro-1"

    # 2. Test non-opus-4.8 Claude model (e.g. claude-opus-5-5-high, not eligible for Nebula)
    if not pro_avail:
        with pytest.raises(NoCapacityError):
            resolve_fleet_route(
                model="claude-opus-5-5-high",
                pro_claude_available=pro_avail,
                nebula_available=nebula_avail,
                ultra_available=ultra_avail,
            )
    else:
        node, model = resolve_fleet_route(
            model="claude-opus-5-5-high",
            pro_claude_available=pro_avail,
            nebula_available=nebula_avail,
            ultra_available=ultra_avail,
        )
        assert node not in IMMUTABLE_ULTRA_ACCOUNTS
        assert node == "pro-1"


@pytest.mark.parametrize("ultra_avail", [True, False])
@pytest.mark.parametrize("pro_gemini_avail", [True, False])
@pytest.mark.parametrize("nebula_avail", [True, False])
def test_gemini_compound_outage_never_touches_nebula(ultra_avail: bool, pro_gemini_avail: bool, nebula_avail: bool):
    """Under ANY failure state, Gemini tasks NEVER touch Nebula nodes."""
    from hermes_cli.routing_policy import (
        resolve_fleet_route,
        NoCapacityError,
        IMMUTABLE_NEBULA_NODES,
    )

    if not ultra_avail and not pro_gemini_avail:
        with pytest.raises(NoCapacityError, match=r"Zero legal Gemini capacity"):
            resolve_fleet_route(
                model="gemini-3.8-flash-high",
                pro_claude_available=True,
                nebula_available=nebula_avail,
                ultra_available=ultra_avail,
                pro_gemini_available=pro_gemini_avail,
            )
    else:
        node, model = resolve_fleet_route(
            model="gemini-3.8-flash-high",
            pro_claude_available=True,
            nebula_available=nebula_avail,
            ultra_available=ultra_avail,
            pro_gemini_available=pro_gemini_avail,
        )
        assert node not in IMMUTABLE_NEBULA_NODES, f"Gemini task breached Nebula boundary: {node}"


def test_redact_routing_attestation_record_crypto_shredding(tmp_path):
    """Verifies that 72h right-to-erasure / crypto-shredding tombstones sensitive fields while preserving ledger integrity."""
    import json
    from hermes_cli.routing_policy import (
        record_routing_attestation,
        redact_routing_attestation_record,
        verify_routing_attestation_ledger,
    )

    ledger_file = tmp_path / "test_ledger.jsonl"

    # Append 3 records
    rec1 = record_routing_attestation("pro-1", "claude-opus-5-5-high", "ALLOWED", ledger_path=ledger_file, task_id="task-100")
    rec2 = record_routing_attestation("ultra-2", "gemini-3.1-pro-high", "ALLOWED", ledger_path=ledger_file, task_id="task-200")
    rec3 = record_routing_attestation("sunward", "claude-sonnet-5-5-high", "ALLOWED", ledger_path=ledger_file, task_id="task-300")

    is_valid, violations = verify_routing_attestation_ledger(ledger_file)
    assert is_valid, f"Initial ledger should be valid: {violations}"

    # Redact task-200 (GDPR Right to Erasure within 72h)
    redacted_count = redact_routing_attestation_record("task-200", ledger_path=ledger_file, redacted_reason="GDPR_RIGHT_TO_ERASURE")
    assert redacted_count == 1

    # Verify task-200 fields are shredded
    records = []
    with open(ledger_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line.strip()))

    assert len(records) == 3

    r1 = next(r for r in records if r["task_id"] == "task-100")
    assert r1["account"] == "pro-1"
    assert r1.get("redacted") is not True

    r2 = next(r for r in records if r["task_id"] == "task-200")
    assert r2["account"] == "[REDACTED]"
    assert r2["model"] == "[REDACTED]"
    assert r2["redacted"] is True
    assert r2["redacted_reason"] == "GDPR_RIGHT_TO_ERASURE"
    assert "redacted_at" in r2
    assert r2["digest"] != rec2["digest"]  # Digest updated to tombstone hash

    r3 = next(r for r in records if r["task_id"] == "task-300")
    assert r3["account"] == "sunward"
    assert r3.get("redacted") is not True

    # Ledger verification must pass with zero violations on lawful tombstones
    is_valid_after, violations_after = verify_routing_attestation_ledger(ledger_file)
    assert is_valid_after, f"Ledger with tombstoned records must remain valid: {violations_after}"
    assert len(violations_after) == 0

    # Redacting non-existent task returns 0
    assert redact_routing_attestation_record("nonexistent-task", ledger_path=ledger_file) == 0






