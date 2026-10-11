"""Unit and integration tests for Webhook Subsystem (Outbound dispatcher & Inbound trigger)."""

import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from service.db.session import get_db_session, init_db
from service.db.models import WebhookSubscription, WebhookDeliveryLog
from service.webhooks.dispatcher import WebhookDispatcher, compute_signature, verify_signature
from service.api.main import app
from service.cli import app as cli_app


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()


@pytest.fixture
def db():
    with get_db_session() as session:
        yield session


def test_hmac_signature_generation_and_verification():
    payload = json.dumps({"event": "test", "data": 123}, sort_keys=True)
    secret = "super-secret-key-12345"

    sig = compute_signature(payload, secret)
    assert sig.startswith("sha256=")
    assert verify_signature(payload, secret, sig) is True
    assert verify_signature(payload, "wrong-key", sig) is False
    assert verify_signature(payload + "tampered", secret, sig) is False


def test_subscription_crud(db):
    dispatcher = WebhookDispatcher(db=db)

    # 1. Create
    sub = dispatcher.create_subscription(
        name="test-subscriber",
        target_url="https://webhook.example.com/hs-events",
        event_types=["hs.ruling.published", "hs.tariff.changed"],
        secret_token="token-abc-987"
    )
    assert len(sub.subscription_id) > 0
    assert sub.name == "test-subscriber"
    assert sub.event_types == ["hs.ruling.published", "hs.tariff.changed"]
    assert sub.is_active is True

    # 2. List
    subs = dispatcher.list_subscriptions()
    assert any(s.subscription_id == sub.subscription_id for s in subs)

    # 3. Delete
    deleted = dispatcher.delete_subscription(sub.subscription_id)
    assert deleted is True
    assert db.query(WebhookSubscription).filter_by(subscription_id=sub.subscription_id).first() is None


def test_event_dispatch_filtering(db):
    # Clean any leftover subscriptions
    db.query(WebhookSubscription).delete()
    db.commit()

    dispatcher = WebhookDispatcher(db=db)

    # Create sub 1: all events (*)
    sub_all = dispatcher.create_subscription(
        name="sub-all",
        target_url="https://mock.example.com/all",
        event_types=["*"]
    )

    # Create sub 2: only rulings
    sub_rulings = dispatcher.create_subscription(
        name="sub-rulings",
        target_url="https://mock.example.com/rulings",
        event_types=["hs.ruling.published"]
    )

    try:
        with patch.object(dispatcher, "_send_to_subscriber") as mock_send:
            mock_log = MagicMock()
            mock_log.status = "SUCCESS"
            mock_send.return_value = mock_log

            # Dispatch hs.ruling.published -> both should receive
            dispatcher.dispatch_event("hs.ruling.published", {"ruling_id": "R001"})
            assert mock_send.call_count == 2

            mock_send.reset_mock()

            # Dispatch hs.tariff.changed -> only sub_all should receive
            dispatcher.dispatch_event("hs.tariff.changed", {"chapter": "84"})
            assert mock_send.call_count == 1
    finally:
        dispatcher.delete_subscription(sub_all.subscription_id)
        dispatcher.delete_subscription(sub_rulings.subscription_id)


def test_webhook_successful_delivery_and_headers(db):
    dispatcher = WebhookDispatcher(db=db)
    sub = dispatcher.create_subscription(
        name="test-delivery",
        target_url="https://mock.site/webhook",
        event_types=["*"],
        secret_token="sign-me-secret"
    )

    try:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"received": true}'

        with patch.object(dispatcher.client, "post", return_value=mock_response) as mock_post:
            log = dispatcher.dispatch_event("hs.legal_doc.promulgated", {"doc_number": "18/2026/TT-BTC"})[0]

            assert log.status == "SUCCESS"
            assert log.response_status_code == 200
            assert log.subscription_id == sub.subscription_id

            # Verify outbound call arguments & headers
            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            headers = kwargs["headers"]
            assert headers["X-HS-Event"] == "hs.legal_doc.promulgated"
            assert "X-HS-Delivery-ID" in headers
            assert "X-HS-Signature-256" in headers
            assert headers["X-HS-Signature-256"].startswith("sha256=")

            # Verify body payload structure
            payload = json.loads(kwargs["content"])
            assert payload["event_type"] == "hs.legal_doc.promulgated"
            assert payload["data"]["doc_number"] == "18/2026/TT-BTC"
    finally:
        dispatcher.delete_subscription(sub.subscription_id)


