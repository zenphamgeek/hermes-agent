"""Unit tests for Source Registry."""

def test_source_registry_validation(registry):
    errors = registry.validate()
    assert len(errors) == 0, f"Expected 0 validation errors, got {errors}"


def test_source_registry_sync_db(registry, db_session):
    count = registry.sync_to_db(db_session)
    assert count == 16, f"Expected 16 sources synced, got {count}"


def test_source_registry_lookup(registry):
    s = registry.get_source("VN_GOV_LEGAL")
    assert s is not None
    assert s.authority_level == "A1_MANDATORY_LAW"
    assert "vanban.chinhphu.vn" in s.allowed_hosts
