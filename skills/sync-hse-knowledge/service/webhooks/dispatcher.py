"""Outbound HMAC-SHA256 Webhook Event Hub for HSE Events."""

import hmac
import hashlib
import json
import time
from typing import Dict, Any, List, Optional
import httpx
from pydantic import BaseModel
from sqlalchemy.orm import Session

from service.config import settings
from service.db.models import WebhookSubscription, WebhookDeliveryLog


class HSEEvent(BaseModel):
    event_id: str
    event_type: str  # hse.law.promulgated, hse.obligation.changed, hse.chemical.updated, hse.sync.completed
    timestamp: str
    data: Dict[str, Any]


class WebhookDispatcher:
    def __init__(self, db: Session):
        self.db = db

    def sign_payload(self, payload_bytes: bytes, secret: str) -> str:
        return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    def dispatch_event(self, event: HSEEvent) -> List[WebhookDeliveryLog]:
        subs = self.db.query(WebhookSubscription).filter_by(is_active=True).all()
        deliveries = []

        payload_dict = event.model_dump()
        payload_bytes = json.dumps(payload_dict, ensure_ascii=False).encode("utf-8")

        for sub in subs:
            if event.event_type not in sub.event_types and "*" not in sub.event_types:
                continue

            sig = self.sign_payload(payload_bytes, sub.secret_token)
            headers = {
                "Content-Type": "application/json",
                "X-HSE-Event": event.event_type,
                "X-HSE-Signature": f"sha256={sig}",
                "X-HSE-Timestamp": str(int(time.time()))
            }

            status_code = None
            resp_body = ""
            is_success = False

            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(sub.target_url, content=payload_bytes, headers=headers)
                    status_code = resp.status_code
                    resp_body = resp.text[:500]
                    is_success = (200 <= resp.status_code < 300)
            except Exception as e:
                resp_body = str(e)
                is_success = False

            log = WebhookDeliveryLog(
                subscription_id=sub.subscription_id,
                event_type=event.event_type,
                payload_json=payload_dict,
                status_code=status_code,
                response_body=resp_body,
                is_success=is_success
            )
            self.db.add(log)
            deliveries.append(log)

        self.db.commit()
        return deliveries
