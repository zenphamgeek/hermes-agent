"""Adaptive Retry Engine with Decorrelated Jitter and Retry Budget (FR-007)."""

import random
import time
from typing import Optional, Dict
from sqlalchemy.orm import Session

from service.db.models import RetryBudget


class AdaptiveRetryEngine:
    def __init__(self, base_delay: float = 1.0, max_delay: float = 30.0):
        self.base_delay = base_delay
        self.max_delay = max_delay

    def calculate_backoff(self, attempt_count: int, previous_delay: float = 1.0) -> float:
        """Decorrelated Jitter Backoff (Full Jitter algorithm)."""
        temp = min(self.max_delay, self.base_delay * 2 ** attempt_count)
        sleep_duration = temp / 2 + random.uniform(0, temp / 2)
        return min(self.max_delay, sleep_duration)

    def parse_retry_after(self, headers: Optional[Dict[str, str]]) -> Optional[float]:
        if not headers:
            return None
        retry_after = headers.get("retry-after") or headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return None

    def consume_retry_budget(self, host: str, db: Session, cost: float = 1.0) -> bool:
        budget = db.query(RetryBudget).filter_by(host=host).first()
        if not budget:
            budget = RetryBudget(host=host, max_tokens=100, available_tokens=100.0)
            db.add(budget)
            db.commit()

        if budget.available_tokens >= cost:
            budget.available_tokens -= cost
            db.commit()
            return True
        return False
