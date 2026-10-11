"""Unit and integration tests for On-Demand Taxonomy Crawling via Webhooks & API."""

import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from service.db.session import init_db, get_db_session
from service.db.models import CrawlRun, HSNode, ClassificationRuling, LegalProvision, WebhookSubscription
from service.pipeline.orchestrator import SyncOrchestrator
from service.api.main import app
from service.cli import app as cli_app
from service.pipeline.tasks import sync_taxonomy_task

runner = CliRunner()
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()
    yield


def test_on_demand_taxonomy_sync_orchestrator():
    with get_db_session() as db:
        orch = SyncOrchestrator(db=db)
        res = orch.run_on_demand_taxonomy_sync(taxonomy="8471.30.20")

        assert res["run_id"] is not None
        assert res["taxonomy"] == "8471.30.20"
        assert res["status"] in ("SUCCEEDED", "PARTIAL")
        assert res["discovered"] > 0
        assert res["normalized"] > 0
        assert res["event_dispatched"] is True
        assert len(res["results"]) > 0

        # Check DB records
        run_obj = db.query(CrawlRun).filter_by(run_id=res["run_id"]).first()
        assert run_obj is not None
        assert run_obj.mode == "on-demand"


def test_on_demand_taxonomy_sync_keyword():
    with get_db_session() as db:
        orch = SyncOrchestrator(db=db)
        res = orch.run_on_demand_taxonomy_sync(taxonomy="bộ điều khiển PLC")

        assert res["status"] in ("SUCCEEDED", "PARTIAL")
        assert res["discovered"] > 0
        assert res["normalized"] > 0
        assert res["event_dispatched"] is True


def test_on_demand_taxonomy_sync_direct_callback():
    with get_db_session() as db:
        orch = SyncOrchestrator(db=db)
        with patch("httpx.Client.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            res = orch.run_on_demand_taxonomy_sync(
                taxonomy="8471.30.20",
                webhook_callback_url="https://subscriber.internal/on-demand-callback"
            )
            assert res["status"] in ("SUCCEEDED", "PARTIAL")
            assert mock_post.called


def test_fastapi_sync_on_demand_endpoint():
    resp = client.post("/v1/sync/on-demand", json={
        "taxonomy": "8471.30.20",
        "scope": "vietnam-core"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["taxonomy"] == "8471.30.20"
    assert data["status"] in ("succeeded", "partial")
    assert data["discovered"] > 0
    assert data["normalized"] > 0
    assert data["event_dispatched"] is True


def test_fastapi_webhook_trigger_with_taxonomy():
    resp = client.post("/v1/webhooks/trigger", json={
        "taxonomy": "8471.30.20",
        "scope": "vietnam-core"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("succeeded", "partial")
    assert data["taxonomy"] == "8471.30.20"
    assert data["results_summary"]["discovered"] > 0
    assert data["results_summary"]["normalized"] > 0


def test_cli_on_demand_command():
    result = runner.invoke(cli_app, ["on-demand", "8471.30.20", "--json"])
    assert result.exit_code == 0
    assert "8471.30.20" in result.stdout
    assert "discovered" in result.stdout


def test_celery_sync_taxonomy_task():
    res = sync_taxonomy_task(taxonomy="8471.30.20")
    assert res["status"] in ("SUCCEEDED", "PARTIAL")
    assert res["taxonomy"] == "8471.30.20"
    assert res["discovered"] > 0