def test_webhook_retry_and_auto_deactivation(db):
    dispatcher = WebhookDispatcher(db=db)
    sub = dispatcher.create_subscription(
        name="flaky-subscriber",
        target_url="https://flaky.site/error",
        event_types=["*"]
    )

    try:
        # Simulate 500 error from target subscriber
        mock_err_response = MagicMock()
        mock_err_response.status_code = 500
        mock_err_response.text = "Internal Server Error"

        with patch.object(dispatcher.client, "post", return_value=mock_err_response):
            log = dispatcher.dispatch_event("hs.sync.completed", {"status": "ok"}, max_retries=1)[0]
            assert log.status == "FAILED"
            assert log.response_status_code == 500

            db.refresh(sub)
            assert sub.failure_count == 1
            assert sub.is_active is True

            # Advance failure count to 9 to test auto-deactivation on 10th
            sub.failure_count = 9
            db.commit()

            log2 = dispatcher.dispatch_event("hs.sync.completed", {"status": "ok"}, max_retries=1)[0]
            db.refresh(sub)
            assert sub.failure_count == 10
            assert sub.is_active is False
    finally:
        dispatcher.delete_subscription(sub.subscription_id)


def test_fastapi_webhook_api():
    client = TestClient(app)

    # 1. Create subscription via REST API
    res = client.post("/v1/webhooks/subscriptions", json={
        "name": "api-sub-1",
        "target_url": "https://client.api/webhook",
        "event_types": ["hs.tariff.changed"],
        "secret_token": "api-token-secret"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "api-sub-1"
    sub_id = data["subscription_id"]

    # 2. List subscriptions
    res = client.get("/v1/webhooks/subscriptions")
    assert res.status_code == 200
    assert any(s["subscription_id"] == sub_id for s in res.json())

    # 3. Test ping endpoint (mocking internal _send_to_subscriber)
    mock_log = WebhookDeliveryLog(
        delivery_id="del_12345",
        subscription_id=sub_id,
        event_type="hs.ping.test",
        event_id="evt_123",
        payload_json={"test": True},
        response_status_code=200,
        response_body="pong",
        duration_ms=15,
        status="SUCCESS"
    )
    with patch.object(WebhookDispatcher, "test_subscription", return_value=mock_log):
        res = client.post(f"/v1/webhooks/subscriptions/{sub_id}/test")
        assert res.status_code == 200
        assert res.json()["status"] == "SUCCESS"
        assert res.json()["delivery_id"] == "del_12345"

    # 4. Inbound webhook trigger
    res = client.post("/v1/webhooks/trigger", json={
        "scope": "vietnam-core",
        "source_id": "VN_GOV_LEGAL"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "triggered"

    # 5. Delete subscription
    res = client.delete(f"/v1/webhooks/subscriptions/{sub_id}")
    assert res.status_code == 200
    assert res.json()["status"] == "deleted"


def test_cli_webhook_commands():
    runner = CliRunner()

    # 1. Add subscription
    result = runner.invoke(cli_app, [
        "webhook", "add", "cli-odoo-erp", "https://erp.internal/webhook",
        "--events", "hs.legal_doc.promulgated,hs.ruling.published",
        "--secret", "cli-secret-123"
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    sub_id = data["subscription_id"]
    assert data["name"] == "cli-odoo-erp"

    # 2. List
    result = runner.invoke(cli_app, ["webhook", "list"])
    assert result.exit_code == 0
    subs = json.loads(result.output)
    assert any(s["subscription_id"] == sub_id for s in subs)

    # 3. Remove
    result = runner.invoke(cli_app, ["webhook", "remove", sub_id])
    assert result.exit_code == 0
    del_res = json.loads(result.output)
    assert del_res["status"] == "deleted"
