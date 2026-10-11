"""Comprehensive SQLAlchemy Relational Models for HSE Knowledge Platform (SRS-HSEK-001)."""

import uuid
from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, JSON, DateTime, Date,
    ForeignKey, Table, Index, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# =============================================================
# 1. Source & Registry Domain
# =============================================================

class Source(Base):
    __tablename__ = "source"

    source_id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    jurisdiction = Column(String(64), nullable=False, default="VN")  # VN, GLOBAL, US, EU, INTERNATIONAL
    authority_level = Column(String(64), nullable=False)  # A1_MANDATORY_LAW, A2_MANDATORY_TECH_REG, etc.
    allowed_hosts = Column(JSON, nullable=False)  # List[str]
    content_classes = Column(JSON, nullable=False)  # List[str]
    discovery_config = Column(JSON, nullable=False)
    fetch_config = Column(JSON, nullable=False)
    acquisition_config = Column(JSON, nullable=False)
    license_policy = Column(String(64), nullable=False, default="PUBLIC_DOWNLOAD")
    entitlement_required = Column(Boolean, default=False, nullable=False)
    privacy_class = Column(String(64), default="public_knowledge", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class SourceEndpoint(Base):
    __tablename__ = "source_endpoint"

    endpoint_id = Column(String(64), primary_key=True, default=generate_uuid)
    source_id = Column(String(64), ForeignKey("source.source_id"), nullable=False)
    channel_type = Column(String(64), nullable=False)  # official_api, bulk_export, http, browser_render
    endpoint_url = Column(Text, nullable=False)
    is_primary = Column(Boolean, default=True, nullable=False)
    auth_type = Column(String(64), default="NONE", nullable=False)


class SourcePolicy(Base):
    __tablename__ = "source_policy"

    policy_id = Column(String(64), primary_key=True, default=generate_uuid)
    source_id = Column(String(64), ForeignKey("source.source_id"), nullable=False)
    robots_txt_status = Column(String(32), default="ALLOWED", nullable=False)
    robots_txt_snapshot = Column(Text, nullable=True)
    terms_url = Column(Text, nullable=True)
    terms_snapshot_hash = Column(String(64), nullable=True)
    last_verified_at = Column(DateTime, default=utc_now, nullable=False)


class Entitlement(Base):
    __tablename__ = "entitlement"

    entitlement_id = Column(String(64), primary_key=True, default=generate_uuid)
    source_id = Column(String(64), ForeignKey("source.source_id"), nullable=False)
    license_contract_ref = Column(String(128), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=False)
    storage_allowed = Column(Boolean, default=False, nullable=False)
    embedding_allowed = Column(Boolean, default=False, nullable=False)
    redistribution_allowed = Column(Boolean, default=False, nullable=False)
    excerpt_limit_chars = Column(Integer, default=500, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


# =============================================================
# 2. Acquisition & Resilience Domain
# =============================================================

class AccessContract(Base):
    __tablename__ = "access_contract"

    contract_id = Column(String(64), primary_key=True, default=generate_uuid)
    source_id = Column(String(64), ForeignKey("source.source_id"), nullable=False)
    rate_limit_rps = Column(Float, default=1.0, nullable=False)
    max_concurrency = Column(Integer, default=2, nullable=False)
    timeout_seconds = Column(Integer, default=30, nullable=False)
    honor_robots_txt = Column(Boolean, default=True, nullable=False)


class AcquisitionRoute(Base):
    __tablename__ = "acquisition_route"

    route_id = Column(String(64), primary_key=True, default=generate_uuid)
    source_id = Column(String(64), ForeignKey("source.source_id"), nullable=False)
    channel = Column(String(64), nullable=False)
    priority_order = Column(Integer, default=1, nullable=False)
    success_rate = Column(Float, default=1.0, nullable=False)
    is_operational = Column(Boolean, default=True, nullable=False)


class FetchAttempt(Base):
    __tablename__ = "fetch_attempt"

    attempt_id = Column(String(64), primary_key=True, default=generate_uuid)
    source_id = Column(String(64), ForeignKey("source.source_id"), nullable=False)
    target_url = Column(Text, nullable=False)
    channel_used = Column(String(64), nullable=False)
    status_code = Column(Integer, nullable=True)
    response_class = Column(String(64), nullable=False)  # SUCCESS, TRANSIENT, RATE_LIMIT, etc.
    duration_ms = Column(Integer, nullable=False)
    attempted_at = Column(DateTime, default=utc_now, nullable=False)
    error_message = Column(Text, nullable=True)


class RetryBudget(Base):
    __tablename__ = "retry_budget"

    budget_id = Column(String(64), primary_key=True, default=generate_uuid)
    host = Column(String(255), unique=True, nullable=False)
    max_tokens = Column(Integer, default=100, nullable=False)
    available_tokens = Column(Float, default=100.0, nullable=False)
    last_replenished_at = Column(DateTime, default=utc_now, nullable=False)


class CircuitBreaker(Base):
    __tablename__ = "circuit_breaker"

    breaker_id = Column(String(64), primary_key=True, default=generate_uuid)
    host = Column(String(255), unique=True, nullable=False)
    state = Column(String(32), default="CLOSED", nullable=False)  # CLOSED, OPEN, HALF_OPEN
    consecutive_failures = Column(Integer, default=0, nullable=False)
    trip_reason = Column(String(255), nullable=True)
    last_tripped_at = Column(DateTime, nullable=True)
    probe_due_at = Column(DateTime, nullable=True)


class ChallengeEvent(Base):
    __tablename__ = "challenge_event"

    event_id = Column(String(64), primary_key=True, default=generate_uuid)
    source_id = Column(String(64), ForeignKey("source.source_id"), nullable=False)
    target_url = Column(Text, nullable=False)
    challenge_type = Column(String(64), nullable=False)  # CLOUDFLARE_TURNSTILE, CAPTCHA, WAF
    action_taken = Column(String(64), default="QUARANTINED", nullable=False)
    occurred_at = Column(DateTime, default=utc_now, nullable=False)


# =============================================================
# 3. Operations, Runs & Quality Domain
# =============================================================

class SyncRun(Base):
    __tablename__ = "sync_run"

    run_id = Column(String(64), primary_key=True, default=generate_uuid)
    scope = Column(String(128), default="vietnam-core", nullable=False)
    mode = Column(String(32), default="incremental", nullable=False)  # incremental, full, on-demand, reconcile
    status = Column(String(32), default="QUEUED", nullable=False)  # QUEUED, RUNNING, SUCCEEDED, PARTIAL, FAILED
    sources_target = Column(JSON, nullable=True)
    items_discovered = Column(Integer, default=0, nullable=False)
    items_downloaded = Column(Integer, default=0, nullable=False)
    items_unchanged = Column(Integer, default=0, nullable=False)
    items_parsed = Column(Integer, default=0, nullable=False)
    items_normalized = Column(Integer, default=0, nullable=False)
    items_quarantined = Column(Integer, default=0, nullable=False)
    coverage_report_uri = Column(Text, nullable=True)
    started_at = Column(DateTime, default=utc_now, nullable=False)
    finished_at = Column(DateTime, nullable=True)


class Checkpoint(Base):
    __tablename__ = "checkpoint"

    checkpoint_id = Column(String(64), primary_key=True, default=generate_uuid)
    run_id = Column(String(64), ForeignKey("sync_run.run_id"), nullable=False)
    source_id = Column(String(64), ForeignKey("source.source_id"), nullable=False)
    cursor_value = Column(String(255), nullable=True)
    items_processed = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)


class CoverageReport(Base):
    __tablename__ = "coverage_report"

    report_id = Column(String(64), primary_key=True, default=generate_uuid)
    run_id = Column(String(64), ForeignKey("sync_run.run_id"), nullable=False)
    jurisdiction = Column(String(64), nullable=False)
    content_class = Column(String(64), nullable=False)
    total_discovered = Column(Integer, default=0, nullable=False)
    total_gated = Column(Integer, default=0, nullable=False)
    total_failed = Column(Integer, default=0, nullable=False)
    manifest_data = Column(JSON, nullable=False)
    generated_at = Column(DateTime, default=utc_now, nullable=False)


class QualityIssue(Base):
    __tablename__ = "quality_issue"

    issue_id = Column(String(64), primary_key=True, default=generate_uuid)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False)
    severity = Column(String(32), default="MEDIUM", nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    issue_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(32), default="OPEN", nullable=False)  # OPEN, RESOLVED, WAIVED
    created_at = Column(DateTime, default=utc_now, nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_event"

    event_id = Column(String(64), primary_key=True, default=generate_uuid)
    actor_role = Column(String(64), default="system", nullable=False)
    action_type = Column(String(64), nullable=False)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False)
    change_summary = Column(JSON, nullable=False)
    recorded_at = Column(DateTime, default=utc_now, nullable=False)


