"""Pre-fetch policy decision engine."""

from enum import Enum
from typing import Optional, List
from urllib.parse import urlparse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from service.db.models import CircuitBreaker, Entitlement
from .registry import SourceDefinition, SourceRegistry


class PolicyDecisionType(str, Enum):
    ALLOW_FULL = "ALLOW_FULL"
    ALLOW_METADATA_ONLY = "ALLOW_METADATA_ONLY"
    LICENSE_REQUIRED = "LICENSE_REQUIRED"
    QUARANTINED = "QUARANTINED"
    DENIED_UNALLOWED_HOST = "DENIED_UNALLOWED_HOST"
    DENIED_URL_PATTERN = "DENIED_URL_PATTERN"
    DENIED_ROBOTS = "DENIED_ROBOTS"
    DENIED = "DENIED"


class PolicyDecision(BaseModel):
    source_id: str
    target_url: str
    decision: PolicyDecisionType
    reason: str
    can_fetch_content: bool
    can_store_raw: bool
    can_embed: bool


class PolicyEngine:
    def __init__(self, registry: SourceRegistry):
        self.registry = registry

    def is_host_allowed(self, host: str, allowed_hosts: List[str]) -> bool:
        """Matches host against allowed host patterns."""
        for pattern in allowed_hosts:
            if pattern == host:
                return True
            if pattern.startswith("*."):
                suffix = pattern[1:]
                if host.endswith(suffix):
                    return True
            if pattern.startswith("kv*."):
                if host.startswith("kv") and host.endswith(pattern[3:]):
                    return True
        return False

    def evaluate_request(self, source_id: str, url: str, content_class: str, db: Optional[Session] = None) -> PolicyDecision:
        source = self.registry.get_source(source_id)
        if not source:
            return PolicyDecision(
                source_id=source_id,
                target_url=url,
                decision=PolicyDecisionType.DENIED,
                reason=f"Unknown source ID: {source_id}",
                can_fetch_content=False,
                can_store_raw=False,
                can_embed=False
            )

        parsed_url = urlparse(url)
        host = parsed_url.netloc.lower()

        # 1. Host allowlist check (FR-006)
        if not self.is_host_allowed(host, source.allowed_hosts):
            return PolicyDecision(
                source_id=source_id,
                target_url=url,
                decision=PolicyDecisionType.DENIED_UNALLOWED_HOST,
                reason=f"Host '{host}' is outside allowed hosts for source {source_id}",
                can_fetch_content=False,
                can_store_raw=False,
                can_embed=False
            )

        # 2. Denied URL pattern check
        for pattern in source.denied_url_patterns:
            clean_pat = pattern.replace("*", "")
            if clean_pat and clean_pat in url:
                return PolicyDecision(
                    source_id=source_id,
                    target_url=url,
                    decision=PolicyDecisionType.DENIED_URL_PATTERN,
                    reason=f"URL matches denied pattern '{pattern}'",
                    can_fetch_content=False,
                    can_store_raw=False,
                    can_embed=False
                )

        # 3. Circuit breaker check
        if db:
            breaker = db.query(CircuitBreaker).filter_by(source_id=source_id).first()
            if breaker and breaker.state == "OPEN":
                return PolicyDecision(
                    source_id=source_id,
                    target_url=url,
                    decision=PolicyDecisionType.QUARANTINED,
                    reason=f"Source {source_id} circuit breaker is OPEN",
                    can_fetch_content=False,
                    can_store_raw=False,
                    can_embed=False
                )

        # 4. License & Entitlement Policy Check (FR-005)
        policy_state = source.license.policy
        if policy_state == "LICENSE_REQUIRED":
            # Check if active entitlement exists
            has_active_entitlement = False
            if db:
                entitlement = db.query(Entitlement).filter_by(source_id=source_id, status="ACTIVE").first()
                if entitlement:
                    has_active_entitlement = True

            if not has_active_entitlement:
                return PolicyDecision(
                    source_id=source_id,
                    target_url=url,
                    decision=PolicyDecisionType.LICENSE_REQUIRED,
                    reason=f"Content for {source_id} requires an active entitlement",
                    can_fetch_content=False,
                    can_store_raw=False,
                    can_embed=False
                )

        if policy_state == "PUBLIC_METADATA_ONLY":
            return PolicyDecision(
                source_id=source_id,
                target_url=url,
                decision=PolicyDecisionType.ALLOW_METADATA_ONLY,
                reason=f"Source {source_id} is configured for metadata-only storage",
                can_fetch_content=True,
                can_store_raw=False,
                can_embed=False
            )

        return PolicyDecision(
            source_id=source_id,
            target_url=url,
            decision=PolicyDecisionType.ALLOW_FULL,
            reason="Approved under public download policy",
            can_fetch_content=True,
            can_store_raw=True,
            can_embed=True
        )
