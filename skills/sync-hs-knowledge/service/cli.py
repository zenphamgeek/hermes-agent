"""Command-line interface for HS Knowledge Sync (FR-001 - FR-116, Section 18)."""

import json
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any
import typer
from rich.console import Console
from rich.table import Table

from service.db.session import get_db_session, init_db
from service.db.models import CrawlRun, QualityIssue, HSNode
from service.core.registry import load_source_registry
from service.core.entitlement import EntitlementManager
from service.pipeline.orchestrator import SyncOrchestrator
from service.index.retrieval import HybridRetriever
from service.acquisition.resilience_lab.simulator import ResilienceLabSimulator

app = typer.Typer(help="HS Knowledge Sync CLI Tool (`hs-sync`)")
sources_app = typer.Typer(help="Source registry commands")
license_app = typer.Typer(help="License & Entitlement commands")
acquisition_app = typer.Typer(help="Acquisition gateway and circuit breaker commands")
resilience_app = typer.Typer(help="WAF/CAPTCHA Resilience Lab commands")
quality_app = typer.Typer(help="Data quality queue commands")
db_app = typer.Typer(help="Database maintenance commands")
hs_app = typer.Typer(help="HS Code hierarchy inspection")
webhook_app = typer.Typer(help="Webhook subscription and event delivery commands")

app.add_typer(sources_app, name="sources")
app.add_typer(license_app, name="license")
app.add_typer(acquisition_app, name="acquisition")
app.add_typer(resilience_app, name="resilience-lab")
app.add_typer(quality_app, name="quality")
app.add_typer(db_app, name="db")
app.add_typer(hs_app, name="hs")
app.add_typer(webhook_app, name="webhook")

console = Console()


def output_result(data: Any, json_output: bool):
    if json_output:
        if hasattr(data, "model_dump"):
            print(json.dumps(data.model_dump(), ensure_ascii=False, indent=2))
        elif hasattr(data, "dict"):
            print(json.dumps(data.dict(), ensure_ascii=False, indent=2))
        elif isinstance(data, (dict, list)):
            print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
        else:
            print(json.dumps({"result": str(data)}, ensure_ascii=False, indent=2))
    else:
        if isinstance(data, dict):
            for k, v in data.items():
                console.print(f"[bold cyan]{k}:[/bold cyan] {v}")
        elif isinstance(data, list):
            for item in data:
                console.print(item)
        else:
            console.print(str(data))


# -------------------------------------------------------------
# Top-level commands
# -------------------------------------------------------------

@app.command(name="plan")
def plan_sync(
    scope: str = typer.Option("vietnam-core", "--scope", help="Sync scope"),
    source: Optional[str] = typer.Option(None, "--source", help="Specific source ID"),
    mode: str = typer.Option("incremental", "--mode", help="incremental or full"),
    json_output: bool = typer.Option(True, "--json/--no-json", help="Output JSON format")
):
    """Generates a dry-run sync execution plan without mutating DB."""
    init_db()
    with get_db_session() as db:
        orch = SyncOrchestrator(db=db)
        res = orch.plan(scope=scope, source_id=source, mode=mode)
        output_result(res, json_output)


@app.command(name="run")
def run_sync(
    scope: str = typer.Option("vietnam-core", "--scope", help="Sync scope"),
    source: Optional[str] = typer.Option(None, "--source", help="Specific source ID"),
    mode: str = typer.Option("incremental", "--mode", help="incremental or full"),
    json_output: bool = typer.Option(True, "--json/--no-json", help="Output JSON format")
):
    """Executes a synchronization run across target sources."""
    init_db()
    with get_db_session() as db:
        orch = SyncOrchestrator(db=db)
        res = orch.run_sync(scope=scope, source_id=source, mode=mode)
        output_result(res, json_output)
        if res.status == "failed":
            sys.exit(4)
        elif res.quarantined > 0:
            sys.exit(5)


