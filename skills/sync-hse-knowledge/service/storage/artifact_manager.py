"""Content-Addressable Storage (CAS) Artifact Manager with SHA-256 integrity."""

import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, Tuple
from pydantic import BaseModel
from sqlalchemy.orm import Session

from service.config import settings
from service.db.models import RawArtifact, ArtifactProvenance


class StoredArtifact(BaseModel):
    artifact_id: str
    content_sha256: str
    object_uri: str
    mime_type: str
    size_bytes: int
    malware_status: str = "CLEAN"


class ArtifactManager:
    def __init__(self, storage_root: Optional[Path] = None):
        self.storage_root = storage_root or settings.storage_dir
        self.storage_root.mkdir(parents=True, exist_ok=True)

    def compute_sha256(self, content_bytes: bytes) -> str:
        return hashlib.sha256(content_bytes).hexdigest()

    def store_artifact(
        self,
        content_bytes: bytes,
        source_id: str,
        source_url: str,
        canonical_url: str,
        db: Session,
        declared_mime_type: Optional[str] = None
    ) -> StoredArtifact:
        sha = self.compute_sha256(content_bytes)
        size = len(content_bytes)

        # Sharded path: <xx>/<yy>/<full_sha256>
        prefix1 = sha[:2]
        prefix2 = sha[2:4]
        target_dir = self.storage_root / prefix1 / prefix2
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / sha

        if not file_path.exists():
            with open(file_path, "wb") as f:
                f.write(content_bytes)

        mime = declared_mime_type
        if not mime or mime == "application/octet-stream":
            guessed, _ = mimetypes.guess_type(canonical_url)
            mime = guessed or "text/html"

        existing = db.query(RawArtifact).filter_by(content_sha256=sha).first()
        if not existing:
            artifact_record = RawArtifact(
                content_sha256=sha,
                object_uri=str(file_path),
                mime_type=mime,
                size_bytes=size,
                malware_status="CLEAN"
            )
            db.add(artifact_record)
            db.flush()
            artifact_id = artifact_record.artifact_id
        else:
            artifact_id = existing.artifact_id

        # Record Provenance
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
            content_sha256=sha,
            object_uri=str(file_path),
            mime_type=mime,
            size_bytes=size,
            malware_status="CLEAN"
        )

    def retrieve_artifact_bytes(self, content_sha256: str) -> Optional[bytes]:
        prefix1 = content_sha256[:2]
        prefix2 = content_sha256[2:4]
        file_path = self.storage_root / prefix1 / prefix2 / content_sha256
        if file_path.exists():
            with open(file_path, "rb") as f:
                return f.read()
        return None
