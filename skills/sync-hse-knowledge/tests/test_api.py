"""Tests for FastAPI endpoints."""

from fastapi.testclient import TestClient
from service.api.main import app

client = TestClient(app)


def test_api_health_live():
    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_api_list_sources():
    resp = client.get("/v1/sources")
    assert resp.status_code == 200
    sources = resp.json()
    assert len(sources) >= 16


def test_api_sync_plan():
    resp = client.post("/v1/sync/plan", json={"scope": "vietnam-core", "mode": "incremental"})
    assert resp.status_code == 200
    data = resp.json()
    assert "target_sources" in data


def test_api_on_demand_sync():
    resp = client.post("/v1/sync/on-demand", json={"topic_or_taxonomy": "Acetone", "scope": "vietnam-core"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"


def test_api_applicability_evaluate():
    payload = {
        "facility_id": "FAC-VN-001",
        "province": "Binh Duong",
        "activities": ["store"],
        "chemicals_stored": ["toluene"],
        "chemical_storage_quantity_kg": 1500.0
    }
    resp = client.post("/v1/applicability/evaluate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["applicable_obligations"]) > 0
