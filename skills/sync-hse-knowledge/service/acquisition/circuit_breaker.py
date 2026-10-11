"""Host-level Circuit Breaker Manager (FR-008)."""

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from service.config import settings
from service.db.models import CircuitBreaker


class CircuitBreakerManager:
    def __init__(self, error_threshold: int = 5, cooldown_seconds: int = 60):
        self.error_threshold = error_threshold
        self.cooldown_seconds = cooldown_seconds

    def record_failure(self, host: str, reason: str, db: Session) -> CircuitBreaker:
        breaker = db.query(CircuitBreaker).filter_by(host=host).first()
        now = datetime.now(timezone.utc)
        if not breaker:
            breaker = CircuitBreaker(
                host=host,
                state="CLOSED",
                consecutive_failures=1,
                trip_reason=reason
            )
            db.add(breaker)
        else:
            breaker.consecutive_failures += 1
            if breaker.consecutive_failures >= self.error_threshold:
                breaker.state = "OPEN"
                breaker.trip_reason = reason
                breaker.last_tripped_at = now
                breaker.probe_due_at = now + timedelta(seconds=self.cooldown_seconds)

        db.commit()
        return breaker

    def record_success(self, host: str, db: Session) -> None:
        breaker = db.query(CircuitBreaker).filter_by(host=host).first()
        if breaker:
            breaker.consecutive_failures = 0
            breaker.state = "CLOSED"
            breaker.trip_reason = None
            breaker.last_tripped_at = None
            breaker.probe_due_at = None
            db.commit()

    def is_available(self, host: str, db: Session) -> bool:
        breaker = db.query(CircuitBreaker).filter_by(host=host).first()
        if not breaker or breaker.state == "CLOSED":
            return True
        if breaker.state == "OPEN":
            now = datetime.now(timezone.utc)
            if breaker.probe_due_at and now >= breaker.probe_due_at.replace(tzinfo=timezone.utc):
                breaker.state = "HALF_OPEN"
                db.commit()
                return True
            return False
        return True  # HALF_OPEN allows single probe
