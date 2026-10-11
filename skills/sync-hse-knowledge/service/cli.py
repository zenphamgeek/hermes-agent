"""Typer CLI for HSE Knowledge Platform (Section 22)."""

import json
import typer
from typing import Optional, List
from datetime import date
from rich.console import Console
from rich.table import Table

from service.config import settings
from service.db.session import get_db_session, init_db
from service.core.registry import load_source_registry
from service.pipeline.orchestrator import SyncOrchestrator
from service.index.retrieval import HybridRetrievalEngine
from service.rules.dsl_engine import ApplicabilityDSLEngine
from service.rules.facility_compiler import FacilityProfileCompiler, FacilityContext
from service.acquisition.resilience_lab.simulator import ResilienceSimulator
from service.webhooks.dispatcher import WebhookDispatcher, HSEEvent
from service.db.models import WebhookSubscription, Substance, OEL, ApplicabilityRule

app = typer.Typer(name="hse-knowledge", help="Deterministic Health, Safety & Environment Knowledge CLI.")
sources_app = typer.Typer(help="Manage and validate knowledge sources.")
webhook_app = typer.Typer(help="Manage outbound HSE webhooks.")
resilience_app = typer.Typer(help="Resilience Lab fault simulator.")

app.add_typer(sources_app, name="sources")
app.add_typer(webhook_app, name="webhook")
app.add_typer(resilience_app, name="resilience-lab")

console = Console()


@app.callback()
def main_callback():
    init_db()


# =============================================================
# Sources Subcommands
# =============================================================

@sources_app.command("list")
def list_sources(json_output: bool = typer.Option(False, "--json", help="Output as JSON")):
    registry = load_source_registry()
    sources = registry.list_sources()

    if json_output:
        typer.echo(json.dumps([s.model_dump() for s in sources], indent=2, ensure_ascii=False))
        return

    table = Table(title="Configured HSE Knowledge Sources")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Jurisdiction", style="magenta")
    table.add_column("Authority", style="yellow")
    table.add_column("License Policy", style="blue")

    for s in sources:
        table.add_row(s.id, s.name, s.jurisdiction, s.authority_level, s.license.policy)
    console.print(table)


@sources_app.command("validate")
def validate_sources(json_output: bool = typer.Option(False, "--json", help="Output as JSON")):
    registry = load_source_registry()
    errors = registry.validate()

    if json_output:
        typer.echo(json.dumps({"valid": len(errors) == 0, "errors": errors}, indent=2))
        return

    if not errors:
        console.print("[bold green]✔ All source catalog definitions are 100% valid.[/bold green]")
    else:
        console.print(f"[bold red]✖ Found {len(errors)} validation errors:[/bold red]")
        for err in errors:
            console.print(f"  - {err}")
        raise typer.Exit(code=2)


# =============================================================
# Sync & On-Demand Commands
# =============================================================

