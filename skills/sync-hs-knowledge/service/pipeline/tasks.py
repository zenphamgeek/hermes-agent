"""Celery async task worker definitions for HS Knowledge Sync."""

import logging
from typing import Optional, Dict, Any

from celery import Celery
from service.config import settings
from service.db.session import get_db_session, init_db
from service.pipeline.orchestrator import SyncOrchestrator

logger = logging.getLogger(__name__)

# Initialize Celery app with Redis broker and backend
celery_app = Celery(
    "hs_sync_tasks",
    broker=settings.redis_url,
    backend=settings.redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=7200,  # 2 hours hard limit
    task_soft_time_limit=3600,  # 1 hour soft limit
)


@celery_app.task(name="tasks.sync_source", bind=True, max_retries=3)
def sync_source_task(self, source_id: str, scope: str = "vietnam-core", mode: str = "incremental") -> Dict[str, Any]:
    """Asynchronously synchronizes a specific source."""
    logger.info("Starting sync_source_task for source_id=%s, mode=%s", source_id, mode)
    init_db()
    try:
        with get_db_session() as db:
            orchestrator = SyncOrchestrator(db=db)
            result = orchestrator.run_sync(scope=scope, source_id=source_id, mode=mode)
            return result.model_dump()
    except Exception as exc:
        logger.error("Error in sync_source_task: %s", exc, exc_info=True)
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="tasks.sync_scope", bind=True)
def sync_scope_task(self, scope: str = "vietnam-core", mode: str = "incremental") -> Dict[str, Any]:
    """Asynchronously synchronizes all sources in a scope."""
    logger.info("Starting sync_scope_task for scope=%s, mode=%s", scope, mode)
    init_db()
    with get_db_session() as db:
        orchestrator = SyncOrchestrator(db=db)
        result = orchestrator.run_sync(scope=scope, mode=mode)
        return result.model_dump()


@celery_app.task(name="tasks.reconcile_full", bind=True)
def reconcile_full_task(self, scope: str = "vietnam-core") -> Dict[str, Any]:
    """Asynchronously runs full reconciliation across target scope."""
    logger.info("Starting reconcile_full_task for scope=%s", scope)
    init_db()
    with get_db_session() as db:
        orchestrator = SyncOrchestrator(db=db)
        result = orchestrator.run_sync(scope=scope, mode="reconcile")
        return result.model_dump()


@celery_app.task(name="tasks.reparse_artifacts", bind=True)
def reparse_artifacts_task(self, parser_name: Optional[str] = None) -> Dict[str, Any]:
    """Asynchronously re-parses all stored artifacts after parser updates."""
    logger.info("Starting reparse_artifacts_task with parser=%s", parser_name)
    init_db()
    with get_db_session() as db:
        orchestrator = SyncOrchestrator(db=db)
        reparsed_count = orchestrator.reparse_all(parser_name=parser_name)
        return {"reparsed_artifacts": reparsed_count, "status": "completed"}


@celery_app.task(name="tasks.periodic_health_check")
def periodic_health_check_task() -> Dict[str, Any]:
    """Periodic health check across infrastructure and sources."""
    init_db()
    with get_db_session() as db:
        from service.core.registry import load_source_registry
        from service.core.entitlement import EntitlementManager
        registry = load_source_registry()
        manager = EntitlementManager(registry)
        report = manager.get_readiness_report(db=db)
        return {
            "status": "healthy",
            "sources_count": len(registry.list_sources()),
            "readiness_report": [r.model_dump() for r in report]
        }


@celery_app.task(name="tasks.sync_taxonomy", bind=True)
def sync_taxonomy_task(
    self,
    taxonomy: str,
    sources: Optional[list] = None,
    scope: str = "vietnam-core",
    as_of: Optional[str] = None,
    webhook_callback_url: Optional[str] = None
) -> Dict[str, Any]:
    """Asynchronously performs on-demand taxonomy crawling and extraction."""
    logger.info("Starting sync_taxonomy_task for taxonomy=%s", taxonomy)
    init_db()
    with get_db_session() as db:
        orchestrator = SyncOrchestrator(db=db)
        return orchestrator.run_on_demand_taxonomy_sync(
            taxonomy=taxonomy,
            sources=sources,
            scope=scope,
            as_of=as_of,
            webhook_callback_url=webhook_callback_url
        )

