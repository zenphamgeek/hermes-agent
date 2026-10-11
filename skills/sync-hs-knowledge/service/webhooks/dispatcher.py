"""Webhook Event Dispatcher and Subscription Management (SRS Event Hub)."""

import hmac
import hashlib
import json
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple, Union

import httpx
from sqlalchemy.orm import Session
from service.db.models import WebhookSubscription, WebhookDeliveryLog

logger = logging.getLogger(__name__)


def compute_signature(payload: Union[str, bytes], secret: Union[str, bytes]) -> str:
    """Computes HMAC-SHA256 signature for payload."""
    payload_bytes = payload.encode("utf-8") if isinstance(payload, str) else payload
    secret_bytes = secret.encode("utf-8") if isinstance(secret, str) else secret
    sig = hmac.new(secret_bytes, payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def verify_signature(payload: Union[str, bytes], secret: str, signature_header: str) -> bool:
    """Verifies HMAC-SHA256 signature using constant-time comparison."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = compute_signature(payload, secret)
    return hmac.compare_digest(expected, signature_header)


class WebhookDispatcher:
    def __init__(self, db: Session, client: Optional[httpx.Client] = None):
        self.db = db
        self.client = client or httpx.Client(timeout=10.0)

    def create_subscription(
        self,
        name: str,
        target_url: str,
        event_types: Optional[List[str]] = None,
        secret_token: Optional[str] = None
    ) -> WebhookSubscription:
        """Creates a new webhook subscription."""
        if not secret_token:
            secret_token = f"whsec_{uuid.uuid4().hex}"
        if not event_types:
            event_types = ["*"]

        sub = WebhookSubscription(
            name=name,
            target_url=target_url,
            secret_token=secret_token,
            event_types=event_types,
            is_active=True,
            failure_count=0
        )
        self.db.add(sub)
        self.db.commit()
        self.db.refresh(sub)
        logger.info("Created WebhookSubscription id=%s name=%s target=%s", sub.subscription_id, name, target_url)
        return sub

    def list_subscriptions(self, active_only: bool = False) -> List[WebhookSubscription]:
        """Lists registered webhook subscriptions."""
        q = self.db.query(WebhookSubscription)
        if active_only:
            q = q.filter_by(is_active=True)
        return q.order_by(WebhookSubscription.created_at.desc()).all()

    def delete_subscription(self, subscription_id: str) -> bool:
        """Deletes a webhook subscription by ID."""
        sub = self.db.query(WebhookSubscription).filter_by(subscription_id=subscription_id).first()
        if not sub:
            return False
        self.db.delete(sub)
        self.db.commit()
        logger.info("Deleted WebhookSubscription id=%s", subscription_id)
        return True

    def dispatch_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        max_retries: int = 3
    ) -> List[WebhookDeliveryLog]:
        """Dispatches an event payload to all matching active subscribers."""
        # Find matching subscriptions
        subscriptions = self.db.query(WebhookSubscription).filter_by(is_active=True).all()
        matching_subs = [
            s for s in subscriptions
            if "*" in (s.event_types or []) or event_type in (s.event_types or [])
        ]

        if not matching_subs:
            return []

        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        timestamp_iso = datetime.now(timezone.utc).isoformat()
        epoch_ts = str(int(time.time()))

        payload_dict = {
            "event_id": event_id,
            "event_type": event_type,
            "timestamp": timestamp_iso,
            "data": data
        }
        payload_bytes = json.dumps(payload_dict, ensure_ascii=False).encode("utf-8")

        delivery_logs = []
        for sub in matching_subs:
            log = self._send_to_subscriber(sub, event_type, event_id, payload_dict, payload_bytes, epoch_ts, max_retries)
            delivery_logs.append(log)

        return delivery_logs

    def test_subscription(self, subscription_id: str) -> WebhookDeliveryLog:
        """Sends a ping test event to a specific subscription."""
        sub = self.db.query(WebhookSubscription).filter_by(subscription_id=subscription_id).first()
        if not sub:
            raise ValueError(f"Webhook subscription '{subscription_id}' not found")

        test_data = {
            "message": "Ping test from HS Knowledge Sync Skill",
            "subscription_id": sub.subscription_id,
            "subscription_name": sub.name,
            "ping_time": datetime.now(timezone.utc).isoformat()
        }
        event_id = f"ping_{uuid.uuid4().hex[:8]}"
        epoch_ts = str(int(time.time()))
        payload_dict = {
            "event_id": event_id,
            "event_type": "hs.ping.test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": test_data
        }
        payload_bytes = json.dumps(payload_dict, ensure_ascii=False).encode("utf-8")

        return self._send_to_subscriber(sub, "hs.ping.test", event_id, payload_dict, payload_bytes, epoch_ts, max_retries=1)

    def _send_to_subscriber(
        self,
        sub: WebhookSubscription,
        event_type: str,
        event_id: str,
        payload_dict: Dict[str, Any],
        payload_bytes: bytes,
        epoch_ts: str,
        max_retries: int = 3
    ) -> WebhookDeliveryLog:
        """Sends signed payload with retry logic."""
        signature = compute_signature(payload_bytes, sub.secret_token)
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "Hermes-HS-Knowledge-Sync/1.1",
            "X-HS-Event": event_type,
            "X-HS-Delivery-ID": event_id,
            "X-HS-Timestamp": epoch_ts,
            "X-HS-Signature-256": signature
        }

        status = "FAILED"
        status_code = None
        response_body = ""
        duration_ms = 0
        attempt = 1

        for attempt in range(1, max_retries + 1):
            t0 = time.time()
            try:
                resp = self.client.post(sub.target_url, content=payload_bytes, headers=headers)
                duration_ms = int((time.time() - t0) * 1000)
                status_code = resp.status_code
                response_body = resp.text[:500] if resp.text else ""

                if 200 <= resp.status_code < 300:
                    status = "SUCCESS"
                    sub.failure_count = 0
                    break
                else:
                    status = "FAILED"
                    if resp.status_code >= 500 and attempt < max_retries:
                        time.sleep(0.05 * (2 ** (attempt - 1)))  # Exponential backoff
            except Exception as exc:
                duration_ms = int((time.time() - t0) * 1000)
                response_body = f"Connection error: {str(exc)}"
                status = "FAILED"
                if attempt < max_retries:
                    time.sleep(0.05 * (2 ** (attempt - 1)))

        if status == "FAILED":
            sub.failure_count += 1
            if sub.failure_count >= 10:
                sub.is_active = False
                logger.warning("Subscription id=%s deactivated after 10 consecutive failures", sub.subscription_id)

        log = WebhookDeliveryLog(
            subscription_id=sub.subscription_id,
            event_type=event_type,
            event_id=event_id,
            payload_json=payload_dict,
            response_status_code=status_code,
            response_body=response_body,
            duration_ms=duration_ms,
            attempt_number=attempt,
            status=status
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
