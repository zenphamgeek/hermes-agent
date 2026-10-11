"""Source Registry parser, schema validator and database synchronizer."""

from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from service.config import settings
from service.db.models import Source


class DiscoveryConfig(BaseModel):
    start_urls: List[str]
    strategies: List[str]


class FetchConfig(BaseModel):
    rate_limit_rps: float = 1.0
    concurrency: int = 2
    timeout_seconds: int = 30
    retries: int = 3
    honor_robots_txt: bool = True
    conditional_requests: bool = True


class AcquisitionConfig(BaseModel):
    unattended_required: bool = True
    preferred_channels: List[str]
    sanctioned_fallback_sources: List[str] = Field(default_factory=list)
    interactive_challenge_action: str = "quarantine_and_fallback"


class LicenseConfig(BaseModel):
    policy: str  # PUBLIC_DOWNLOAD, PUBLIC_METADATA_ONLY, LICENSE_REQUIRED, INTERNAL_AUTHORIZED
    entitlement_required: bool = False


class PrivacyConfig(BaseModel):
    data_class: str = "public_knowledge"


class SourceDefinition(BaseModel):
    id: str
    name: str
    jurisdiction: str
    authority_level: str
    allowed_hosts: List[str]
    content_classes: List[str]
    discovery: DiscoveryConfig
    fetch: FetchConfig
    acquisition: AcquisitionConfig
    license: LicenseConfig
    privacy: PrivacyConfig
    parsers: List[str]
    schedule: Dict[str, str]


class SourceRegistry:
    def __init__(self, sources: List[SourceDefinition]):
        self._sources = {s.id: s for s in sources}

    def list_sources(self) -> List[SourceDefinition]:
        return list(self._sources.values())

    def get_source(self, source_id: str) -> Optional[SourceDefinition]:
        return self._sources.get(source_id)

    def validate(self) -> List[str]:
        errors = []
        for s in self._sources.values():
            if not s.allowed_hosts:
                errors.append(f"Source {s.id} missing allowed_hosts")
            if s.license.policy == "LICENSE_REQUIRED" and not s.license.entitlement_required:
                errors.append(f"Source {s.id} is LICENSE_REQUIRED but entitlement_required is False")
            if s.fetch.rate_limit_rps <= 0:
                errors.append(f"Source {s.id} invalid rate_limit_rps")
        return errors

    def sync_to_db(self, db: Session) -> int:
        count = 0
        for s in self._sources.values():
            existing = db.query(Source).filter_by(source_id=s.id).first()
            if not existing:
                src_obj = Source(
                    source_id=s.id,
                    name=s.name,
                    jurisdiction=s.jurisdiction,
                    authority_level=s.authority_level,
                    allowed_hosts=s.allowed_hosts,
                    content_classes=s.content_classes,
                    discovery_config=s.discovery.model_dump(),
                    fetch_config=s.fetch.model_dump(),
                    acquisition_config=s.acquisition.model_dump(),
                    license_policy=s.license.policy,
                    entitlement_required=s.license.entitlement_required,
                    privacy_class=s.privacy.data_class
                )
                db.add(src_obj)
                count += 1
            else:
                existing.name = s.name
                existing.allowed_hosts = s.allowed_hosts
                existing.content_classes = s.content_classes
                existing.license_policy = s.license.policy
                existing.entitlement_required = s.license.entitlement_required
        db.commit()
        return count


def load_source_registry(catalog_path: Optional[Path] = None) -> SourceRegistry:
    path = catalog_path or settings.source_registry_path
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    sources = [SourceDefinition(**s) for s in data.get("sources", [])]
    return SourceRegistry(sources)
