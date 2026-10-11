"""Test 6 P0 Source Adapters (Section 20.1, AC-004)."""

import pytest
from service.adapters.factory import get_adapter, list_registered_adapters


def test_registered_adapters():
    adapters = list_registered_adapters()
    assert "VN_GOV_LEGAL" in adapters
    assert "VN_VBPL" in adapters
    assert "VN_CUSTOMS_TARIFF" in adapters
    assert "VN_CUSTOMS_RULINGS" in adapters
    assert "VN_VNTR" in adapters
    assert "ASEAN_AHTN" in adapters


def test_adapter_discovery_and_canonicalization():
    for sid in ["VN_GOV_LEGAL", "VN_VBPL", "VN_CUSTOMS_TARIFF", "VN_CUSTOMS_RULINGS", "VN_VNTR", "ASEAN_AHTN"]:
        adapter = get_adapter(sid)
        assert adapter is not None
        health = adapter.healthcheck()
        assert health.is_healthy is True

        page = adapter.discover(cursor="1", limit=10)
        assert len(page.candidates) > 0
        for cand in page.candidates:
            assert cand.url.startswith("http")
            assert cand.canonical_url.startswith("http")
            assert "?" not in cand.canonical_url or "utm_" not in cand.canonical_url
