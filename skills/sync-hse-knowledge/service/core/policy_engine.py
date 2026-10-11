"""Pre-fetch Policy Evaluation Engine (FR-002, FR-004, FR-005)."""

from enum import Enum
from urllib.parse import urlparse
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from service.core.registry import SourceRegistry, SourceDefinition
from service.db.models import Entitlement, CircuitBreaker


class PolicyDecisionType(str, Enum):
    ALLOWED = "ALLOWED"
    DENIED_UNALLOWED_HOST = "DENIED_UNALLOWED_HOST"
    DENIED_LICENSE_REQUIRED = "DENIED_LICENSE_REQUIRED"
    DENIED_CIRCUIT_BREAKER = "DENIED_CIRCUIT_BREAKER"
    DENIED_URL_PATTERN = "DENIED_URL_PATTERN"
    DENIED_PRIVACY_RESTRICTION = "DENIED_PRIVACY_RESTRICTION"


class PolicyDecision(BaseModel):
    decision: PolicyDecisionType
    source_id: str
    target_url: str
    reason: Optional[str] = None
    allowed: bool = False


class PolicyEngine:
    def __init__(self, registry: SourceRegistry):
        self.registry = registry

    def evaluate_request(
        self,
        source_id: str,
        target_url: str,
        content_class: str,
        db: Session
    ) -> PolicyDecision:
        source = self.registry.get_source(source_id)
        if not source:
            return PolicyDecision(
                decision=PolicyDecisionType.DENIED_UNALLOWED_HOST,
                source_id=source_id,
                target_url=target_url,
                reason=f"Source ID '{source_id}' not found in registry"
            )

        # 1. Host Allowlist Check
        parsed = urlparse(target_url)
        host = parsed.netloc.split(":")[0].lower()
        if host not in [h.lower() for h in source.allowed_hosts]:
            return PolicyDecision(
                decision=PolicyDecisionType.DENIED_UNALLOWED_HOST,
                source_id=source_id,
                target_url=target_url,
                reason=f"Host '{host}' is outside allowed_hosts: {source.allowed_hosts}"
            )

        # 2. License & Entitlement Check
        if source.license.policy == "LICENSE_REQUIRED":
            entitlement = db.query(Entitlement).filter_by(source_id=source_id, is_active=True).first()
            if not entitlement or not entitlement.storage_allowed:
                return PolicyDecision(
                    decision=PolicyDecisionType.DENIED_LICENSE_REQUIRED,
                    source_id=source_id,
                    target_url=target_url,
                    reason=f"Source '{source_id}' requires commercial entitlement which is missing or pending"
                )

        # 3. Circuit Breaker Check
        breaker = db.query(CircuitBreaker).filter_by(host=host).first()
        if breaker and breaker.state == "OPEN":
            return PolicyDecision(
                decision=PolicyDecisionType.DENIED_CIRCUIT_BREAKER,
                source_id=source_id,
                target_url=target_url,
                reason=f"Circuit breaker is OPEN for host '{host}' (Trip reason: {breaker.trip_reason})"
            )

        # 4. Prohibited URL Pattern Check
        prohibited_keywords = ["login", "signin", "admin", "wp-admin", "cart", "checkout", "auth"]
        path_lower = parsed.path.lower()
        if any(keyword in path_lower for keyword in prohibited_keywords):
            return PolicyDecision(
                decision=PolicyDecisionType.DENIED_URL_PATTERN,
                source_id=source_id,
                target_url=target_url,
                reason=f"Target URL path '{parsed.path}' matches prohibited pattern"
            )

        return PolicyDecision(
            decision=PolicyDecisionType.ALLOWED,
            source_id=source_id,
            target_url=target_url,
            allowed=True
        )
