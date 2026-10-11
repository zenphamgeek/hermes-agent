"""Configuration settings for HS Knowledge Sync."""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

SKILL_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HS_", extra="ignore")

    # Database
    database_url: str = os.getenv(
        "HS_DATABASE_URL",
        f"sqlite:///{SKILL_DIR}/data/hs_knowledge.db"
    )
    
    # Redis
    redis_url: str = os.getenv("HS_REDIS_URL", "redis://localhost:6379/0")
    
    # Object Storage (MinIO / S3 or Local Disk fallback)
    object_endpoint: str = os.getenv("HS_OBJECT_ENDPOINT", "http://localhost:9000")
    object_bucket: str = os.getenv("HS_OBJECT_BUCKET", "hs-knowledge-raw")
    object_access_key: str = os.getenv("HS_OBJECT_ACCESS_KEY", "minio_admin")
    object_secret_key: str = os.getenv("HS_OBJECT_SECRET_KEY", "minio_password")
    object_region: str = os.getenv("HS_OBJECT_REGION", "us-east-1")
    local_storage_dir: str = os.getenv("HS_LOCAL_STORAGE_DIR", str(SKILL_DIR / "data" / "storage"))

    # Source Registry
    source_registry_path: str = os.getenv(
        "HS_SOURCE_REGISTRY_PATH",
        str(SKILL_DIR / "references" / "source-catalog.yaml")
    )
    
    # Embedding / LLM
    embedding_provider: str = os.getenv("HS_EMBEDDING_PROVIDER", "lmstudio")
    embedding_endpoint: str = os.getenv("HS_EMBEDDING_ENDPOINT", "http://10.123.214.1:1234/v1")
    embedding_model: str = os.getenv("HS_EMBEDDING_MODEL", "text-embedding-nomic-embed-text-v1.5")
    
    # Resilience Lab
    resilience_lab_enabled: bool = os.getenv("HS_RESILIENCE_LAB_ENABLED", "false").lower() == "true"
    resilience_lab_allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    
    # General
    log_level: str = os.getenv("HS_LOG_LEVEL", "INFO")


settings = Settings()
