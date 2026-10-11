"""Object storage abstraction with MinIO S3 and local disk fallback."""

import os
from pathlib import Path
from typing import Optional, BinaryIO
import boto3
from botocore.exceptions import BotoCoreError, ClientError

from service.config import settings


class ObjectStore:
    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        bucket_name: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        local_fallback_dir: Optional[str] = None
    ):
        self.endpoint_url = endpoint_url or settings.object_endpoint
        self.bucket_name = bucket_name or settings.object_bucket
        self.access_key = access_key or settings.object_access_key
        self.secret_key = secret_key or settings.object_secret_key
        self.local_dir = Path(local_fallback_dir or settings.local_storage_dir)
        self.local_dir.mkdir(parents=True, exist_ok=True)
        self._s3_client = None
        self._use_local = False
        self._init_client()

    def _init_client(self):
        try:
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=settings.object_region
            )
            # Test connectivity
            self._s3_client.head_bucket(Bucket=self.bucket_name)
        except Exception:
            # Fallback to local disk storage seamlessly
            self._use_local = True

    def put_object(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Stores bytes and returns an object URI."""
        if not self._use_local and self._s3_client:
            try:
                self._s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=data,
                    ContentType=content_type
                )
                return f"s3://{self.bucket_name}/{key}"
            except Exception:
                self._use_local = True

        # Local storage fallback
        dest_path = self.local_dir / key
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(data)
        return f"file://{dest_path.resolve()}"

    def get_object(self, key: str) -> Optional[bytes]:
        """Retrieves raw bytes for a key."""
        if not self._use_local and self._s3_client:
            try:
                response = self._s3_client.get_object(Bucket=self.bucket_name, Key=key)
                return response["Body"].read()
            except Exception:
                pass

        dest_path = self.local_dir / key
        if dest_path.exists():
            return dest_path.read_bytes()
        return None

    def exists(self, key: str) -> bool:
        if not self._use_local and self._s3_client:
            try:
                self._s3_client.head_object(Bucket=self.bucket_name, Key=key)
                return True
            except Exception:
                pass

        dest_path = self.local_dir / key
        return dest_path.exists()


_global_object_store = None

def get_object_store() -> ObjectStore:
    global _global_object_store
    if _global_object_store is None:
        _global_object_store = ObjectStore()
    return _global_object_store
