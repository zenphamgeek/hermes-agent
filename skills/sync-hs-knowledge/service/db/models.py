"""SQLAlchemy 2.0 ORM Models for HS Knowledge Base."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Index, JSON, Enum
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ==========================================
# 1. Source & Policy Management
# ==========================================

class Source(Base):
    __tablename__ = "source"

    source_id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    jurisdiction = Column(String(32), nullable=False, default="VN")  # VN, ASEAN, INT
    authority_level = Column(String(32), nullable=False)  # A1_SIGNED_OFFICIAL, A2_OFFICIAL_DATABASE, etc.
    base_urls = Column(JSON, nullable=False, default=list)
    allowed_hosts = Column(JSON, nullable=False, default=list)
    content_classes = Column(JSON, nullable=False, default=list)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    policy = relationship("SourcePolicy", back_populates="source", uselist=False, cascade="all, delete-orphan")
    endpoints = relationship("SourceEndpoint", back_populates="source", cascade="all, delete-orphan")


class SourceEndpoint(Base):
    __tablename__ = "source_endpoint"

    endpoint_id = Column(String(64), primary_key=True, default=generate_uuid)
    source_id = Column(String(64), ForeignKey("source.source_id"), nullable=False)
    strategy = Column(String(32), nullable=False)  # sitemap, paginated_index, attachment_links
    start_url = Column(Text, nullable=False)
    url_pattern = Column(Text, nullable=True)
    rate_limit_rps = Column(Float, default=0.5, nullable=False)
    concurrency = Column(Integer, default=2, nullable=False)
    timeout_seconds = Column(Integer, default=60, nullable=False)

    source = relationship("Source", back_populates="endpoints")


class SourcePolicy(Base):
    __tablename__ = "source_policy"

    policy_id = Column(String(64), primary_key=True, default=generate_uuid)
    source_id = Column(String(64), ForeignKey("source.source_id"), nullable=False, unique=True)
    policy_state = Column(String(32), nullable=False, default="PUBLIC_DOWNLOAD")  # PUBLIC_DOWNLOAD, LICENSE_REQUIRED, etc.
    entitlement_required = Column(Boolean, default=False, nullable=False)
    honor_robots_txt = Column(Boolean, default=True, nullable=False)
    conditional_requests = Column(Boolean, default=True, nullable=False)
    max_retries = Column(Integer, default=4, nullable=False)
    retry_policy = Column(String(32), default="adaptive_v1", nullable=False)
    max_retry_budget_minutes = Column(Integer, default=120, nullable=False)
    circuit_breaker_threshold = Column(Integer, default=8, nullable=False)

    source = relationship("Source", back_populates="policy")


class Entitlement(Base):
    __tablename__ = "entitlement"

    entitlement_id = Column(String(64), primary_key=True, default=generate_uuid)
    source_id = Column(String(64), ForeignKey("source.source_id"), nullable=False)
    content_classes = Column(JSON, nullable=False, default=list)
    licensed_entity = Column(String(255), nullable=False)
    license_reference = Column(String(255), nullable=False)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)
    storage_allowed = Column(Boolean, default=True, nullable=False)
    indexing_allowed = Column(Boolean, default=True, nullable=False)
    embedding_allowed = Column(Boolean, default=True, nullable=False)
    redistribution_allowed = Column(Boolean, default=False, nullable=False)
    status = Column(String(32), default="ACTIVE", nullable=False)  # ACTIVE, EXPIRED, REVOKED, PENDING
    created_at = Column(DateTime, default=utc_now, nullable=False)


class RobotsSnapshot(Base):
    __tablename__ = "robots_snapshot"

    snapshot_id = Column(String(64), primary_key=True, default=generate_uuid)
    host = Column(String(255), nullable=False, index=True)
    content_sha256 = Column(String(64), nullable=False)
    content_text = Column(Text, nullable=False)
    fetched_at = Column(DateTime, default=utc_now, nullable=False)


# ==========================================
# 2. Crawl Runs & Checkpoints
# ==========================================

class CrawlRun(Base):
    __tablename__ = "crawl_run"

    run_id = Column(String(64), primary_key=True, default=generate_uuid)
    scope = Column(String(64), nullable=False, default="vietnam-core")
    mode = Column(String(32), nullable=False, default="incremental")  # plan, incremental, full, reparse
    status = Column(String(32), nullable=False, default="RUNNING")  # RUNNING, SUCCEEDED, PARTIAL, FAILED, CANCELLED
    sources_target = Column(JSON, nullable=False, default=list)
    items_discovered = Column(Integer, default=0, nullable=False)
    items_downloaded = Column(Integer, default=0, nullable=False)
    items_unchanged = Column(Integer, default=0, nullable=False)
    items_parsed = Column(Integer, default=0, nullable=False)
    items_normalized = Column(Integer, default=0, nullable=False)
    items_quarantined = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=utc_now, nullable=False)
    finished_at = Column(DateTime, nullable=True)


class CrawlCheckpoint(Base):
    __tablename__ = "crawl_checkpoint"

    checkpoint_id = Column(String(64), primary_key=True, default=generate_uuid)
    run_id = Column(String(64), ForeignKey("crawl_run.run_id"), nullable=False)
    source_id = Column(String(64), ForeignKey("source.source_id"), nullable=False)
    cursor_value = Column(Text, nullable=True)
    last_page = Column(Integer, default=1, nullable=False)
    last_item_url = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class CrawlItem(Base):
    __tablename__ = "crawl_item"

    item_id = Column(String(64), primary_key=True, default=generate_uuid)
    source_id = Column(String(64), ForeignKey("source.source_id"), nullable=False, index=True)
    raw_url = Column(Text, nullable=False)
    canonical_url = Column(Text, nullable=False, index=True)
    content_class = Column(String(64), nullable=False)
    discovered_at = Column(DateTime, default=utc_now, nullable=False)
    last_crawled_at = Column(DateTime, nullable=True)
    status = Column(String(32), default="DISCOVERED", nullable=False)  # DISCOVERED, FETCHED, NOT_MODIFIED, FAILED, QUARANTINED


class FetchAttempt(Base):
    __tablename__ = "fetch_attempt"

    attempt_id = Column(String(64), primary_key=True, default=generate_uuid)
    item_id = Column(String(64), ForeignKey("crawl_item.item_id"), nullable=False)
    channel = Column(String(32), nullable=False)  # official_api, bulk_export, http, browser_render, fallback
    status_code = Column(Integer, nullable=True)
    response_class = Column(String(32), nullable=False)  # SUCCESS, NOT_MODIFIED, TRANSIENT, RATE_LIMIT, JS_REQUIRED, INTERACTIVE_CHALLENGE, AUTH_REVOKED
    etag = Column(String(128), nullable=True)
    last_modified = Column(String(128), nullable=True)
    duration_ms = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=utc_now, nullable=False)


# ==========================================
# 3. Unattended Acquisition & Circuit Breaker
# ==========================================

class AccessContract(Base):
    __tablename__ = "access_contract"

    contract_id = Column(String(64), primary_key=True, default=generate_uuid)
    source_id = Column(String(64), ForeignKey("source.source_id"), nullable=False)
    contract_type = Column(String(32), nullable=False)  # api_token, sftp, ip_allowlist, signed_export
    secret_ref = Column(String(128), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    status = Column(String(32), default="VALID", nullable=False)


class CircuitBreaker(Base):
    __tablename__ = "circuit_breaker"

    breaker_id = Column(String(64), primary_key=True, default=generate_uuid)
    source_id = Column(String(64), ForeignKey("source.source_id"), nullable=False, unique=True)
    state = Column(String(32), default="CLOSED", nullable=False)  # CLOSED, OPEN, HALF_OPEN
    consecutive_failures = Column(Integer, default=0, nullable=False)
    last_failure_at = Column(DateTime, nullable=True)
    probe_due_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class RetryBudget(Base):
    __tablename__ = "retry_budget"

    budget_id = Column(String(64), primary_key=True, default=generate_uuid)
    source_id = Column(String(64), ForeignKey("source.source_id"), nullable=False)
    attempts_used = Column(Integer, default=0, nullable=False)
    max_budget_minutes = Column(Integer, default=120, nullable=False)
    window_started_at = Column(DateTime, default=utc_now, nullable=False)


class ChallengeEvent(Base):
    __tablename__ = "challenge_event"

    event_id = Column(String(64), primary_key=True, default=generate_uuid)
    source_id = Column(String(64), ForeignKey("source.source_id"), nullable=False)
    url = Column(Text, nullable=False)
    challenge_type = Column(String(64), nullable=False)  # CLOUDFLARE_TURNSTILE, MANAGED_CHALLENGE, CAPTCHA
    redacted_evidence = Column(Text, nullable=True)
    action_taken = Column(String(64), nullable=False)  # QUARANTINED, FALLBACK_TRIGGERED
    occurred_at = Column(DateTime, default=utc_now, nullable=False)


# ==========================================
# 4. Raw Storage & Parsed Artifacts
# ==========================================

class RawArtifact(Base):
    __tablename__ = "raw_artifact"

    artifact_id = Column(String(64), primary_key=True, default=generate_uuid)
    content_sha256 = Column(String(64), nullable=False, unique=True, index=True)
    object_uri = Column(Text, nullable=False)
    mime_type = Column(String(128), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    first_seen_at = Column(DateTime, default=utc_now, nullable=False)
    malware_status = Column(String(32), default="CLEAN", nullable=False)


class ArtifactProvenance(Base):
    __tablename__ = "artifact_provenance"

    provenance_id = Column(String(64), primary_key=True, default=generate_uuid)
    artifact_id = Column(String(64), ForeignKey("raw_artifact.artifact_id"), nullable=False)
    source_id = Column(String(64), ForeignKey("source.source_id"), nullable=False)
    source_url = Column(Text, nullable=False)
    canonical_url = Column(Text, nullable=False)
    fetched_at = Column(DateTime, default=utc_now, nullable=False)


class ParsedDocument(Base):
    __tablename__ = "parsed_document"

    parsed_id = Column(String(64), primary_key=True, default=generate_uuid)
    artifact_id = Column(String(64), ForeignKey("raw_artifact.artifact_id"), nullable=False)
    parser_name = Column(String(64), nullable=False)
    parser_version = Column(String(32), nullable=False)
    title = Column(Text, nullable=True)
    language = Column(String(16), default="vi", nullable=False)
    parsed_json = Column(JSON, nullable=False)  # Pages, blocks, tables, metadata
    extraction_confidence = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


# ==========================================
# 5. Legal Documents & Versioning (Temporal)
# ==========================================

class Document(Base):
    __tablename__ = "document"

    document_id = Column(String(64), primary_key=True, default=generate_uuid)
    doc_number = Column(String(128), nullable=False, index=True)  # e.g., 85/2026/TT-BTC
    doc_type = Column(String(64), nullable=False)  # ThongTu, NghiDinh, Luat, QuyetDinh, ThongBao
    issuing_authority = Column(String(255), nullable=False)  # Bo Tai Chinh, Tong Cuc Hai Quan
    title = Column(Text, nullable=False)
    jurisdiction = Column(String(32), default="VN", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class DocumentVersion(Base):
    __tablename__ = "document_version"

    version_id = Column(String(64), primary_key=True, default=generate_uuid)
    document_id = Column(String(64), ForeignKey("document.document_id"), nullable=False, index=True)
    version_number = Column(Integer, default=1, nullable=False)
    source_artifact_id = Column(String(64), ForeignKey("raw_artifact.artifact_id"), nullable=False)
    authoritative_level = Column(String(32), nullable=False)
    language = Column(String(16), default="vi", nullable=False)
    published_at = Column(Date, nullable=True)
    valid_from = Column(Date, nullable=True, index=True)
    valid_to = Column(Date, nullable=True, index=True)
    effective_status = Column(String(32), default="ACTIVE", nullable=False)  # ACTIVE, SUPERSEDED, REPEALED, PENDING
    normalized_sha256 = Column(String(64), nullable=False)
    parser_version = Column(String(32), default="1.0.0", nullable=False)
    recorded_at = Column(DateTime, default=utc_now, nullable=False)
    superseded_at = Column(DateTime, nullable=True)
    is_current = Column(Boolean, default=True, nullable=False)


class DocumentRelation(Base):
    __tablename__ = "document_relation"

    relation_id = Column(String(64), primary_key=True, default=generate_uuid)
    source_doc_id = Column(String(64), ForeignKey("document.document_id"), nullable=False)
    target_doc_id = Column(String(64), ForeignKey("document.document_id"), nullable=False)
    relation_type = Column(String(32), nullable=False)  # REPLACES, AMENDS, SUPPLEMENTS, GUIDES, REPEALS
    effective_date = Column(Date, nullable=True)


class LegalProvision(Base):
    __tablename__ = "legal_provision"

    provision_id = Column(String(64), primary_key=True, default=generate_uuid)
    document_version_id = Column(String(64), ForeignKey("document_version.version_id"), nullable=False)
    provision_type = Column(String(32), nullable=False)  # PHAN, CHUONG, MUC, DIEU, KHOAN, DIEM, PHU_LUC
    code = Column(String(64), nullable=False)  # e.g., DIEU_1, KHOAN_2
    title = Column(Text, nullable=True)
    content_text = Column(Text, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)


# ==========================================
# 6. Nomenclature, Tariff & Rulings
# ==========================================

class HSEdition(Base):
    __tablename__ = "hs_edition"

    edition_id = Column(String(64), primary_key=True, default=generate_uuid)
    jurisdiction = Column(String(32), nullable=False)  # VN, ASEAN, WCO
    edition_year = Column(String(16), nullable=False)  # 2022, 2027
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)
    name = Column(String(255), nullable=False)


class HSNode(Base):
    __tablename__ = "hs_node"

    node_id = Column(String(64), primary_key=True, default=generate_uuid)
    edition_id = Column(String(64), ForeignKey("hs_edition.edition_id"), nullable=False)
    code = Column(String(32), nullable=False, index=True)  # 84, 8471, 8471.30, 8471.30.20
    level = Column(Integer, nullable=False)  # 1: Chapter(2), 2: Heading(4), 3: Subheading(6), 4: National(8)
    parent_code = Column(String(32), nullable=True, index=True)
    description_vi = Column(Text, nullable=True)
    description_en = Column(Text, nullable=True)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    is_leaf = Column(Boolean, default=False, nullable=False)


class TariffSchedule(Base):
    __tablename__ = "tariff_schedule"

    schedule_id = Column(String(64), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    schedule_type = Column(String(64), nullable=False)  # MFN, ATIGA, EVFTA, CPTPP, ACFTA
    partner_country = Column(String(64), nullable=True)
    jurisdiction = Column(String(32), default="VN", nullable=False)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)


class TariffRate(Base):
    __tablename__ = "tariff_rate"

    rate_id = Column(String(64), primary_key=True, default=generate_uuid)
    schedule_id = Column(String(64), ForeignKey("tariff_schedule.schedule_id"), nullable=False)
    hs_code = Column(String(32), nullable=False, index=True)
    rate_type = Column(String(32), default="ad_valorem", nullable=False)  # ad_valorem, specific, compound, mixed
    rate_value = Column(Float, nullable=True)  # e.g., 5.0 for 5%
    rate_unit = Column(String(32), nullable=True)  # %, USD/kg
    condition_text = Column(Text, nullable=True)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)


class ClassificationRuling(Base):
    __tablename__ = "classification_ruling"

    ruling_id = Column(String(64), primary_key=True, default=generate_uuid)
    ruling_number = Column(String(128), nullable=False, index=True)  # So Thong Bao / Quyet Dinh
    issuing_authority = Column(String(255), nullable=False)
    ruling_date = Column(Date, nullable=False)
    product_declared_name = Column(Text, nullable=False)
    product_classified_name = Column(Text, nullable=True)
    product_specifications = Column(Text, nullable=True)
    hs_code = Column(String(32), nullable=False, index=True)
    legal_basis = Column(Text, nullable=True)
    source_artifact_id = Column(String(64), ForeignKey("raw_artifact.artifact_id"), nullable=True)
    source_url = Column(Text, nullable=True)
    status = Column(String(32), default="ACTIVE", nullable=False)  # ACTIVE, REPLACED, REVOKED, AMENDED
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)


# ==========================================
# 7. Search, Chunks & Quality Issues
# ==========================================

class ContentChunk(Base):
    __tablename__ = "content_chunk"

    chunk_id = Column(String(64), primary_key=True, default=generate_uuid)
    entity_type = Column(String(64), nullable=False)  # document_version, hs_node, tariff_rate, classification_ruling
    entity_id = Column(String(64), nullable=False, index=True)
    title = Column(Text, nullable=True)
    content_text = Column(Text, nullable=False)
    search_vector_text = Column(Text, nullable=False)  # Normalized search tokens
    source_url = Column(Text, nullable=True)
    page_number = Column(Integer, nullable=True)
    section_name = Column(String(255), nullable=True)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class QualityIssue(Base):
    __tablename__ = "quality_issue"

    issue_id = Column(String(64), primary_key=True, default=generate_uuid)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False)
    severity = Column(String(32), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    issue_type = Column(String(64), nullable=False)  # MISSING_PARENT, INVALID_CODE, DATE_CONFLICT, FORMAT_ERROR
    description = Column(Text, nullable=False)
    status = Column(String(32), default="OPEN", nullable=False)  # OPEN, RESOLVED, IGNORED
    created_at = Column(DateTime, default=utc_now, nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_event"

    event_id = Column(String(64), primary_key=True, default=generate_uuid)
    event_type = Column(String(64), nullable=False)  # SOURCE_SYNC, POLICY_CHANGE, ENTITLEMENT_UPDATE, REPARSE
    actor = Column(String(64), default="system", nullable=False)
    details = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


# ==========================================
# 9. Outbound Webhooks & Subscriber Subsystem
# ==========================================

class WebhookSubscription(Base):
    __tablename__ = "webhook_subscription"

    subscription_id = Column(String(64), primary_key=True, default=generate_uuid)
    name = Column(String(128), nullable=False)
    target_url = Column(Text, nullable=False)
    secret_token = Column(String(128), nullable=False)  # For HMAC-SHA256
    event_types = Column(JSON, nullable=False, default=list)  # ["hs.ruling.published", "hs.tariff.changed", "*"]
    is_active = Column(Boolean, default=True, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class WebhookDeliveryLog(Base):
    __tablename__ = "webhook_delivery_log"

    delivery_id = Column(String(64), primary_key=True, default=generate_uuid)
    subscription_id = Column(String(64), ForeignKey("webhook_subscription.subscription_id"), nullable=False)
    event_type = Column(String(64), nullable=False)
    event_id = Column(String(64), nullable=False)
    payload_json = Column(JSON, nullable=False)
    response_status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    attempt_number = Column(Integer, default=1, nullable=False)
    status = Column(String(32), nullable=False)  # DELIVERED, FAILED, RETRYING
    delivered_at = Column(DateTime, default=utc_now, nullable=False)
