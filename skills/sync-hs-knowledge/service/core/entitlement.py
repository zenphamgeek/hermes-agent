"""Entitlement management and license readiness reporting."""

from datetime import date
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from service.db.models import Entitlement
from .registry import SourceRegistry


class LicenseReadinessItem(BaseModel):
    source_id: str
    source_name: str
    policy: str
    content_classes: List[str]
    entitlement_status: str  # ACTIVE, PENDING_ENTITLEMENT, EXPIRED, NOT_REQUIRED
    valid_to: Optional[date] = None
    ready_for_full_sync: bool


class EntitlementManager:
    def __init__(self, registry: SourceRegistry):
        self.registry = registry

    def get_readiness_report(self, db: Optional[Session] = None) -> List[LicenseReadinessItem]:
        report = []
        for source in self.registry.list_sources():
            policy = source.license.policy
            entitlement_required = source.license.entitlement_required

            if not entitlement_required:
                report.append(LicenseReadinessItem(
                    source_id=source.id,
                    source_name=source.name,
                    policy=policy,
                    content_classes=source.content_classes,
                    entitlement_status="NOT_REQUIRED",
                    valid_to=None,
                    ready_for_full_sync=True
                ))
                continue

            entitlement = None
            if db:
                entitlement = db.query(Entitlement).filter_by(source_id=source.id, status="ACTIVE").first()

            if entitlement:
                today = date.today()
                is_valid = entitlement.valid_to is None or entitlement.valid_to >= today
                report.append(LicenseReadinessItem(
                    source_id=source.id,
                    source_name=source.name,
                    policy=policy,
                    content_classes=source.content_classes,
                    entitlement_status="ACTIVE" if is_valid else "EXPIRED",
                    valid_to=entitlement.valid_to,
                    ready_for_full_sync=is_valid
                ))
            else:
                report.append(LicenseReadinessItem(
                    source_id=source.id,
                    source_name=source.name,
                    policy=policy,
                    content_classes=source.content_classes,
                    entitlement_status="PENDING_ENTITLEMENT",
                    valid_to=None,
                    ready_for_full_sync=False
                ))

        return report