# =============================================================
# 4. Evidence & Raw Storage Domain
# =============================================================

class RawArtifact(Base):
    __tablename__ = "raw_artifact"

    artifact_id = Column(String(64), primary_key=True, default=generate_uuid)
    content_sha256 = Column(String(64), unique=True, index=True, nullable=False)
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
    parsed_json = Column(JSON, nullable=False)
    parsed_at = Column(DateTime, default=utc_now, nullable=False)


# =============================================================
# 5. Legal & Technical Documents Domain
# =============================================================

class Document(Base):
    __tablename__ = "document"

    document_id = Column(String(64), primary_key=True, default=generate_uuid)
    doc_number = Column(String(128), unique=True, index=True, nullable=False)  # e.g. 84/2015/QH13, 08/2022/ND-CP
    doc_type = Column(String(64), nullable=False)  # Luat, NghiDinh, ThongTu, QCVN, TCVN, ISO
    issuing_authority = Column(String(255), nullable=False)
    title = Column(Text, nullable=False)
    jurisdiction = Column(String(64), default="VN", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class DocumentVersion(Base):
    __tablename__ = "document_version"

    version_id = Column(String(64), primary_key=True, default=generate_uuid)
    document_id = Column(String(64), ForeignKey("document.document_id"), nullable=False)
    version_number = Column(Integer, default=1, nullable=False)
    source_artifact_id = Column(String(64), ForeignKey("raw_artifact.artifact_id"), nullable=False)
    authoritative_level = Column(String(64), default="A1_MANDATORY_LAW", nullable=False)
    language = Column(String(16), default="vi", nullable=False)
    published_at = Column(Date, nullable=True)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    effective_status = Column(String(32), default="ACTIVE", nullable=False)  # ACTIVE, SUPERSEDED, REPEALED
    normalized_sha256 = Column(String(64), nullable=False)
    parser_version = Column(String(32), default="1.0.0", nullable=False)
    is_current = Column(Boolean, default=True, nullable=False)


class LegalProvision(Base):
    __tablename__ = "legal_provision"

    provision_id = Column(String(64), primary_key=True, default=generate_uuid)
    version_id = Column(String(64), ForeignKey("document_version.version_id"), nullable=False)
    provision_type = Column(String(32), nullable=False)  # CHUONG, MUC, DIEU, KHOAN, DIEM, PHU_LUC
    code = Column(String(64), nullable=False, index=True)  # e.g. DIEU_15
    title = Column(Text, nullable=True)
    content_text = Column(Text, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)


class Definition(Base):
    __tablename__ = "definition"

    definition_id = Column(String(64), primary_key=True, default=generate_uuid)
    provision_id = Column(String(64), ForeignKey("legal_provision.provision_id"), nullable=False)
    term = Column(String(255), index=True, nullable=False)
    definition_text = Column(Text, nullable=False)
    scope_context = Column(String(128), nullable=True)


class SanctionLink(Base):
    __tablename__ = "sanction_link"

    sanction_id = Column(String(64), primary_key=True, default=generate_uuid)
    obligation_id = Column(String(64), nullable=False)
    decree_doc_number = Column(String(128), nullable=False)
    article_ref = Column(String(64), nullable=False)
    fine_min_vnd = Column(Float, nullable=True)
    fine_max_vnd = Column(Float, nullable=True)
    remedial_measures = Column(Text, nullable=True)


# =============================================================
# 6. Obligations & Applicability Domain
# =============================================================

class Obligation(Base):
    __tablename__ = "obligation"

    obligation_id = Column(String(64), primary_key=True, default=generate_uuid)
    code = Column(String(128), unique=True, index=True, nullable=False)
    title = Column(Text, nullable=False)
    domain = Column(String(64), default="safety", nullable=False)  # safety, health, environment, chemical, fire
    created_at = Column(DateTime, default=utc_now, nullable=False)


class ObligationVersion(Base):
    __tablename__ = "obligation_version"

    obligation_version_id = Column(String(64), primary_key=True, default=generate_uuid)
    obligation_id = Column(String(64), ForeignKey("obligation.obligation_id"), nullable=False)
    actor_type = Column(String(64), nullable=False)  # employer, facility_owner, worker, chemical_operator
    action_type = Column(String(64), nullable=False)  # inspect, report, permit, train, monitor, equip
    object_type = Column(String(64), nullable=False)  # boiler, hazardous_waste, chemical_storage, confined_space
    requirement_text = Column(Text, nullable=False)
    frequency_or_deadline = Column(JSON, nullable=True)
    threshold = Column(JSON, nullable=True)
    authority_level = Column(String(64), default="A1_MANDATORY_LAW", nullable=False)
    source_provision_id = Column(String(64), ForeignKey("legal_provision.provision_id"), nullable=True)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    rule_review_status = Column(String(32), default="APPROVED", nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)


class ApplicabilityRule(Base):
    __tablename__ = "applicability_rule"

    rule_id = Column(String(64), primary_key=True, default=generate_uuid)
    code = Column(String(128), unique=True, index=True, nullable=False)
    rule_version = Column(Integer, default=1, nullable=False)
    jurisdiction = Column(String(64), default="VN", nullable=False)
    expression = Column(JSON, nullable=False)  # Boolean logic rule DSL
    required_facts = Column(JSON, nullable=False)  # List of fact keys
    source_provision_id = Column(String(64), ForeignKey("legal_provision.provision_id"), nullable=True)
    authority_level = Column(String(64), default="A1_MANDATORY_LAW", nullable=False)
    approval_status = Column(String(32), default="APPROVED", nullable=False)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)


