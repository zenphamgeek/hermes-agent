"""Circuit breaker state manager and health probe dispatcher (FR-026)."""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional
from sqlalchemy.orm import Session

from service.db.models import CircuitBreaker


class BreakerState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerManager:
    def __init__(self, failure_threshold: int = 8, cooldown_minutes: int = 30):
        self.failure_threshold = failure_threshold
        self.cooldown_minutes = cooldown_minutes

    def get_or_create(self, source_id: str, db: Session) -> CircuitBreaker:
        breaker = db.query(CircuitBreaker).filter_by(source_id=source_id).first()
        if not breaker:
            breaker = CircuitBreaker(
                source_id=source_id,
                state=BreakerState.CLOSED.value,
                consecutive_failures=0
            )
            db.add(breaker)
            db.commit()
            db.refresh(breaker)
        return breaker

    def record_success(self, source_id: str, db: Session):
        breaker = self.get_or_create(source_id, db)
        breaker.state = BreakerState.CLOSED.value
        breaker.consecutive_failures = 0
        breaker.probe_due_at = None
        db.commit()

    def record_failure(self, source_id: str, db: Session):
        breaker = self.get_or_create(source_id, db)
        breaker.consecutive_failures += 1
        breaker.last_failure_at = datetime.now(timezone.utc)

        if breaker.consecutive_failures >= self.failure_threshold:
            breaker.state = BreakerState.OPEN.value
            breaker.probe_due_at = datetime.now(timezone.utc) + timedelta(minutes=self.cooldown_minutes)

        db.commit()

    def can_attempt(self, source_id: str, db: Session) -> bool:
        breaker = self.get_or_create(source_id, db)
        if breaker.state == BreakerState.CLOSED.value:
            return True

        if breaker.state == BreakerState.OPEN.value:
            now = datetime.now(timezone.utc)
            if breaker.probe_due_at and now >= breaker.probe_due_at.replace(tzinfo=timezone.utc):
                breaker.state = BreakerState.HALF_OPEN.value
                db.commit()
                return True
            return False

        if breaker.state == BreakerState.HALF_OPEN.value:
            return True

        return False
