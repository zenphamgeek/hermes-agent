"""Pydantic Schemas for HSE Knowledge Platform REST API."""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field


class SyncPlanRequest(BaseModel):
    scope: str = "vietnam-core"
    mode: str = "incremental"


class SyncPlanResponse(BaseModel):
    scope: str
    mode: str
    target_sources: List[str]
    estimated_workload: int
    policy_blocks: List[str] = []


class SyncRunResponse(BaseModel):
    run_id: str
    scope: str
    mode: str
    status: str
    items_discovered: int
    items_downloaded: int
    items_normalized: int
    started_at: datetime
    finished_at: Optional[datetime] = None


class OnDemandSyncRequest(BaseModel):
    topic_or_taxonomy: str
    scope: str = "vietnam-core"
    callback_url: Optional[str] = None


class SourceSummary(BaseModel):
    id: str
    name: str
    jurisdiction: str
    authority_level: str
    license_policy: str
    entitlement_required: bool
    is_active: bool = True


class ApplicabilityEvaluationRequest(BaseModel):
    facility_id: str
    province: str = "Binh Duong"
    activities: List[str] = ["store", "use"]
    chemicals_stored: List[str] = ["toluene", "acetone"]
    chemical_storage_quantity_kg: float = 1200.0
    wastewater_flow_m3_day: float = 100.0
    has_boiler: bool = True
    as_of: Optional[date] = None


class ApplicabilityEvaluationResponse(BaseModel):
    facility_id: str
    as_of: date
    applicable_obligations: List[str]
    unknown_obligations: List[str] = []
    missing_facts: List[str] = []
    decision_traces: List[Dict[str, Any]] = []


class SearchQueryResponse(BaseModel):
    query: str
    as_of: date
    total_results: int
    results: List[Dict[str, Any]]


class WebhookSubscriptionCreate(BaseModel):
    name: str
    target_url: str
    secret_token: str
    event_types: List[str] = ["*"]


class WebhookSubscriptionResponse(BaseModel):
    subscription_id: str
    name: str
    target_url: str
    event_types: List[str]
    is_active: bool
    created_at: datetime
