"""Source Registry loader and schema validation."""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from service.db.models import Source, SourceEndpoint, SourcePolicy
from service.config import settings


class BrowserRenderConfig(BaseModel):
    enabled: bool = False
    persistent_profile: bool = False
    solve_interactive_challenge: bool = False
    stealth: bool = False
    proxy_rotation: bool = False

    @field_validator("stealth", "solve_interactive_challenge", "proxy_rotation")
    @classmethod
    def validate_prohibited_evasion(cls, v: bool, info) -> bool:
        if v:
            raise ValueError(f"Field {info.field_name} must be false: evasion techniques are prohibited by SRS policy.")
        return v


class AcquisitionConfig(BaseModel):
    unattended_required: bool = True
    preferred_channels: List[str] = Field(default_factory=lambda: ["http"])
    sanctioned_fallback_sources: List[str] = Field(default_factory=list)
    browser_render: Optional[BrowserRenderConfig] = None
    interactive_challenge_action: str = "quarantine_and_fallback"


class FetchConfig(BaseModel):
    rate_limit_rps: float = Field(default=0.5, gt=0.0, le=10.0)
    concurrency: int = Field(default=2, ge=1, le=10)
    timeout_seconds: int = Field(default=60, ge=5, le=300)
    retries: int = Field(default=4, ge=0, le=10)
    honor_robots_txt: bool = True
    conditional_requests: bool = True
    retry_policy: str = "adaptive_v1"
    max_retry_budget_minutes: int = Field(default=120, ge=5)
    circuit_breaker_threshold: int = Field(default=8, ge=1)


class DiscoveryConfig(BaseModel):
    strategies: List[str] = Field(default_factory=lambda: ["paginated_index"])
    start_urls: List[str] = Field(default_factory=list)


class LicenseConfig(BaseModel):
    policy: str = "PUBLIC_DOWNLOAD"  # PUBLIC_DOWNLOAD, PUBLIC_METADATA_ONLY, LICENSE_REQUIRED, LICENSED, INTERNAL_AUTHORIZED
    entitlement_required: bool = False


class SourceDefinition(BaseModel):
    id: str
    name: str
    jurisdiction: str = "VN"
    authority_level: str = "A1_SIGNED_OFFICIAL"
    base_urls: List[str]
    allowed_hosts: List[str]
    discovery: DiscoveryConfig
    allowed_url_patterns: List[str] = Field(default_factory=list)
    denied_url_patterns: List[str] = Field(default_factory=list)
    content_classes: List[str]
    fetch: FetchConfig
    acquisition: AcquisitionConfig
    license: LicenseConfig
    parsers: List[str] = Field(default_factory=lambda: ["html"])
    schedule: Dict[str, str] = Field(default_factory=dict)

    @field_validator("allowed_hosts")
    @classmethod
    def validate_allowed_hosts(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("allowed_hosts must contain at least one host pattern.")
        for host in v:
            if host == "*" or host.count("*") > 1:
                raise ValueError(f"Overly broad wildcard host prohibited: {host}")
        return v

    @field_validator("license")
    @classmethod
    def validate_license_consistency(cls, v: LicenseConfig) -> LicenseConfig:
        if v.policy == "LICENSE_REQUIRED" and not v.entitlement_required:
            raise ValueError("entitlement_required must be true when policy is LICENSE_REQUIRED.")
        return v


class SourceCatalog(BaseModel):
    sources: List[SourceDefinition]


class SourceRegistry:
    def __init__(self, catalog_path: Optional[str] = None):
        self.catalog_path = catalog_path or settings.source_registry_path
        self._sources: Dict[str, SourceDefinition] = {}
        self.load()

    def load(self):
        path = Path(self.catalog_path)
        if not path.exists():
            raise FileNotFoundError(f"Source catalog not found at {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        catalog = SourceCatalog(**data)
        self._sources = {s.id: s for s in catalog.sources}

    def get_source(self, source_id: str) -> Optional[SourceDefinition]:
        return self._sources.get(source_id)

    def list_sources(self) -> List[SourceDefinition]:
        return list(self._sources.values())

    def validate_all(self) -> List[str]:
        """Validates all sources and returns any issues found."""
        issues = []
        for s in self._sources.values():
            if not s.parsers:
                issues.append(f"Source {s.id}: No parser specified.")
            if s.fetch.rate_limit_rps <= 0:
                issues.append(f"Source {s.id}: Invalid rate limit {s.fetch.rate_limit_rps}.")
        return issues

    def sync_to_db(self, db: Session):
        """Syncs in-memory source definitions into the database."""
        for s in self._sources.values():
            db_source = db.query(Source).filter_by(source_id=s.id).first()
            if not db_source:
                db_source = Source(
                    source_id=s.id,
                    name=s.name,
                    jurisdiction=s.jurisdiction,
                    authority_level=s.authority_level,
                    base_urls=s.base_urls,
                    allowed_hosts=s.allowed_hosts,
                    content_classes=s.content_classes,
                    is_active=True
                )
                db.add(db_source)
                db.flush()

                # Add policy
                policy = SourcePolicy(
                    source_id=s.id,
                    policy_state=s.license.policy,
                    entitlement_required=s.license.entitlement_required,
                    honor_robots_txt=s.fetch.honor_robots_txt,
                    conditional_requests=s.fetch.conditional_requests,
                    max_retries=s.fetch.retries,
                    retry_policy=s.fetch.retry_policy,
                    max_retry_budget_minutes=s.fetch.max_retry_budget_minutes,
                    circuit_breaker_threshold=s.fetch.circuit_breaker_threshold
                )
                db.add(policy)

                # Add endpoints
                for start_url in s.discovery.start_urls:
                    endpoint = SourceEndpoint(
                        source_id=s.id,
                        strategy=s.discovery.strategies[0] if s.discovery.strategies else "paginated_index",
                        start_url=start_url,
                        rate_limit_rps=s.fetch.rate_limit_rps,
                        concurrency=s.fetch.concurrency,
                        timeout_seconds=s.fetch.timeout_seconds
                    )
                    db.add(endpoint)
            else:
                db_source.name = s.name
                db_source.base_urls = s.base_urls
                db_source.allowed_hosts = s.allowed_hosts
                db_source.content_classes = s.content_classes
        db.commit()


def load_source_registry(catalog_path: Optional[str] = None) -> SourceRegistry:
    return SourceRegistry(catalog_path)