@app.command("plan")
def plan_sync(
    scope: str = typer.Option("vietnam-core", "--scope", help="Sync scope"),
    mode: str = typer.Option("incremental", "--mode", help="incremental / full"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    with get_db_session() as db:
        orchestrator = SyncOrchestrator()
        plan_res = orchestrator.plan(scope=scope, mode=mode, db=db)

        if json_output:
            typer.echo(plan_res.model_dump_json(indent=2))
            return

        console.print(f"[bold cyan]Plan for Scope:[/bold cyan] {plan_res.scope} (Mode: {plan_res.mode})")
        console.print(f"Target Sources ({len(plan_res.target_sources)}): {', '.join(plan_res.target_sources)}")
        if plan_res.policy_blocks:
            console.print(f"[yellow]Policy Blocks ({len(plan_res.policy_blocks)}):[/yellow]")
            for block in plan_res.policy_blocks:
                console.print(f"  - {block}")


@app.command("sync")
def run_sync(
    scope: str = typer.Option("vietnam-core", "--scope", help="Sync scope"),
    mode: str = typer.Option("incremental", "--mode", help="incremental / full"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    with get_db_session() as db:
        orchestrator = SyncOrchestrator()
        run = orchestrator.run_sync(scope=scope, mode=mode, db=db)

        if json_output:
            typer.echo(json.dumps({
                "run_id": run.run_id,
                "status": run.status,
                "items_discovered": run.items_discovered,
                "items_downloaded": run.items_downloaded,
                "items_normalized": run.items_normalized
            }, indent=2))
            return

        console.print(f"[bold green]✔ Sync Run {run.run_id} Succeeded![/bold green]")
        console.print(f"Items Discovered: {run.items_discovered} | Normalized: {run.items_normalized}")


@app.command("on-demand")
def on_demand_sync(
    topic_or_taxonomy: str = typer.Argument(..., help="Search term, chemical CAS, standard number, or topic"),
    scope: str = typer.Option("vietnam-core", "--scope", help="Target scope"),
    callback_url: Optional[str] = typer.Option(None, "--callback-url", help="Webhook callback URL"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    with get_db_session() as db:
        orchestrator = SyncOrchestrator()
        res = orchestrator.sync_on_demand(topic_or_taxonomy=topic_or_taxonomy, scope=scope, callback_url=callback_url, db=db)

        if json_output:
            typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
            return

        console.print(f"[bold green]✔ On-Demand Sync for '{topic_or_taxonomy}' Completed![/bold green]")
        console.print(f"Synced {res['synced_count']} items across registry.")


# =============================================================
# Search & Applicability
# =============================================================

@app.command("search")
def search_knowledge(
    query: str = typer.Argument(..., help="Search query"),
    as_of: Optional[str] = typer.Option(None, "--as-of", help="YYYY-MM-DD temporal date"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    with get_db_session() as db:
        retriever = HybridRetrievalEngine(db)
        as_of_d = date.fromisoformat(as_of) if as_of else date.today()
        results = retriever.search(query=query, as_of=as_of_d)

        if json_output:
            typer.echo(json.dumps([r.model_dump() for r in results], indent=2, ensure_ascii=False))
            return

        console.print(f"[bold cyan]Found {len(results)} results for '{query}' (as of {as_of_d}):[/bold cyan]")
        for r in results:
            console.print(f"\n[bold green]{r.title}[/bold green] (Type: {r.entity_type}, Score: {r.score:.2f})")
            console.print(f"  {r.content_text[:200]}...")


@app.command("health")
def check_health(json_output: bool = typer.Option(False, "--json", help="Output as JSON")):
    with get_db_session() as db:
        from service.db.models import Source
        src_cnt = db.query(Source).count()
        health_data = {"status": "healthy", "database": "connected", "source_count": src_cnt}

        if json_output:
            typer.echo(json.dumps(health_data, indent=2))
            return

        console.print("[bold green]✔ HSE Knowledge Platform is HEALTHY[/bold green]")
        console.print(f"Database: Connected | Active Sources: {src_cnt}")


# =============================================================
# Resilience Lab Simulator
# =============================================================

@resilience_app.command("run")
def run_resilience_lab(
    scenario: str = typer.Option("all", "--scenario", help="Target scenario name"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    simulator = ResilienceSimulator()
    results = simulator.run_all_scenarios()

    if json_output:
        typer.echo(json.dumps([r.model_dump() for r in results], indent=2))
        return

    table = Table(title="Resilience Lab Test Results")
    table.add_column("Scenario", style="cyan")
    table.add_column("Injected Status", style="yellow")
    table.add_column("Detected Class", style="magenta")
    table.add_column("Quarantined", style="red")
    table.add_column("Passed", style="green")

    for r in results:
        table.add_row(
            r.scenario_name,
            str(r.injected_status),
            r.detected_class.value,
            "YES" if r.quarantined else "NO",
            "✔ PASS" if r.handled_properly else "✖ FAIL"
        )
    console.print(table)


# =============================================================
# Webhooks Subcommands
# =============================================================

@webhook_app.command("add")
def add_webhook(
    name: str = typer.Argument(..., help="Subscriber name (e.g. odoo-erp)"),
    url: str = typer.Argument(..., help="Target URL"),
    secret: str = typer.Option("sec_hse_2026", "--secret", help="HMAC secret token"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    with get_db_session() as db:
        sub = WebhookSubscription(name=name, target_url=url, secret_token=secret, event_types=["*"])
        db.add(sub)
        db.commit()

        if json_output:
            typer.echo(json.dumps({"subscription_id": sub.subscription_id, "name": sub.name}, indent=2))
            return

        console.print(f"[bold green]✔ Webhook subscription '{name}' created ({sub.subscription_id})[/bold green]")


@webhook_app.command("list")
def list_webhooks(json_output: bool = typer.Option(False, "--json", help="Output as JSON")):
    with get_db_session() as db:
        subs = db.query(WebhookSubscription).all()

        if json_output:
            typer.echo(json.dumps([{
                "subscription_id": s.subscription_id,
                "name": s.name,
                "url": s.target_url,
                "is_active": s.is_active
            } for s in subs], indent=2))
            return

        table = Table(title="Active HSE Webhook Subscriptions")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Target URL", style="blue")
        table.add_column("Status", style="magenta")

        for s in subs:
            table.add_row(s.subscription_id, s.name, s.target_url, "ACTIVE" if s.is_active else "INACTIVE")
        console.print(table)


if __name__ == "__main__":
    app()
