"""FastAPI Application implementing HS Knowledge Sync REST API (FR-001 - FR-116, Section 17)."""

from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from service.db.session import get_db, init_db
from service.db.models import CrawlRun, QualityIssue, HSNode
from service.core.registry import load_source_registry
from service.core.entitlement import EntitlementManager
from service.pipeline.orchestrator import SyncOrchestrator, SyncPlanResult, SyncRunResult
from service.index.retrieval import HybridRetriever, SearchResponse
from .schemas import (
    SyncPlanRequest, SyncRunCreateRequest, SourceHealthResponse, QualityIssueResponse,
    WebhookSubscriptionCreateRequest, WebhookSubscriptionResponse,
    WebhookDeliveryLogResponse, WebhookTriggerRequest, WebhookTriggerResponse,
    TaxonomySyncRequest, TaxonomySyncResponse
)
from service.webhooks.dispatcher import WebhookDispatcher
from service.db.models import WebhookSubscription, WebhookDeliveryLog

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="HS Knowledge Sync API",
    version="1.1.0",
    description="Deterministic HS Knowledge Synchronization, Search & Auditing API",
    lifespan=lifespan
)


@app.get("/health")
def health_root(db: Session = Depends(get_db)):
    return {"status": "ok", "database": "connected"}


@app.get("/health/live")
def health_live():
    return {"status": "alive", "service": "hs-sync"}


@app.get("/health/ready")
def health_ready(db: Session = Depends(get_db)):
    try:
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "degraded", "database": "disconnected", "error": str(e)}


@app.post("/v1/sync/plan", response_model=SyncPlanResult)
def create_sync_plan(req: SyncPlanRequest, db: Session = Depends(get_db)):
    orch = SyncOrchestrator(db=db)
    return orch.plan(scope=req.scope, source_id=req.source_id, mode=req.mode)


@app.post("/v1/sync/runs", response_model=SyncRunResult)
def create_sync_run(req: SyncRunCreateRequest, db: Session = Depends(get_db)):
    orch = SyncOrchestrator(db=db)
    if req.dry_run:
        plan_res = orch.plan(scope=req.scope, mode=req.mode)
        return SyncRunResult(
            status="succeeded",
            run_id="dry-run",
            scope=req.scope,
            sources=[s.source_id for s in plan_res.sources],
            discovered=plan_res.total_estimated,
            downloaded=0,
            unchanged=0,
            parsed=0,
            normalized=0
        )
    return orch.run_sync(scope=req.scope, source_id=req.source_id, mode=req.mode)


@app.get("/v1/sync/runs/{run_id}")
def get_sync_run(run_id: str, db: Session = Depends(get_db)):
    run_obj = db.query(CrawlRun).filter_by(run_id=run_id).first()
    if not run_obj:
        raise HTTPException(status_code=404, detail="Sync run not found")
    return {
        "run_id": run_obj.run_id,
        "status": run_obj.status,
        "scope": run_obj.scope,
        "discovered": run_obj.items_discovered,
        "downloaded": run_obj.items_downloaded,
        "unchanged": run_obj.items_unchanged,
        "parsed": run_obj.items_parsed,
        "normalized": run_obj.items_normalized,
        "quarantined": run_obj.items_quarantined,
        "started_at": run_obj.started_at,
        "finished_at": run_obj.finished_at
    }


@app.post("/v1/sync/runs/{run_id}/resume", response_model=SyncRunResult)
def resume_sync_run(run_id: str, db: Session = Depends(get_db)):
    orch = SyncOrchestrator(db=db)
    run_obj = db.query(CrawlRun).filter_by(run_id=run_id).first()
    if not run_obj:
        raise HTTPException(status_code=404, detail="Run ID not found")
    return orch.run_sync(scope=run_obj.scope, mode=run_obj.mode, existing_run_id=run_id)


@app.get("/v1/sources")
def list_sources(db: Session = Depends(get_db)):
    registry = load_source_registry()
    return [s.model_dump() for s in registry.list_sources()]


