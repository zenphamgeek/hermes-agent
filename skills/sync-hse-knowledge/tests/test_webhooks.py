"""Tests for Outbound HMAC-SHA256 Webhook Hub."""

from service.webhooks.dispatcher import WebhookDispatcher, HSEEvent
from service.db.models import WebhookSubscription


def test_webhook_signing(db_session):
    dispatcher = WebhookDispatcher(db_session)
    secret = "test_sec_2026"
    payload = b'{"event":"test"}'
    sig = dispatcher.sign_payload(payload, secret)
    assert len(sig) == 64  # SHA256 hex string


def test_webhook_dispatch_audit_logging(db_session):
    sub = WebhookSubscription(
        name="test-sub",
        target_url="http://dummy-local-target:9999/wh",
        secret_token="sec123",
        event_types=["*"]
    )
    db_session.add(sub)
    db_session.commit()

    dispatcher = WebhookDispatcher(db_session)
    event = HSEEvent(
        event_id="evt_01",
        event_type="hse.sync.completed",
        timestamp="2026-08-21T00:00:00Z",
        data={"items": 10}
    )
    deliveries = dispatcher.dispatch_event(event)
    assert len(deliveries) == 1
    assert deliveries[0].event_type == "hse.sync.completed"
