"""Test response classification, adaptive retry, and circuit breaker (FR-017, FR-022, FR-023, FR-026)."""

import pytest
from service.acquisition.classifier import ResponseClass, ResponseClassifier
from service.acquisition.retry_engine import AdaptiveRetryEngine
from service.acquisition.circuit_breaker import CircuitBreakerManager, BreakerState


def test_response_classifier():
    # 200 Success
    assert ResponseClassifier.classify(200, {"content-type": "text/html"}, "<html>Content</html>") == ResponseClass.SUCCESS

    # 304 Not Modified
    assert ResponseClassifier.classify(304, {}) == ResponseClass.NOT_MODIFIED

    # 429 Rate Limit
    assert ResponseClassifier.classify(429, {"retry-after": "5"}) == ResponseClass.RATE_LIMIT

    # 403 Challenge
    challenge_html = "<div class='cf-turnstile'>Checking browser... Cloudflare</div>"
    assert ResponseClassifier.classify(403, {}, challenge_html) == ResponseClass.INTERACTIVE_CHALLENGE

    # 503 Transient
    assert ResponseClassifier.classify(503, {}) == ResponseClass.TRANSIENT


def test_retry_engine():
    engine = AdaptiveRetryEngine(base_delay=1.0, max_retries=3)

    # Retry transient error
    d1 = engine.compute_retry(1, ResponseClass.TRANSIENT, {})
    assert d1.should_retry is True
    assert d1.delay_seconds > 0

    # Adhere to Retry-After
    d2 = engine.compute_retry(1, ResponseClass.RATE_LIMIT, {"retry-after": "10"})
    assert d2.should_retry is True
    assert d2.delay_seconds == 10.0

    # Permanent failure - DO NOT RETRY
    d3 = engine.compute_retry(1, ResponseClass.INTERACTIVE_CHALLENGE, {})
    assert d3.should_retry is False


def test_circuit_breaker(db_session):
    manager = CircuitBreakerManager(failure_threshold=3, cooldown_minutes=5)
    source_id = "TEST_SOURCE"

    assert manager.can_attempt(source_id, db_session) is True

    # 3 failures trip breaker
    manager.record_failure(source_id, db_session)
    manager.record_failure(source_id, db_session)
    manager.record_failure(source_id, db_session)

    assert manager.can_attempt(source_id, db_session) is False

    # Success closes breaker
    manager.record_success(source_id, db_session)
    assert manager.can_attempt(source_id, db_session) is True
