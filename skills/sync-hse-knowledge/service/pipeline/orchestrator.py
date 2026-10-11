"""HSE Knowledge Sync Orchestrator & On-Demand Crawling Engine (Section 10.2, FR-140-142)."""

import uuid
import time
from datetime import datetime, timezone, date
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from service.core.registry import SourceRegistry, load_source_registry
from service.core.policy_engine import PolicyEngine
from service.storage.artifact_manager import ArtifactManager
from service.acquisition.gateway import AcquisitionGateway, GatewayFetchResult
from service.adapters.factory import get_adapter
from service.parsers.html_parser import HTMLDocumentParser
from service.parsers.sds_parser import SDSDocumentParser
from service.normalization.legal_doc import LegalDocumentNormalizer, ObligationExtractor
from service.normalization.chemical_sds import ChemicalSDSNormalizer
from service.webhooks.dispatcher import WebhookDispatcher, HSEEvent
from service.db.models import SyncRun, CoverageReport, ContentChunk, Document, Substance


class SyncPlanResult(BaseModel):
    scope: str
    mode: str
    target_sources: List[str]
    estimated_workload: int
    policy_blocks: List[str] = []


class SyncOrchestrator:
    def __init__(
        self,
        registry: Optional[SourceRegistry] = None,
        artifact_manager: Optional[ArtifactManager] = None
    ):
        self.registry = registry or load_source_registry()
        self.artifact_manager = artifact_manager or ArtifactManager()
        self.policy_engine = PolicyEngine(self.registry)
        self.gateway = AcquisitionGateway(self.policy_engine, self.artifact_manager)
        self.html_parser = HTMLDocumentParser()
        self.sds_parser = SDSDocumentParser()

    def plan(self, scope: str, mode: str, db: Session) -> SyncPlanResult:
        all_sources = self.registry.list_sources()
        target = []
        blocks = []
        for s in all_sources:
            if scope == "vietnam-core" and s.jurisdiction == "VN":
                target.append(s.id)
            elif scope == "all":
                target.append(s.id)

            if s.license.policy == "LICENSE_REQUIRED" and s.license.entitlement_required:
                blocks.append(f"Source {s.id} is gated pending commercial license registration")

        return SyncPlanResult(
            scope=scope,
            mode=mode,
            target_sources=target,
            estimated_workload=len(target) * 2,
            policy_blocks=blocks
        )

    def run_sync(self, scope: str, mode: str, db: Session) -> SyncRun:
        plan_res = self.plan(scope, mode, db)
        run = SyncRun(
            scope=scope,
            mode=mode,
            status="RUNNING",
            sources_target=plan_res.target_sources
        )
        db.add(run)
        db.commit()

        discovered_count = 0
        downloaded_count = 0
        parsed_count = 0
        normalized_count = 0

        for source_id in plan_res.target_sources:
            source_def = self.registry.get_source(source_id)
            if not source_def:
                continue

            adapter = get_adapter(source_id)
            if not adapter:
                continue

            discovery_page = adapter.discover(limit=50)
            discovered_count += len(discovery_page.items)

            for item in discovery_page.items:
                # Store artifact directly from candidate raw_content or fetch
                raw_bytes = item.raw_content.encode("utf-8") if item.raw_content else b"Empty content"
                artifact = self.artifact_manager.store_artifact(
                    content_bytes=raw_bytes,
                    source_id=source_id,
                    source_url=item.source_url,
                    canonical_url=item.canonical_url,
                    db=db,
                    declared_mime_type="text/html"
                )
                downloaded_count += 1

                # Parse & Normalize
                parsed = self.html_parser.parse(raw_bytes)
                parsed_count += 1

                doc, version, provisions = LegalDocumentNormalizer.normalize_document(
                    parsed=parsed,
                    source_id=source_id,
                    artifact_id=artifact.artifact_id,
                    authority_level=source_def.authority_level,
                    db=db
                )

                # Extract Obligations & Create Search Chunks
                for prov in provisions:
                    ObligationExtractor.extract_obligations(
                        provision=prov,
                        doc_number=doc.doc_number,
                        authority_level=source_def.authority_level,
                        db=db
                    )

                    # Create ContentChunk for Search
                    chunk = ContentChunk(
                        entity_type="document",
                        entity_id=prov.provision_id,
                        title=f"{doc.doc_number} - {prov.title or prov.code}",
                        content_text=prov.content_text,
                        search_vector_text=f"{doc.doc_number} {doc.title} {prov.title} {prov.content_text}",
                        source_url=item.source_url,
                        section_name=prov.code,
                        valid_from=date.today()
                    )
                    db.add(chunk)

                normalized_count += 1

        db.commit()

        # Update run stats
        run.items_discovered = discovered_count
        run.items_downloaded = downloaded_count
        run.items_parsed = parsed_count
        run.items_normalized = normalized_count
        run.status = "SUCCEEDED"
        run.finished_at = datetime.now(timezone.utc)
        db.commit()

        # Dispatch completion webhook event
        dispatcher = WebhookDispatcher(db)
        dispatcher.dispatch_event(HSEEvent(
            event_id=str(uuid.uuid4()),
            event_type="hse.sync.completed",
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "run_id": run.run_id,
                "scope": scope,
                "items_normalized": normalized_count,
                "status": "SUCCEEDED"
            }
        ))

        return run

    def sync_on_demand(
        self,
        topic_or_taxonomy: str,
        scope: str = "vietnam-core",
        callback_url: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Real-time on-demand crawling for a specific topic, chemical, regulation, or standard."""
        run = SyncRun(
            scope=f"on-demand:{topic_or_taxonomy}",
            mode="on-demand",
            status="RUNNING",
            sources_target=[scope]
        )
        db.add(run)
        db.commit()

        all_sources = self.registry.list_sources()
        synced_items = []

        q_lower = topic_or_taxonomy.lower()

        for s in all_sources:
            adapter = get_adapter(s.id)
            if not adapter:
                continue

            page = adapter.discover(limit=50)
            for item in page.items:
                content_to_check = (item.title + " " + (item.raw_content or "") + " " + (item.doc_number or "")).lower()
                if q_lower in content_to_check:
                    raw_bytes = (item.raw_content or "").encode("utf-8")
                    artifact = self.artifact_manager.store_artifact(
                        content_bytes=raw_bytes,
                        source_id=s.id,
                        source_url=item.source_url,
                        canonical_url=item.canonical_url,
                        db=db,
                        declared_mime_type="text/html"
                    )

                    parsed = self.html_parser.parse(raw_bytes)
                    doc, version, provisions = LegalDocumentNormalizer.normalize_document(
                        parsed=parsed,
                        source_id=s.id,
                        artifact_id=artifact.artifact_id,
                        authority_level=s.authority_level,
                        db=db
                    )

                    for prov in provisions:
                        ObligationExtractor.extract_obligations(
                            provision=prov,
                            doc_number=doc.doc_number,
                            authority_level=s.authority_level,
                            db=db
                        )

                        chunk = ContentChunk(
                            entity_type="document",
                            entity_id=prov.provision_id,
                            title=f"{doc.doc_number} - {prov.title or prov.code}",
                            content_text=prov.content_text,
                            search_vector_text=f"{doc.doc_number} {doc.title} {prov.title} {prov.content_text}",
                            source_url=item.source_url,
                            section_name=prov.code,
                            valid_from=date.today()
                        )
                        db.add(chunk)

                    synced_items.append(item.title)

        run.status = "SUCCEEDED"
        run.items_discovered = len(synced_items)
        run.items_downloaded = len(synced_items)
        run.items_normalized = len(synced_items)
        run.finished_at = datetime.now(timezone.utc)
        db.commit()

        # Emit Webhook event
        dispatcher = WebhookDispatcher(db)
        event = HSEEvent(
            event_id=str(uuid.uuid4()),
            event_type="hse.taxonomy.synced",
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={
                "query": topic_or_taxonomy,
                "synced_count": len(synced_items),
                "items": synced_items,
                "run_id": run.run_id
            }
        )
        dispatcher.dispatch_event(event)

        return {
            "status": "success",
            "run_id": run.run_id,
            "query": topic_or_taxonomy,
            "synced_count": len(synced_items),
            "items": synced_items
        }
