"""Tests for CAS Storage and Artifact Manager."""

import tempfile
from pathlib import Path
from service.storage.artifact_manager import ArtifactManager


def test_artifact_storage_and_retrieval(db_session):
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = ArtifactManager(storage_root=Path(tmpdir))
        content = b"Content of Vietnamese HSE Regulation 84/2015/QH13"
        artifact = mgr.store_artifact(
            content_bytes=content,
            source_id="VN_GOV_LEGAL",
            source_url="https://vanban.chinhphu.vn/?docid=180606",
            canonical_url="https://vanban.chinhphu.vn/?docid=180606",
            db=db_session
        )

        assert artifact.size_bytes == len(content)
        retrieved = mgr.retrieve_artifact_bytes(artifact.content_sha256)
        assert retrieved == content
