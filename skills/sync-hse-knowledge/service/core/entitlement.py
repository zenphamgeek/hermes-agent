"""Entitlement and license contract manager."""

from datetime import date
from typing import Optional, List
from sqlalchemy.orm import Session

from service.db.models import Entitlement


class EntitlementManager:
    def __init__(self, db: Session):
        self.db = db

    def register_entitlement(
        self,
        source_id: str,
        contract_ref: str,
        effective_from: date,
        effective_to: date,
        storage_allowed: bool = True,
        embedding_allowed: bool = True,
        redistribution_allowed: bool = False,
        excerpt_limit_chars: int = 500
    ) -> Entitlement:
        ent = Entitlement(
            source_id=source_id,
            license_contract_ref=contract_ref,
            effective_from=effective_from,
            effective_to=effective_to,
            storage_allowed=storage_allowed,
            embedding_allowed=embedding_allowed,
            redistribution_allowed=redistribution_allowed,
            excerpt_limit_chars=excerpt_limit_chars,
            is_active=True
        )
        self.db.add(ent)
        self.db.commit()
        return ent

    def is_entitled(self, source_id: str) -> bool:
        ent = self.db.query(Entitlement).filter_by(source_id=source_id, is_active=True).first()
        if not ent:
            return False
        today = date.today()
        return ent.effective_from <= today <= ent.effective_to and ent.storage_allowed