class DecisionTrace(Base):
    __tablename__ = "decision_trace"

    trace_id = Column(String(64), primary_key=True, default=generate_uuid)
    facility_id = Column(String(64), nullable=False)
    rule_id = Column(String(64), ForeignKey("applicability_rule.rule_id"), nullable=False)
    evaluation_result = Column(String(32), nullable=False)  # applicable, not_applicable, conditional, unknown
    evaluated_facts = Column(JSON, nullable=False)
    missing_facts = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=False)
    evaluated_at = Column(DateTime, default=utc_now, nullable=False)


# =============================================================
# 7. Organization, Facility & Context Domain
# =============================================================

class Organization(Base):
    __tablename__ = "organization"

    org_id = Column(String(64), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    tax_code = Column(String(64), unique=True, nullable=True)
    industry_code = Column(String(64), nullable=True)  # VSIC / ISIC
    created_at = Column(DateTime, default=utc_now, nullable=False)


class Facility(Base):
    __tablename__ = "facility"

    facility_id = Column(String(64), primary_key=True, default=generate_uuid)
    org_id = Column(String(64), ForeignKey("organization.org_id"), nullable=False)
    name = Column(String(255), nullable=False)
    province = Column(String(128), default="Binh Duong", nullable=False)
    industrial_zone = Column(String(255), nullable=True)
    lifecycle_stage = Column(String(64), default="OPERATION", nullable=False)
    worker_count = Column(Integer, default=100, nullable=False)
    profile_facts = Column(JSON, nullable=False)  # Structured facts compiler


class Commitment(Base):
    __tablename__ = "commitment"

    commitment_id = Column(String(64), primary_key=True, default=generate_uuid)
    facility_id = Column(String(64), ForeignKey("facility.facility_id"), nullable=False)
    standard_name = Column(String(64), nullable=False)  # ISO_14001, ISO_45001, IFC_EHS
    edition = Column(String(32), default="2026", nullable=False)
    scope = Column(Text, nullable=True)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)


