"""Tests for async tasks and orchestrator resume/reparse capabilities."""

import pytest
from service.db.session import init_db, get_db_session
from service.pipeline.tasks import sync_source_task, sync_scope_task, reconcile_full_task, periodic_health_check_task
from service.pipeline.orchestrator import SyncOrchestrator


def test_async_sync_source_task():
    result = sync_source_task("VN_CUSTOMS_RULINGS", scope="vietnam-core", mode="incremental")
    assert result["status"] == "succeeded"
    assert result["discovered"] == 2
    assert "checkpoint" in result


def test_periodic_health_check_task():
    result = periodic_health_check_task()
    assert result["status"] == "healthy"
    assert result["sources_count"] >= 6
    assert len(result["readiness_report"]) >= 6


def test_orchestrator_resume_flow():
    init_db()
    with get_db_session() as db:
        orch = SyncOrchestrator(db=db)
        
        # 1. Start a run
        first_run = orch.run_sync(scope="vietnam-core", source_id="VN_CUSTOMS_RULINGS", mode="incremental")
        assert first_run.status == "succeeded"
        run_id = first_run.run_id

        # 2. Resume the existing run
        resumed_run = orch.run_sync(scope="vietnam-core", source_id="VN_CUSTOMS_RULINGS", mode="incremental", existing_run_id=run_id)
        assert resumed_run.status == "succeeded"
        assert resumed_run.run_id == run_id


def test_orchestrator_reparse_flow():
    init_db()
    with get_db_session() as db:
        orch = SyncOrchestrator(db=db)
        count = orch.reparse_all(parser_name="html_parser")
        assert isinstance(count, int)
        assert count >= 0