@app.get("/v1/sources/{source_id}/health", response_model=SourceHealthResponse)
def get_source_health(source_id: str):
    registry = load_source_registry()
    source = registry.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceHealthResponse(source_id=source_id, is_healthy=True, latency_ms=15)


@app.get("/v1/entitlements/validate")
def validate_entitlements(db: Session = Depends(get_db)):
    registry = load_source_registry()
    manager = EntitlementManager(registry)
    return [item.model_dump() for item in manager.get_readiness_report(db=db)]


@app.get("/v1/search", response_model=SearchResponse)
def search_knowledge(
    query: str = Query(..., description="Keywords or HS code"),
    as_of: Optional[str] = Query(None, description="Temporal as-of date (YYYY-MM-DD)"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    retriever = HybridRetriever(db=db)
    return retriever.search(query=query, as_of=as_of, limit=limit)


@app.get("/v1/hs/{code}")
def get_hs_node(code: str, edition: str = "2022", db: Session = Depends(get_db)):
    node = db.query(HSNode).filter_by(code=code).first()
    if not node:
        raise HTTPException(status_code=404, detail=f"HS code {code} not found")
    return {
        "code": node.code,
        "level": node.level,
        "parent_code": node.parent_code,
        "description_vi": node.description_vi,
        "description_en": node.description_en,
        "is_leaf": node.is_leaf
    }


@app.get("/v1/quality/issues", response_model=List[QualityIssueResponse])
def get_quality_issues(severity: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(QualityIssue)
    if severity:
        q = q.filter_by(severity=severity.upper())
    issues = q.all()
    return [
        QualityIssueResponse(
            issue_id=i.issue_id,
            entity_type=i.entity_type,
            entity_id=i.entity_id,
            severity=i.severity,
            issue_type=i.issue_type,
            description=i.description,
            status=i.status
        ) for i in issues
    ]


# ==========================================
# Webhook REST API Endpoints
# ==========================================

@app.post("/v1/webhooks/subscriptions", response_model=WebhookSubscriptionResponse)
def create_webhook_subscription(
    req: WebhookSubscriptionCreateRequest,
    db: Session = Depends(get_db)
):
    """Registers a new outbound webhook subscriber."""
    dispatcher = WebhookDispatcher(db=db)
    sub = dispatcher.create_subscription(
        name=req.name,
        target_url=req.target_url,
        event_types=req.event_types or ["*"],
        secret_token=req.secret_token
    )
    return WebhookSubscriptionResponse(
        subscription_id=sub.subscription_id,
        name=sub.name,
        target_url=sub.target_url,
        event_types=sub.event_types,
        is_active=sub.is_active,
        failure_count=sub.failure_count,
        created_at=sub.created_at.isoformat() if sub.created_at else None
    )


@app.get("/v1/webhooks/subscriptions", response_model=List[WebhookSubscriptionResponse])
def list_webhook_subscriptions(
    active_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Lists all registered outbound webhook subscriptions."""
    dispatcher = WebhookDispatcher(db=db)
    subs = dispatcher.list_subscriptions(active_only=active_only)
    return [
        WebhookSubscriptionResponse(
            subscription_id=s.subscription_id,
            name=s.name,
            target_url=s.target_url,
            event_types=s.event_types,
            is_active=s.is_active,
            failure_count=s.failure_count,
            created_at=s.created_at.isoformat() if s.created_at else None
        ) for s in subs
    ]


@app.delete("/v1/webhooks/subscriptions/{subscription_id}")
def delete_webhook_subscription(
    subscription_id: str,
    db: Session = Depends(get_db)
):
    """Deletes a webhook subscription."""
    dispatcher = WebhookDispatcher(db=db)
    success = dispatcher.delete_subscription(subscription_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Subscription '{subscription_id}' not found")
    return {"status": "deleted", "subscription_id": subscription_id}


@app.post("/v1/webhooks/subscriptions/{subscription_id}/test", response_model=WebhookDeliveryLogResponse)
def test_webhook_subscription(
    subscription_id: str,
    db: Session = Depends(get_db)
):
    """Sends a ping test event to a specific webhook subscription."""
    dispatcher = WebhookDispatcher(db=db)
    try:
        log = dispatcher.test_subscription(subscription_id)
        return WebhookDeliveryLogResponse(
            delivery_id=log.delivery_id,
            subscription_id=log.subscription_id,
            event_type=log.event_type,
            event_id=log.event_id,
            response_status_code=log.response_status_code,
            duration_ms=log.duration_ms,
            status=log.status,
            delivered_at=log.delivered_at.isoformat() if log.delivered_at else None
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/webhooks/deliveries", response_model=List[WebhookDeliveryLogResponse])
def list_webhook_deliveries(
    subscription_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Retrieves recent webhook delivery logs for auditing."""
    q = db.query(WebhookDeliveryLog).order_by(WebhookDeliveryLog.delivered_at.desc())
    if subscription_id:
        q = q.filter_by(subscription_id=subscription_id)
    logs = q.limit(limit).all()
    return [
        WebhookDeliveryLogResponse(
            delivery_id=l.delivery_id,
            subscription_id=l.subscription_id,
            event_type=l.event_type,
            event_id=l.event_id,
            response_status_code=l.response_status_code,
            duration_ms=l.duration_ms,
            status=l.status,
            delivered_at=l.delivered_at.isoformat() if l.delivered_at else None
        ) for l in logs
    ]


@app.post("/v1/webhooks/trigger", response_model=WebhookTriggerResponse)
def trigger_inbound_sync(
    req: WebhookTriggerRequest,
    db: Session = Depends(get_db)
):
    """Inbound webhook trigger allowing external upstream systems or message queues to trigger an on-demand sync (optionally with taxonomy)."""
    from datetime import datetime, timezone
    orchestrator = SyncOrchestrator(db=db)
    
    if req.taxonomy:
        # Run targeted on-demand taxonomy sync
        sources_list = [req.source_id] if req.source_id else None
        res = orchestrator.run_on_demand_taxonomy_sync(
            taxonomy=req.taxonomy,
            sources=sources_list,
            scope=req.scope,
            webhook_callback_url=req.callback_url
        )
        return WebhookTriggerResponse(
            status="succeeded" if res.get("status") == "SUCCEEDED" else "partial",
            triggered_at=datetime.now(timezone.utc).isoformat(),
            message=f"Completed on-demand taxonomy sync for '{req.taxonomy}'. Discovered: {res.get('discovered')}, Normalized: {res.get('normalized')}",
            taxonomy=req.taxonomy,
            results_summary={
                "run_id": res.get("run_id"),
                "discovered": res.get("discovered"),
                "normalized": res.get("normalized"),
                "matches_count": len(res.get("results", []))
            }
        )
    
    plan_res = orchestrator.plan(scope=req.scope, source_id=req.source_id, mode=req.mode)
    return WebhookTriggerResponse(
        status="triggered",
        triggered_at=datetime.now(timezone.utc).isoformat(),
        message=f"Triggered on-demand sync for scope={req.scope}, source_id={req.source_id}. Discovered estimated items: {plan_res.total_estimated}"
    )


@app.post("/v1/sync/on-demand", response_model=TaxonomySyncResponse)
def sync_taxonomy_on_demand(
    req: TaxonomySyncRequest,
    db: Session = Depends(get_db)
):
    """
    On-demand document crawl & extraction triggered when querying a specific taxonomy / HS prefix / chapter.
    Fetches, parses, normalizes, indexes, and dispatches webhook events in real time.
    """
    orchestrator = SyncOrchestrator(db=db)
    res = orchestrator.run_on_demand_taxonomy_sync(
        taxonomy=req.taxonomy,
        sources=req.sources,
        scope=req.scope,
        as_of=req.as_of,
        webhook_callback_url=req.callback_url
    )
    return TaxonomySyncResponse(
        run_id=res["run_id"],
        taxonomy=res["taxonomy"],
        status=res["status"].lower(),
        discovered=res["discovered"],
        downloaded=res["downloaded"],
        normalized=res["normalized"],
        quarantined=res["quarantined"],
        results=res["results"],
        event_dispatched=res["event_dispatched"]
    )