# =============================================================
# 8. Chemical Master, SDS & GHS Domain
# =============================================================

class Substance(Base):
    __tablename__ = "substance"

    substance_id = Column(String(64), primary_key=True, default=generate_uuid)
    cas_number = Column(String(64), unique=True, index=True, nullable=False)
    ec_number = Column(String(64), nullable=True)
    un_number = Column(String(32), nullable=True)
    chemical_name_en = Column(String(255), nullable=False)
    chemical_name_vi = Column(String(255), nullable=False)
    formula = Column(String(128), nullable=True)
    molecular_weight = Column(Float, nullable=True)


class ChemicalProduct(Base):
    __tablename__ = "chemical_product"

    product_id = Column(String(64), primary_key=True, default=generate_uuid)
    trade_name = Column(String(255), index=True, nullable=False)
    supplier_name = Column(String(255), nullable=False)
    physical_state = Column(String(64), default="LIQUID", nullable=False)
    flash_point_c = Column(Float, nullable=True)
    is_mixture = Column(Boolean, default=False, nullable=False)


class SDS(Base):
    __tablename__ = "sds"

    sds_id = Column(String(64), primary_key=True, default=generate_uuid)
    product_id = Column(String(64), ForeignKey("chemical_product.product_id"), nullable=False)
    revision_date = Column(Date, nullable=False)
    language = Column(String(16), default="vi", nullable=False)
    source_artifact_id = Column(String(64), ForeignKey("raw_artifact.artifact_id"), nullable=False)
    sections_json = Column(JSON, nullable=False)  # 16 sections data
    completeness_score = Column(Float, default=1.0, nullable=False)
    is_current = Column(Boolean, default=True, nullable=False)


