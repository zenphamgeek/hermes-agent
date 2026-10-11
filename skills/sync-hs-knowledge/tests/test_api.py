"""Tests for FastAPI REST API endpoints (FR-010 - FR-094)."""

import pytest
from fastapi.testclient import TestClient
from service.api.main import app
from service.db.session import init_db

client = TestClient(app)


def test_api_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"


def test_api_list_sources():
    response = client.get("/v1/sources")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 6
    source_ids = [s["id"] for s in data]
    assert "VN_GOV_LEGAL" in source_ids
    assert "VN_CUSTOMS_TARIFF" in source_ids


def test_api_get_source_health():
    response = client.get("/v1/sources/VN_GOV_LEGAL/health")
    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == "VN_GOV_LEGAL"
    assert data["is_healthy"] is True


def test_api_entitlements_validate():
    response = client.get("/v1/entitlements/validate")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    gated = next((item for item in data if item["source_id"] == "WCO_HS_CONTENT"), None)
    assert gated is not None
    assert gated["ready_for_full_sync"] is False


def test_api_sync_plan():
    response = client.post("/v1/sync/plan", json={"scope": "vietnam-core", "mode": "incremental"})
    assert response.status_code == 200
    data = response.json()
    assert data["scope"] == "vietnam-core"
    assert data["total_estimated"] > 0
    assert len(data["sources"]) >= 5


def test_api_sync_run_and_search():
    # 1. Trigger sync run on VN_CUSTOMS_RULINGS
    response = client.post(
        "/v1/sync/runs",
        json={"scope": "vietnam-core", "source_id": "VN_CUSTOMS_RULINGS", "mode": "incremental"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "succeeded"
    assert data["discovered"] == 2
    assert data["normalized"] == 2

    # 2. Search
    search_resp = client.get("/v1/search?query=8471.30.20&as_of=2026-08-21")
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["query"] == "8471.30.20"
    assert len(search_data["results"]) > 0
    assert search_data["results"][0]["citation"]["section"] is not None
