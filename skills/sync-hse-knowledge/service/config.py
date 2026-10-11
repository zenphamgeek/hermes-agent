"""Configuration settings for HSE Knowledge Platform & Sync Skill."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "HSE Knowledge Platform & Sync Skill"
    environment: str = "production"
    log_level: str = "INFO"

    # Base paths
    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = base_dir / "data"
    storage_dir: Path = data_dir / "storage" / "raw" / "sha256"
    reports_dir: Path = data_dir / "reports"
    source_registry_path: Path = base_dir / "references" / "source-catalog.yaml"

    # Database
    database_url: str = os.getenv("HSE_DATABASE_URL", f"sqlite:///{data_dir}/hse_knowledge.db")

    # Redis & Celery
    redis_url: str = os.getenv("HSE_REDIS_URL", "redis://localhost:6379/1")

    # Security & Webhooks
    webhook_secret: str = os.getenv("HSE_WEBHOOK_SECRET", "default_hse_webhook_secret_2026")
    default_request_timeout: float = 30.0
    default_max_retries: int = 3
    circuit_breaker_error_threshold: int = 5
    circuit_breaker_cooldown_seconds: int = 60

    class Config:
        env_prefix = "HSE_"
        case_sensitive = False


settings = Settings()

# Ensure directories exist
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.storage_dir.mkdir(parents=True, exist_ok=True)
settings.reports_dir.mkdir(parents=True, exist_ok=True)
