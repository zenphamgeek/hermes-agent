"""FastAPI REST API for Deterministic HSE Knowledge Platform."""

from datetime import date
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from service.config import settings
from service.db.session import get_db, init_db
from service.core.registry import load_source_registry
from service.pipeline.orchestrator import SyncOrchestrator
from service.index.retrieval import HybridRetrievalEngine
from service.rules.dsl_engine import ApplicabilityDSLEngine
from service.rules.facility_compiler import FacilityProfileCompiler, FacilityContext
from service.webhooks.dispatcher import WebhookDispatcher, HSEEvent
from service.db.models import (
    SyncRun, Source, Document, Substance, OEL, Hazard, Control, EnvironmentalLimit,
    WebhookSubscription, ApplicabilityRule
)
from service.api.schemas import (
    SyncPlanRequest, SyncPlanResponse, SyncRunResponse, OnDemandSyncRequest,
    SourceSummary, ApplicabilityEvaluationRequest, ApplicabilityEvaluationResponse,
    SearchQueryResponse, WebhookSubscriptionCreate, WebhookSubscriptionResponse
)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Deterministic Health, Safety and Environment (HSE) Knowledge Base & Sync Engine API."
)

# Ensure DB initialized on module import
init_db()


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health/live")
def health_live():
    return {"status": "ok", "service": "hse-knowledge-service"}


@app.get("/health/ready")
def health_ready(db: Session = Depends(get_db)):
    try:
        source_count = db.query(Source).count()
        return {"status": "ready", "database": "connected", "source_count": source_count}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database not ready: {str(e)}")


@app.get("/v1/sources", response_model=List[SourceSummary])
def list_sources(db: Session = Depends(get_db)):
    registry = load_source_registry()
    return [
        SourceSummary(
            id=s.id,
            name=s.name,
            jurisdiction=s.jurisdiction,
            authority_level=s.authority_level,
            license_policy=s.license.policy,
            entitlement_required=s.license.entitlement_required,
            is_active=True
        )
        for s in registry.list_sources()
    ]


@app.post("/v1/sync/plan", response_model=SyncPlanResponse)
def plan_sync(req: SyncPlanRequest, db: Session = Depends(get_db)):
    orchestrator = SyncOrchestrator()
    res = orchestrator.plan(scope=req.scope, mode=req.mode, db=db)
    return SyncPlanResponse(
        scope=res.scope,
        mode=res.mode,
        target_sources=res.target_sources,
        estimated_workload=res.estimated_workload,
        policy_blocks=res.policy_blocks
    )


@app.post("/v1/sync/runs", response_model=SyncRunResponse)
def trigger_sync_run(req: SyncPlanRequest, db: Session = Depends(get_db)):
    orchestrator = SyncOrchestrator()
    run = orchestrator.run_sync(scope=req.scope, mode=req.mode, db=db)
    return SyncRunResponse(
        run_id=run.run_id,
        scope=run.scope,
        mode=run.mode,
        status=run.status,
        items_discovered=run.items_discovered,
        items_downloaded=run.items_downloaded,
        items_normalized=run.items_normalized,
        started_at=run.started_at,
        finished_at=run.finished_at
    )


@app.post("/v1/sync/on-demand")
def trigger_on_demand_sync(req: OnDemandSyncRequest, db: Session = Depends(get_db)):
    orchestrator = SyncOrchestrator()
    res = orchestrator.sync_on_demand(
        topic_or_taxonomy=req.topic_or_taxonomy,
        scope=req.scope,
        callback_url=req.callback_url,
        db=db
    )
    return res