class GHSProfile(Base):
    __tablename__ = "ghs_profile"

    ghs_id = Column(String(64), primary_key=True, default=generate_uuid)
    product_id = Column(String(64), ForeignKey("chemical_product.product_id"), nullable=False)
    edition = Column(String(32), default="Rev_11", nullable=False)
    signal_word = Column(String(32), default="DANGER", nullable=False)  # DANGER, WARNING, NONE
    pictograms = Column(JSON, nullable=False)  # List[str] e.g. GHS02, GHS07
    h_statements = Column(JSON, nullable=False)  # List[str] e.g. H225, H319
    p_statements = Column(JSON, nullable=False)  # List[str] e.g. P210, P280


class OEL(Base):
    __tablename__ = "oel"

    oel_id = Column(String(64), primary_key=True, default=generate_uuid)
    substance_id = Column(String(64), ForeignKey("substance.substance_id"), nullable=False)
    jurisdiction = Column(String(64), default="VN", nullable=False)  # VN (QCVN), US_NIOSH, US_ACGIH, US_OSHA
    authority_level = Column(String(64), default="A2_MANDATORY_TECH_REG", nullable=False)
    twa_mg_m3 = Column(Float, nullable=True)
    twa_ppm = Column(Float, nullable=True)
    stel_mg_m3 = Column(Float, nullable=True)
    ceiling_mg_m3 = Column(Float, nullable=True)
    source_doc_number = Column(String(128), nullable=False)
    valid_from = Column(Date, default=date(2026, 1, 1), nullable=False)


