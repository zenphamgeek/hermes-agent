"""Tests for Pre-fetch Policy and Entitlements."""

from datetime import date, timedelta
from service.core.policy_engine import PolicyEngine, PolicyDecisionType
from service.core.entitlement import EntitlementManager


def test_policy_allowed_url(registry, db_session):
    policy_engine = PolicyEngine(registry)
    decision = policy_engine.evaluate_request(
        source_id="VN_GOV_LEGAL",
        target_url="https://vanban.chinhphu.vn/?docid=180606",
        content_class="legal_document",
        db=db_session
    )
    assert decision.allowed is True
    assert decision.decision == PolicyDecisionType.ALLOWED


def test_policy_denied_external_host(registry, db_session):
    policy_engine = PolicyEngine(registry)
    decision = policy_engine.evaluate_request(
        source_id="VN_GOV_LEGAL",
        target_url="https://malicious-external-site.com/doc",
        content_class="legal_document",
        db=db_session
    )
    assert decision.allowed is False
    assert decision.decision == PolicyDecisionType.DENIED_UNALLOWED_HOST


def test_policy_license_required_blocked(registry, db_session):
    policy_engine = PolicyEngine(registry)
    decision = policy_engine.evaluate_request(
        source_id="ISO_14001",
        target_url="https://iso.org/standard/14001",
        content_class="standards_metadata",
        db=db_session
    )
    assert decision.allowed is False
    assert decision.decision == PolicyDecisionType.DENIED_LICENSE_REQUIRED


def test_policy_license_unblocked_after_entitlement(registry, db_session):
    ent_mgr = EntitlementManager(db_session)
    ent_mgr.register_entitlement(
        source_id="ISO_14001",
        contract_ref="ISO-LIC-2026-001",
        effective_from=date.today() - timedelta(days=1),
        effective_to=date.today() + timedelta(days=365),
        storage_allowed=True
    )

    policy_engine = PolicyEngine(registry)
    decision = policy_engine.evaluate_request(
        source_id="ISO_14001",
        target_url="https://iso.org/standard/14001",
        content_class="standards_metadata",
        db=db_session
    )
    assert decision.allowed is True
