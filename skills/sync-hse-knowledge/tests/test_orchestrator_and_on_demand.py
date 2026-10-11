"""Tests for Sync Orchestrator and On-Demand Taxonomy Crawling."""

from service.pipeline.orchestrator import SyncOrchestrator


def test_orchestrator_plan(db_session, registry):
    orchestrator = SyncOrchestrator(registry=registry)
    plan = orchestrator.plan(scope="vietnam-core", mode="incremental", db=db_session)
    assert len(plan.target_sources) >= 8
    assert "VN_GOV_LEGAL" in plan.target_sources


def test_orchestrator_sync_run(db_session, registry):
    orchestrator = SyncOrchestrator(registry=registry)
    run = orchestrator.run_sync(scope="vietnam-core", mode="incremental", db=db_session)
    assert run.status == "SUCCEEDED"
    assert run.items_discovered > 0
    assert run.items_normalized > 0


def test_orchestrator_on_demand_sync(db_session, registry):
    orchestrator = SyncOrchestrator(registry=registry)
    res = orchestrator.sync_on_demand(topic_or_taxonomy="Acetone", scope="vietnam-core", db=db_session)
    assert res["status"] == "success"
    assert res["synced_count"] > 0
