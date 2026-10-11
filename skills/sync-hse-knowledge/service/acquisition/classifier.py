"""HTTP Response Classifier (FR-007, FR-009, Section 18.2)."""

from enum import Enum
from typing import Optional, Dict


class ResponseClass(str, Enum):
    SUCCESS = "SUCCESS"
    NOT_MODIFIED = "NOT_MODIFIED"
    TRANSIENT = "TRANSIENT"  # 500, 502, 503, 504, Connection Reset, Timeout
    RATE_LIMIT = "RATE_LIMIT"  # 429
    JS_REQUIRED = "JS_REQUIRED"  # Needs browser rendering
    INTERACTIVE_CHALLENGE = "INTERACTIVE_CHALLENGE"  # Cloudflare Turnstile, CAPTCHA
    AUTH_REVOKED = "AUTH_REVOKED"  # 401, 403 (unauthorized)
    NOT_FOUND = "NOT_FOUND"  # 404, 410
    POLICY_DENIED = "POLICY_DENIED"
    PARSER_DRIFT = "PARSER_DRIFT"


class ResponseClassifier:
    @staticmethod
    def classify(
        status_code: Optional[int],
        headers: Optional[Dict[str, str]] = None,
        body_text: Optional[str] = None,
        exception: Optional[Exception] = None
    ) -> ResponseClass:
        headers = headers or {}
        body = (body_text or "").lower()

        # Check interactive challenges
        if "cf-turnstile" in body or "challenges.cloudflare.com" in body or "hcaptcha" in body or "g-recaptcha" in body:
            return ResponseClass.INTERACTIVE_CHALLENGE

        # Status code routing
        if status_code == 200:
            if "<div id=\"root\"></div>" in body and len(body) < 500:
                return ResponseClass.JS_REQUIRED
            return ResponseClass.SUCCESS
        elif status_code == 304:
            return ResponseClass.NOT_MODIFIED
        elif status_code == 429:
            return ResponseClass.RATE_LIMIT
        elif status_code in (401, 403):
            if "cf-mitigated" in headers.get("server", "").lower() or "challenge" in body:
                return ResponseClass.INTERACTIVE_CHALLENGE
            return ResponseClass.AUTH_REVOKED
        elif status_code in (404, 410):
            return ResponseClass.NOT_FOUND
        elif status_code in (500, 502, 503, 504):
            return ResponseClass.TRANSIENT
        elif exception:
            return ResponseClass.TRANSIENT

        return ResponseClass.SUCCESS