@app.command(name="resume")
def resume_sync(
    run_id: str = typer.Argument(..., help="Run ID to resume"),
    json_output: bool = typer.Option(True, "--json/--no-json")
):
    """Resumes an interrupted sync run from checkpoint."""
    init_db()
    with get_db_session() as db:
        orch = SyncOrchestrator(db=db)
        run_obj = db.query(CrawlRun).filter_by(run_id=run_id).first()
        if not run_obj:
            output_result({"error": f"Run ID {run_id} not found"}, json_output)
            sys.exit(2)
        res = orch.run_sync(scope=run_obj.scope, mode=run_obj.mode, existing_run_id=run_id)
        output_result(res, json_output)


@app.command(name="search")
def search_cmd(
    query: str = typer.Argument(..., help="Search terms or HS code"),
    as_of: Optional[str] = typer.Option(None, "--as-of", help="Temporal date YYYY-MM-DD"),
    limit: int = typer.Option(10, "--limit", help="Max results"),
    json_output: bool = typer.Option(True, "--json/--no-json")
):
    """Performs hybrid lexical/semantic retrieval with temporal filter."""
    init_db()
    with get_db_session() as db:
        retriever = HybridRetriever(db=db)
        res = retriever.search(query=query, as_of=as_of, limit=limit)
        output_result(res, json_output)


@app.command(name="on-demand")
def on_demand_sync_cmd(
    taxonomy: str = typer.Argument(..., help="Taxonomy / HS prefix / Chapter / Commodity keyword (e.g. 8471.30.20, chapter:84, PLC)"),
    scope: str = typer.Option("vietnam-core", "--scope", help="Sync scope"),
    sources: Optional[str] = typer.Option(None, "--sources", "-s", help="Comma-separated source IDs"),
    as_of: Optional[str] = typer.Option(None, "--as-of", help="Temporal date YYYY-MM-DD"),
    callback_url: Optional[str] = typer.Option(None, "--callback-url", help="Optional webhook callback URL"),
    json_output: bool = typer.Option(True, "--json/--no-json")
):
    """Performs real-time on-demand document crawling and extraction for a specific taxonomy."""
    init_db()
    source_list = [s.strip() for s in sources.split(",") if s.strip()] if sources else None
    with get_db_session() as db:
        orch = SyncOrchestrator(db=db)
        res = orch.run_on_demand_taxonomy_sync(
            taxonomy=taxonomy,
            sources=source_list,
            scope=scope,
            as_of=as_of,
            webhook_callback_url=callback_url
        )
        output_result(res, json_output)



@app.command(name="health")
def health_cmd(json_output: bool = typer.Option(True, "--json/--no-json")):
    """Checks database, storage, and infrastructure health."""
    try:
        init_db()
        with get_db_session() as db:
            registry = load_source_registry()
            status = {
                "status": "healthy",
                "database": "connected",
                "sources_configured": len(registry.list_sources()),
                "timestamp": str(datetime.now())
            }
            output_result(status, json_output)
    except Exception as e:
        output_result({"status": "unhealthy", "error": str(e)}, json_output)
        sys.exit(7)


# -------------------------------------------------------------
# Sources Subcommands
# -------------------------------------------------------------

@sources_app.command(name="list")
def list_sources_cmd(json_output: bool = typer.Option(True, "--json/--no-json")):
    """Lists all configured sources in catalog."""
    registry = load_source_registry()
    sources = [s.model_dump() for s in registry.list_sources()]
    output_result(sources, json_output)


@sources_app.command(name="validate")
def validate_sources_cmd(json_output: bool = typer.Option(True, "--json/--no-json")):
    """Validates source catalog YAML schema."""
    try:
        registry = load_source_registry()
        issues = registry.validate_all()
        if issues:
            output_result({"valid": False, "issues": issues}, json_output)
            sys.exit(2)
        output_result({"valid": True, "sources_count": len(registry.list_sources())}, json_output)
    except Exception as e:
        output_result({"valid": False, "error": str(e)}, json_output)
        sys.exit(2)


# -------------------------------------------------------------
# License Subcommands
# -------------------------------------------------------------

