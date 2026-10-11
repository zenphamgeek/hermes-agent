"""Test source registry validation and loading."""

import pytest
from service.core.registry import SourceRegistry, SourceDefinition, BrowserRenderConfig


def test_registry_loading(registry):
    sources = registry.list_sources()
    assert len(sources) >= 6
    source_ids = [s.id for s in sources]
    assert "VN_GOV_LEGAL" in source_ids
    assert "VN_VBPL" in source_ids
    assert "VN_CUSTOMS_TARIFF" in source_ids
    assert "VN_CUSTOMS_RULINGS" in source_ids
    assert "VN_VNTR" in source_ids
    assert "ASEAN_AHTN" in source_ids


def test_registry_validation(registry):
    issues = registry.validate_all()
    assert len(issues) == 0


def test_prohibited_stealth_validation():
    with pytest.raises(ValueError, match="evasion techniques are prohibited"):
        BrowserRenderConfig(stealth=True)

    with pytest.raises(ValueError, match="evasion techniques are prohibited"):
        BrowserRenderConfig(solve_interactive_challenge=True)


def test_registry_sync_to_db(registry, db_session):
    registry.sync_to_db(db_session)
    from service.db.models import Source
    db_sources = db_session.query(Source).all()
    assert len(db_sources) >= 6
