"""Adaptive Retry Engine with exponential backoff, decorrelated jitter, and budget tracking (FR-017, FR-025)."""

import random
import time
from typing import Optional, Dict
from pydantic import BaseModel

from .classifier import ResponseClass


class RetryDecision(BaseModel):
    should_retry: bool
    delay_seconds: float
    reason: str


class AdaptiveRetryEngine:
    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0, max_retries: int = 4):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries

    def compute_retry(
        self,
        attempt_number: int,
        response_class: ResponseClass,
        headers: Dict[str, str],
        budget_remaining: int = 10
    ) -> RetryDecision:
        if attempt_number >= self.max_retries:
            return RetryDecision(
                should_retry=False,
                delay_seconds=0.0,
                reason=f"Exceeded max retry limit ({self.max_retries})"
            )

        if budget_remaining <= 0:
            return RetryDecision(
                should_retry=False,
                delay_seconds=0.0,
                reason="Retry budget exhausted for current run window"
            )

        # Permanent failure classes - DO NOT RETRY (FR-017)
        if response_class in (
            ResponseClass.AUTH_REVOKED,
            ResponseClass.POLICY_DENIED,
            ResponseClass.PERMANENT_NOT_FOUND,
            ResponseClass.INTERACTIVE_CHALLENGE
        ):
            return RetryDecision(
                should_retry=False,
                delay_seconds=0.0,
                reason=f"Permanent failure condition: {response_class.value}"
            )

        # Check Retry-After header
        retry_after = headers.get("retry-after") or headers.get("Retry-After")
        if retry_after:
            try:
                delay = float(retry_after)
                return RetryDecision(
                    should_retry=True,
                    delay_seconds=min(delay, self.max_delay),
                    reason=f"Server Retry-After header: {delay}s"
                )
            except ValueError:
                pass

        # Exponential backoff with decorrelated jitter
        backoff = self.base_delay * (2 ** (attempt_number - 1))
        jitter = random.uniform(0.5, 1.5)
        delay = min(self.max_delay, backoff * jitter)

        return RetryDecision(
            should_retry=True,
            delay_seconds=delay,
            reason=f"Exponential backoff (attempt {attempt_number})"
        )
