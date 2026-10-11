"""Test content-addressed immutable artifact storage (FR-030, FR-031, FR-032)."""

import pytest
from service.storage.object_store import ObjectStore
from service.storage.artifact_manager import ArtifactManager


def test_artifact_storage_and_deduplication(db_session, tmp_path):
    store = ObjectStore(local_fallback_dir=str(tmp_path))
    manager = ArtifactManager(object_store=store)

    data = b"Official Circular 85/2026/TT-BTC Sample Content"
    url1 = "https://vanban.chinhphu.vn/doc1"
    url2 = "https://vbpl.vn/doc1-mirror"

    # Store first time
    res1 = manager.store_artifact(
        data=data,
        mime_type="text/plain",
        source_id="VN_GOV_LEGAL",
        source_url=url1,
        canonical_url=url1,
        db=db_session
    )
    assert res1.is_duplicate is False

    # Store second time with different URL but same bytes
    res2 = manager.store_artifact(
        data=data,
        mime_type="text/plain",
        source_id="VN_VBPL",
        source_url=url2,
        canonical_url=url2,
        db=db_session
    )
    assert res2.is_duplicate is True
    assert res1.artifact_id == res2.artifact_id
    assert res1.content_sha256 == res2.content_sha256

    # Verify retrieval
    retrieved = manager.retrieve_artifact_bytes(res1.content_sha256)
    assert retrieved == data
