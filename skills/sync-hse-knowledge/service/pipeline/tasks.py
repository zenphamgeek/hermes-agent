"""Celery async worker tasks for HSE sync pipeline."""

from typing import Optional, Dict, Any
from celery import Celery

from service.config import settings
from service.db.session import get_db_session
from service.pipeline.orchestrator import SyncOrchestrator

celery_app = Celery("hse_sync", broker=settings.redis_url, backend=settings.redis_url)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_routes={
        "tasks.sync_scope": {"queue": "sync"},
        "tasks.sync_on_demand": {"queue": "on_demand"},
        "tasks.reconcile_graph": {"queue": "maintenance"}
    }
)


@celery_app.task(name="tasks.sync_scope")
def sync_scope_task(scope: str = "vietnam-core", mode: str = "incremental") -> Dict[str, Any]:
    with get_db_session() as db:
        orchestrator = SyncOrchestrator()
        run = orchestrator.run_sync(scope=scope, mode=mode, db=db)
        return {
            "run_id": run.run_id,
            "status": run.status,
            "items_normalized": run.items_normalized
        }


@celery_app.task(name="tasks.sync_on_demand")
def sync_on_demand_task(topic_or_taxonomy: str, scope: str = "vietnam-core", callback_url: Optional[str] = None) -> Dict[str, Any]:
    with get_db_session() as db:
        orchestrator = SyncOrchestrator()
        result = orchestrator.sync_on_demand(topic_or_taxonomy=topic_or_taxonomy, scope=scope, callback_url=callback_url, db=db)
        return result
