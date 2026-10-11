"""HTTP Response Classification engine (FR-022)."""

from enum import Enum
from typing import Dict, Any, Optional
import httpx


class ResponseClass(str, Enum):
    SUCCESS = "SUCCESS"
    NOT_MODIFIED = "NOT_MODIFIED"
    TRANSIENT = "TRANSIENT"
    RATE_LIMIT = "RATE_LIMIT"
    JS_REQUIRED = "JS_REQUIRED"
    INTERACTIVE_CHALLENGE = "INTERACTIVE_CHALLENGE"
    AUTH_REVOKED = "AUTH_REVOKED"
    PERMANENT_NOT_FOUND = "PERMANENT_NOT_FOUND"
    POLICY_DENIED = "POLICY_DENIED"
    PARSER_DRIFT = "PARSER_DRIFT"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class ResponseClassifier:
    CHALLENGE_INDICATORS = [
        "cf-chl-bypass",
        "cf-turnstile",
        "challenges.cloudflare.com",
        "just a moment...",
        "ddos protection by cloudflare",
        "attention required! | cloudflare",
        "recaptcha",
        "hcaptcha"
    ]

    JS_INDICATORS = [
        "you need to enable javascript",
        "please turn javascript on",
        "noscript"
    ]

    @classmethod
    def classify(
        cls,
        status_code: Optional[int],
        headers: Dict[str, str],
        body_text: Optional[str] = None
    ) -> ResponseClass:
        headers_lower = {k.lower(): v.lower() for k, v in headers.items()}
        text_lower = (body_text or "").lower()

        # Check for 304 Not Modified
        if status_code == 304:
            return ResponseClass.NOT_MODIFIED

        # Check for interactive managed challenge (FR-023)
        if status_code in (403, 503, 429) or "cf-mitigated" in headers_lower:
            for ind in cls.CHALLENGE_INDICATORS:
                if ind in text_lower or ind in str(headers_lower):
                    return ResponseClass.INTERACTIVE_CHALLENGE

        # Check 429 Rate Limit
        if status_code == 429:
            return ResponseClass.RATE_LIMIT

        # Check 401 / 403 Auth
        if status_code == 401:
            return ResponseClass.AUTH_REVOKED
        if status_code == 403:
            return ResponseClass.POLICY_DENIED

        # Check 404
        if status_code == 404:
            return ResponseClass.PERMANENT_NOT_FOUND

        # Check 5xx Transient
        if status_code and 500 <= status_code <= 599:
            return ResponseClass.TRANSIENT

        # Check 200 Success & JS dependency
        if status_code and 200 <= status_code < 300:
            for ind in cls.JS_INDICATORS:
                if ind in text_lower and len(text_lower) < 1000:
                    return ResponseClass.JS_REQUIRED
            return ResponseClass.SUCCESS

        return ResponseClass.UNKNOWN_ERROR
