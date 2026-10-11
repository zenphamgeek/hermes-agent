"""Tests for Source Adapters."""

from service.adapters.factory import get_adapter


def test_vietnam_p0_adapters():
    sources = [
        "VN_GOV_LEGAL", "VN_VBPL", "VN_OSH_LEGAL", "VN_HEALTH_OCC",
        "VN_ENV_LEGAL", "VN_CHEMICALS", "VN_FIRE_RESCUE", "VN_QCVN"
    ]
    for s_id in sources:
        adapter = get_adapter(s_id)
        assert adapter is not None, f"Adapter for {s_id} is missing"
        page = adapter.discover()
        assert len(page.items) > 0, f"Adapter {s_id} returned 0 items"


def test_international_adapters():
    sources = ["UN_GHS", "ILO_WHO_ICSC", "IFC_EHS", "US_NIOSH_NPG", "US_OSHA", "ISO_14001"]
    for s_id in sources:
        adapter = get_adapter(s_id)
        assert adapter is not None
        page = adapter.discover()
        assert len(page.items) > 0