@license_app.command(name="readiness")
def license_readiness_cmd(json_output: bool = typer.Option(True, "--json/--no-json")):
    """Displays readiness of gated/licensed sources."""
    init_db()
    with get_db_session() as db:
        registry = load_source_registry()
        manager = EntitlementManager(registry)
        report = [r.model_dump() for r in manager.get_readiness_report(db=db)]
        output_result(report, json_output)


# -------------------------------------------------------------
# Resilience Lab Subcommands
# -------------------------------------------------------------

@resilience_app.command(name="run")
def run_resilience_lab_cmd(
    scenario: str = typer.Option("challenge-matrix", "--scenario", help="challenge-matrix or scenario name"),
    json_output: bool = typer.Option(True, "--json/--no-json")
):
    """Executes offline WAF and challenge resilience simulations."""
    sim = ResilienceLabSimulator()
    if scenario == "challenge-matrix":
        results = [r.model_dump() for r in sim.run_matrix()]
        all_passed = all(r["passed"] for r in results)
        output_result({"scenario": scenario, "all_passed": all_passed, "matrix": results}, json_output)
        if not all_passed:
            sys.exit(9)
    else:
        res = sim.run_scenario(scenario)
        output_result(res, json_output)
        if not res.passed:
            sys.exit(9)


# -------------------------------------------------------------
# Quality Subcommands
# -------------------------------------------------------------

@quality_app.command(name="list")
def list_quality_issues_cmd(
    severity: Optional[str] = typer.Option(None, "--severity", help="Filter by CRITICAL/HIGH/MEDIUM"),
    json_output: bool = typer.Option(True, "--json/--no-json")
):
    """Lists data quality issues in the review queue."""
    init_db()
    with get_db_session() as db:
        q = db.query(QualityIssue)
        if severity:
            q = q.filter_by(severity=severity.upper())
        issues = [
            {
                "issue_id": i.issue_id,
                "entity_type": i.entity_type,
                "entity_id": i.entity_id,
                "severity": i.severity,
                "issue_type": i.issue_type,
                "description": i.description,
                "status": i.status
            } for i in q.all()
        ]
        output_result(issues, json_output)


# -------------------------------------------------------------
# HS Code Subcommands
# -------------------------------------------------------------

@hs_app.command(name="get")
def get_hs_code_cmd(
    code: str = typer.Argument(..., help="HS Code e.g. 8471.30.20"),
    edition: str = typer.Option("2022", "--edition"),
    as_of: Optional[str] = typer.Option(None, "--as-of"),
    json_output: bool = typer.Option(True, "--json/--no-json")
):
    """Inspects an HS code node hierarchy and descriptions."""
    init_db()
    with get_db_session() as db:
        node = db.query(HSNode).filter_by(code=code).first()
        if not node:
            output_result({"error": f"HS code {code} not found"}, json_output)
            sys.exit(2)
        output_result({
            "code": node.code,
            "level": node.level,
            "parent_code": node.parent_code,
            "description_vi": node.description_vi,
            "description_en": node.description_en,
            "is_leaf": node.is_leaf
        }, json_output)


# -------------------------------------------------------------
# Database Subcommands
# -------------------------------------------------------------

@db_app.command(name="migrate")
def db_migrate_cmd(
    direction: str = typer.Option("upgrade", "--direction", help="upgrade or downgrade"),
    json_output: bool = typer.Option(True, "--json/--no-json")
):
    """Executes database schema creation and migrations."""
    init_db()
    output_result({"status": "migration_complete", "direction": direction}, json_output)


# -------------------------------------------------------------
# Webhook Subcommands
# -------------------------------------------------------------

