"""Pydantic schemas for the REST API."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SyncPlanRequest(BaseModel):
    scope: str = "vietnam-core"
    source_id: Optional[str] = None
    mode: str = "incremental"


class SyncRunCreateRequest(BaseModel):
    mode: str = "incremental"  # incremental, full
    scope: str = "vietnam-core"
    source_id: Optional[str] = None
    sources: Optional[List[str]] = None
    dry_run: bool = False
    reparse: bool = False


class SourceHealthResponse(BaseModel):
    source_id: str
    is_healthy: bool
    latency_ms: int = 0
    status: str = "OK"


class QualityIssueResponse(BaseModel):
    issue_id: str
    entity_type: str
    entity_id: str
    severity: str
    issue_type: str
    description: str
    status: str


# ==========================================
# Webhook API Schemas
# ==========================================

class WebhookSubscriptionCreateRequest(BaseModel):
    name: str
    target_url: str
    event_types: Optional[List[str]] = Field(default_factory=lambda: ["*"])
    secret_token: Optional[str] = None


class WebhookSubscriptionResponse(BaseModel):
    subscription_id: str
    name: str
    target_url: str
    event_types: List[str]
    is_active: bool
    failure_count: int
    created_at: Optional[str] = None


class WebhookDeliveryLogResponse(BaseModel):
    delivery_id: str
    subscription_id: str
    event_type: str
    event_id: str
    response_status_code: Optional[int] = None
    duration_ms: Optional[int] = None
    status: str
    delivered_at: Optional[str] = None


class WebhookTriggerRequest(BaseModel):
    source_id: Optional[str] = None
    scope: str = "vietnam-core"
    mode: str = "incremental"
    taxonomy: Optional[str] = None
    callback_url: Optional[str] = None


class WebhookTriggerResponse(BaseModel):
    status: str
    triggered_at: str
    message: str
    taxonomy: Optional[str] = None
    task_id: Optional[str] = None
    results_summary: Optional[Dict[str, Any]] = None


class TaxonomySyncRequest(BaseModel):
    taxonomy: str
    scope: str = "vietnam-core"
    sources: Optional[List[str]] = None
    as_of: Optional[str] = None
    callback_url: Optional[str] = None
    async_execution: bool = False


class TaxonomySyncResponse(BaseModel):
    run_id: str
    taxonomy: str
    status: str
    discovered: int
    downloaded: int
    normalized: int
    quarantined: int = 0
    results: List[Dict[str, Any]] = Field(default_factory=list)
    event_dispatched: bool = True
    task_id: Optional[str] = None