# =============================================================
# 9. Hazard, Bow-Tie & Controls Domain
# =============================================================

class Hazard(Base):
    __tablename__ = "hazard"

    hazard_id = Column(String(64), primary_key=True, default=generate_uuid)
    code = Column(String(64), unique=True, index=True, nullable=False)
    category = Column(String(64), nullable=False)  # physical, chemical, fire_explosion, mechanical, electrical
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)


class Control(Base):
    __tablename__ = "control"

    control_id = Column(String(64), primary_key=True, default=generate_uuid)
    hazard_id = Column(String(64), ForeignKey("hazard.hazard_id"), nullable=False)
    hierarchy_level = Column(String(64), nullable=False)  # elimination, substitution, engineering, administrative, ppe
    title = Column(String(255), nullable=False)
    verification_method = Column(String(255), nullable=True)
    frequency = Column(String(64), default="continuous", nullable=False)


# =============================================================
# 10. Environmental Aspects & Permits Domain
# =============================================================

class EnvironmentalAspect(Base):
    __tablename__ = "environmental_aspect"

    aspect_id = Column(String(64), primary_key=True, default=generate_uuid)
    facility_id = Column(String(64), ForeignKey("facility.facility_id"), nullable=False)
    activity_name = Column(String(255), nullable=False)
    aspect_type = Column(String(64), nullable=False)  # wastewater_discharge, air_emission, hazardous_waste
    significance = Column(String(32), default="HIGH", nullable=False)


class EnvironmentalLimit(Base):
    __tablename__ = "environmental_limit"

    limit_id = Column(String(64), primary_key=True, default=generate_uuid)
    pollutant_name = Column(String(128), index=True, nullable=False)
    medium = Column(String(32), nullable=False)  # wastewater, ambient_air, stack_emission, noise
    max_concentration = Column(Float, nullable=False)
    unit = Column(String(32), default="mg/L", nullable=False)
    source_regulation = Column(String(128), default="QCVN 40:2011/BTNMT", nullable=False)
    authority_level = Column(String(64), default="A2_MANDATORY_TECH_REG", nullable=False)


# =============================================================
# 11. Search Chunks, Webhooks & Outbound Hub
# =============================================================

class ContentChunk(Base):
    __tablename__ = "content_chunk"

    chunk_id = Column(String(64), primary_key=True, default=generate_uuid)
    entity_type = Column(String(64), index=True, nullable=False)  # document, obligation, substance, sds, oel, control
    entity_id = Column(String(64), index=True, nullable=False)
    title = Column(Text, nullable=False)
    content_text = Column(Text, nullable=False)
    search_vector_text = Column(Text, nullable=False)
    source_url = Column(Text, nullable=True)
    section_name = Column(String(255), nullable=True)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class WebhookSubscription(Base):
    __tablename__ = "webhook_subscription"

    subscription_id = Column(String(64), primary_key=True, default=generate_uuid)
    name = Column(String(128), nullable=False)
    target_url = Column(Text, nullable=False)
    secret_token = Column(String(255), nullable=False)
    event_types = Column(JSON, nullable=False)  # List[str] e.g. ["hse.law.promulgated", "hse.sds.updated"]
    is_active = Column(Boolean, default=True, nullable=False)
    consecutive_failures = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class WebhookDeliveryLog(Base):
    __tablename__ = "webhook_delivery_log"

    delivery_id = Column(String(64), primary_key=True, default=generate_uuid)
    subscription_id = Column(String(64), ForeignKey("webhook_subscription.subscription_id"), nullable=False)
    event_type = Column(String(64), nullable=False)
    payload_json = Column(JSON, nullable=False)
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    delivered_at = Column(DateTime, default=utc_now, nullable=False)
    is_success = Column(Boolean, default=False, nullable=False)