@webhook_app.command(name="add")
def add_webhook_cmd(
    name: str = typer.Argument(..., help="Subscription name (e.g. odoo-erp)"),
    url: str = typer.Argument(..., help="Target HTTP/HTTPS webhook URL"),
    events: str = typer.Option("*", "--events", "-e", help="Comma-separated event types (e.g. hs.ruling.published,hs.tariff.changed or *)"),
    secret: Optional[str] = typer.Option(None, "--secret", "-s", help="Optional secret for HMAC signing"),
    json_output: bool = typer.Option(True, "--json/--no-json")
):
    """Registers a new outbound webhook subscription."""
    from service.webhooks.dispatcher import WebhookDispatcher
    init_db()
    event_list = [e.strip() for e in events.split(",") if e.strip()]
    with get_db_session() as db:
        dispatcher = WebhookDispatcher(db=db)
        sub = dispatcher.create_subscription(name=name, target_url=url, event_types=event_list, secret_token=secret)
        output_result({
            "status": "created",
            "subscription_id": sub.subscription_id,
            "name": sub.name,
            "target_url": sub.target_url,
            "secret_token": sub.secret_token,
            "event_types": sub.event_types,
            "is_active": sub.is_active
        }, json_output)


@webhook_app.command(name="list")
def list_webhooks_cmd(
    active_only: bool = typer.Option(False, "--active-only"),
    json_output: bool = typer.Option(True, "--json/--no-json")
):
    """Lists all registered outbound webhook subscriptions."""
    from service.webhooks.dispatcher import WebhookDispatcher
    init_db()
    with get_db_session() as db:
        dispatcher = WebhookDispatcher(db=db)
        subs = dispatcher.list_subscriptions(active_only=active_only)
        result = [
            {
                "subscription_id": s.subscription_id,
                "name": s.name,
                "target_url": s.target_url,
                "event_types": s.event_types,
                "is_active": s.is_active,
                "failure_count": s.failure_count,
                "created_at": s.created_at.isoformat() if s.created_at else None
            }
            for s in subs
        ]
        output_result(result, json_output)


@webhook_app.command(name="remove")
def remove_webhook_cmd(
    subscription_id: str = typer.Argument(..., help="Subscription ID to delete"),
    json_output: bool = typer.Option(True, "--json/--no-json")
):
    """Removes a webhook subscription."""
    from service.webhooks.dispatcher import WebhookDispatcher
    init_db()
    with get_db_session() as db:
        dispatcher = WebhookDispatcher(db=db)
        success = dispatcher.delete_subscription(subscription_id)
        if not success:
            output_result({"error": f"Subscription '{subscription_id}' not found"}, json_output)
            sys.exit(2)
        output_result({"status": "deleted", "subscription_id": subscription_id}, json_output)


@webhook_app.command(name="test")
def test_webhook_cmd(
    subscription_id: str = typer.Argument(..., help="Subscription ID to test"),
    json_output: bool = typer.Option(True, "--json/--no-json")
):
    """Sends a ping test event to a registered webhook subscription."""
    from service.webhooks.dispatcher import WebhookDispatcher
    init_db()
    with get_db_session() as db:
        dispatcher = WebhookDispatcher(db=db)
        try:
            log = dispatcher.test_subscription(subscription_id)
            output_result({
                "delivery_id": log.delivery_id,
                "subscription_id": log.subscription_id,
                "status": log.status,
                "response_status_code": log.response_status_code,
                "duration_ms": log.duration_ms,
                "response_body": log.response_body
            }, json_output)
        except Exception as e:
            output_result({"error": str(e)}, json_output)
            sys.exit(2)


@webhook_app.command(name="deliver")
def deliver_webhook_cmd(
    event_type: str = typer.Argument(..., help="Event type (e.g. hs.ruling.published)"),
    payload: str = typer.Argument(..., help="JSON payload string or path to JSON file"),
    json_output: bool = typer.Option(True, "--json/--no-json")
):
    """Manually dispatches an event to all matching subscribers."""
    from service.webhooks.dispatcher import WebhookDispatcher
    import os
    init_db()
    if os.path.exists(payload):
        with open(payload, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.loads(payload)

    with get_db_session() as db:
        dispatcher = WebhookDispatcher(db=db)
        logs = dispatcher.dispatch_event(event_type=event_type, data=data)
        output_result({
            "event_type": event_type,
            "subscribers_notified": len(logs),
            "deliveries": [
                {
                    "delivery_id": l.delivery_id,
                    "subscription_id": l.subscription_id,
                    "status": l.status,
                    "response_status_code": l.response_status_code
                }
                for l in logs
            ]
        }, json_output)
