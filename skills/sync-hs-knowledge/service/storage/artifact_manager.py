"""Artifact Manager implementing content-addressed immutable storage and provenance tracking."""

import hashlib
from typing import Optional, Tuple
from pydantic import BaseModel
from sqlalchemy.orm import Session

from service.db.models import RawArtifact, ArtifactProvenance
from .object_store import ObjectStore, get_object_store


class StoredArtifact(BaseModel):
    artifact_id: str
    content_sha256: str
    object_uri: str
    mime_type: str
    size_bytes: int
    is_duplicate: bool


class ArtifactManager:
    def __init__(self, object_store: Optional[ObjectStore] = None):
        self.store = object_store or get_object_store()

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def get_object_key(sha256_hash: str) -> str:
        """Rule: raw/sha256/{first2}/{next2}/{full_sha256}"""
        return f"raw/sha256/{sha256_hash[:2]}/{sha256_hash[2:4]}/{sha256_hash}"

    def store_artifact(
        self,
        data: bytes,
        mime_type: str,
        source_id: str,
        source_url: str,
        canonical_url: str,
        db: Session
    ) -> StoredArtifact:
        sha256_hash = self.compute_sha256(data)
        size_bytes = len(data)
        object_key = self.get_object_key(sha256_hash)

        existing = db.query(RawArtifact).filter_by(content_sha256=sha256_hash).first()
        is_duplicate = False

        if existing:
            artifact_id = existing.artifact_id
            object_uri = existing.object_uri
            is_duplicate = True
        else:
            object_uri = self.store.put_object(object_key, data, content_type=mime_type)
            raw_artifact = RawArtifact(
                content_sha256=sha256_hash,
                object_uri=object_uri,
                mime_type=mime_type,
                size_bytes=size_bytes,
                malware_status="CLEAN"
            )
            db.add(raw_artifact)
            db.flush()
            artifact_id = raw_artifact.artifact_id

        # Always record provenance (FR-032)
        provenance = ArtifactProvenance(
            artifact_id=artifact_id,
            source_id=source_id,
            source_url=source_url,
            canonical_url=canonical_url
        )
        db.add(provenance)
        db.commit()

        return StoredArtifact(
            artifact_id=artifact_id,
            content_sha256=sha256_hash,
            object_uri=object_uri,
            mime_type=mime_type,
            size_bytes=size_bytes,
            is_duplicate=is_duplicate
        )

    def retrieve_artifact_bytes(self, content_sha256: str) -> Optional[bytes]:
        object_key = self.get_object_key(content_sha256)
        return self.store.get_object(object_key)
