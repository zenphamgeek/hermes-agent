"""Test policy engine decisions and entitlement gating (FR-002, FR-005, FR-006)."""

import pytest
from service.core.policy_engine import PolicyEngine, PolicyDecisionType


def test_allowed_host_decision(registry, db_session):
    engine = PolicyEngine(registry)
    decision = engine.evaluate_request(
        source_id="VN_GOV_LEGAL",
        url="https://vanban.chinhphu.vn/he-thong-van-ban",
        content_class="legal_document",
        db=db_session
    )
    assert decision.decision == PolicyDecisionType.ALLOW_FULL
    assert decision.can_fetch_content is True
    assert decision.can_store_raw is True


def test_denied_outside_host(registry, db_session):
    engine = PolicyEngine(registry)
    decision = engine.evaluate_request(
        source_id="VN_GOV_LEGAL",
        url="https://random-untrusted-site.com/doc.pdf",
        content_class="legal_document",
        db=db_session
    )
    assert decision.decision == PolicyDecisionType.DENIED_UNALLOWED_HOST
    assert decision.can_fetch_content is False


def test_denied_url_pattern(registry, db_session):
    engine = PolicyEngine(registry)
    decision = engine.evaluate_request(
        source_id="VN_GOV_LEGAL",
        url="https://vanban.chinhphu.vn/login",
        content_class="legal_document",
        db=db_session
    )
    assert decision.decision == PolicyDecisionType.DENIED_URL_PATTERN
    assert decision.can_fetch_content is False


def test_license_required_negative_test(registry, db_session):
    """Test that WCO content is gated and blocked when no entitlement is active (FR-005)."""
    engine = PolicyEngine(registry)
    decision = engine.evaluate_request(
        source_id="WCO_HS_CONTENT",
        url="https://www.wcotradetools.org/en/harmonized-system",
        content_class="wco_explanatory_notes",
        db=db_session
    )
    assert decision.decision == PolicyDecisionType.LICENSE_REQUIRED
    assert decision.can_fetch_content is False
    assert decision.can_store_raw is False