@app.post("/v1/applicability/evaluate", response_model=ApplicabilityEvaluationResponse)
def evaluate_applicability(req: ApplicabilityEvaluationRequest, db: Session = Depends(get_db)):
    ctx = FacilityContext(
        facility_id=req.facility_id,
        province=req.province,
        activities=req.activities,
        chemicals_stored=req.chemicals_stored,
        chemical_storage_quantity_kg=req.chemical_storage_quantity_kg,
        wastewater_flow_m3_day=req.wastewater_flow_m3_day,
        has_boiler=req.has_boiler
    )
    facts = FacilityProfileCompiler.compile_facts(ctx)

    # Seed sample applicability rule if none in DB
    rule = db.query(ApplicabilityRule).filter_by(code="VN_CHEM_SPECIAL_CONTROL_STORAGE").first()
    if not rule:
        rule = ApplicabilityRule(
            code="VN_CHEM_SPECIAL_CONTROL_STORAGE",
            jurisdiction="VN",
            expression={
                "when": {
                    "all": [
                        {"fact": "activity.type", "op": "in", "value": ["store", "use", "trade"]},
                        {"fact": "chemical.storage_quantity_kg", "op": "gte", "value": 1000.0}
                    ]
                },
                "then": {
                    "obligations": ["OBL_VN_CHEM_SECURITY_PLAN", "OBL_VN_CHEM_SPECIAL_CONTROL_REPORT"]
                }
            },
            required_facts=["activity.type", "chemical.storage_quantity_kg"]
        )
        db.add(rule)
        db.commit()

    trace = ApplicabilityDSLEngine.evaluate_rule(rule, facts)

    return ApplicabilityEvaluationResponse(
        facility_id=req.facility_id,
        as_of=req.as_of or date.today(),
        applicable_obligations=trace.obligations if trace.outcome == "applicable" else [],
        missing_facts=trace.missing_facts,
        decision_traces=[trace.model_dump()]
    )


@app.get("/v1/search", response_model=SearchQueryResponse)
def search_knowledge(
    q: str = Query(..., description="Query search term"),
    as_of: Optional[date] = Query(None, description="Temporal effective date query"),
    entity_type: Optional[str] = Query(None, description="document, obligation, substance, oel"),
    db: Session = Depends(get_db)
):
    retriever = HybridRetrievalEngine(db)
    results = retriever.search(query=q, as_of=as_of, entity_type=entity_type)
    return SearchQueryResponse(
        query=q,
        as_of=as_of or date.today(),
        total_results=len(results),
        results=[r.model_dump() for r in results]
    )


@app.get("/v1/chemicals")
def query_chemicals(cas: Optional[str] = None, db: Session = Depends(get_db)):
    stmt = db.query(Substance)
    if cas:
        stmt = stmt.filter(Substance.cas_number == cas)
    subs = stmt.limit(50).all()
    return [{"cas_number": s.cas_number, "chemical_name_en": s.chemical_name_en, "chemical_name_vi": s.chemical_name_vi} for s in subs]


@app.get("/v1/oels")
def query_oels(substance_cas: Optional[str] = None, db: Session = Depends(get_db)):
    stmt = db.query(OEL)
    if substance_cas:
        sub = db.query(Substance).filter_by(cas_number=substance_cas).first()
        if sub:
            stmt = stmt.filter(OEL.substance_id == sub.substance_id)
    oels = stmt.limit(50).all()
    return [{"jurisdiction": o.jurisdiction, "twa_mg_m3": o.twa_mg_m3, "stel_mg_m3": o.stel_mg_m3, "source_doc": o.source_doc_number} for o in oels]


@app.post("/v1/webhooks/subscriptions", response_model=WebhookSubscriptionResponse)
def create_webhook_subscription(sub_in: WebhookSubscriptionCreate, db: Session = Depends(get_db)):
    sub = WebhookSubscription(
        name=sub_in.name,
        target_url=sub_in.target_url,
        secret_token=sub_in.secret_token,
        event_types=sub_in.event_types
    )
    db.add(sub)
    db.commit()
    return WebhookSubscriptionResponse(
        subscription_id=sub.subscription_id,
        name=sub.name,
        target_url=sub.target_url,
        event_types=sub.event_types,
        is_active=sub.is_active,
        created_at=sub.created_at
    )


@app.get("/v1/webhooks/subscriptions", response_model=List[WebhookSubscriptionResponse])
def list_webhook_subscriptions(db: Session = Depends(get_db)):
    subs = db.query(WebhookSubscription).all()
    return [
        WebhookSubscriptionResponse(
            subscription_id=s.subscription_id,
            name=s.name,
            target_url=s.target_url,
            event_types=s.event_types,
            is_active=s.is_active,
            created_at=s.created_at
        )
        for s in subs
    ]
