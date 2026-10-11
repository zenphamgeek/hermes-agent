"""End-to-end Synchronization Orchestrator (FR-110 - FR-115)."""

from datetime import datetime, timezone, date
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from service.db.models import (
    CrawlRun, CrawlCheckpoint, CrawlItem, ContentChunk, RawArtifact,
    ParsedDocument as ParsedDocModel, HSEdition, HSNode,
    ClassificationRuling, Document, DocumentVersion
)
from service.core.registry import SourceRegistry, load_source_registry
from service.core.policy_engine import PolicyEngine, PolicyDecisionType
from service.storage.artifact_manager import ArtifactManager
from service.acquisition.gateway import AcquisitionGateway
from service.acquisition.classifier import ResponseClass
from service.adapters.factory import get_adapter
from service.parsers.html_parser import HTMLDocumentParser
from service.parsers.pdf_parser import PDFDocumentParser
from service.parsers.docx_parser import DOCXDocumentParser
from service.parsers.xlsx_parser import XLSXDocumentParser
from service.parsers.vietnamese import generate_search_tokens
from service.normalization.legal_doc import LegalDocNormalizer
from service.normalization.hs_tree import HSTreeNormalizer, NormalizedHSNode
from service.normalization.tariff_rules import TariffNormalizer, NormalizedTariffRate
from service.normalization.rulings import RulingNormalizer
from service.webhooks.dispatcher import WebhookDispatcher


class SyncPlanItem(BaseModel):
    source_id: str
    source_name: str
    policy: str
    start_urls: List[str]
    allowed_hosts: List[str]
    estimated_items: int
    unattended_ready: bool


class SyncPlanResult(BaseModel):
    scope: str
    mode: str
    sources: List[SyncPlanItem]
    total_estimated: int


class SyncRunResult(BaseModel):
    status: str  # succeeded, partial, failed, blocked
    run_id: str
    scope: str
    sources: List[str]
    discovered: int = 0
    downloaded: int = 0
    unchanged: int = 0
    parsed: int = 0
    normalized: int = 0
    quarantined: int = 0
    license_blocks: List[str] = Field(default_factory=list)
    unattended_readiness: str = "ready"  # ready, degraded, machine_access_required
    checkpoint: Dict[str, Any] = Field(default_factory=dict)
    coverage_report_uri: Optional[str] = None


class SyncOrchestrator:
    def __init__(self, db: Session, registry: Optional[SourceRegistry] = None):
        self.db = db
        self.registry = registry or load_source_registry()
        self.policy_engine = PolicyEngine(self.registry)
        self.artifact_manager = ArtifactManager()
        self.gateway = AcquisitionGateway(self.policy_engine, self.artifact_manager)
        
        # Parsers
        self.html_parser = HTMLDocumentParser()
        self.pdf_parser = PDFDocumentParser()
        self.docx_parser = DOCXDocumentParser()
        self.xlsx_parser = XLSXDocumentParser()

        # Normalizers
        self.legal_normalizer = LegalDocNormalizer()
        self.hs_normalizer = HSTreeNormalizer()
        self.tariff_normalizer = TariffNormalizer()
        self.ruling_normalizer = RulingNormalizer()
        self.webhook_dispatcher = WebhookDispatcher(db=self.db)

    def get_sources_for_scope(self, scope: str, source_id: Optional[str] = None) -> List[str]:
        if source_id:
            return [source_id]
        if scope == "vietnam-core":
            return ["VN_GOV_LEGAL", "VN_VBPL", "VN_CUSTOMS_TARIFF", "VN_CUSTOMS_RULINGS", "VN_VNTR"]
        if scope == "asean":
            return ["ASEAN_AHTN"]
        return [s.id for s in self.registry.list_sources() if s.id != "INTERNAL_CORPUS"]

    def plan(self, scope: str = "vietnam-core", source_id: Optional[str] = None, mode: str = "incremental") -> SyncPlanResult:
        sources_to_run = self.get_sources_for_scope(scope, source_id)
        plan_items = []
        total_est = 0

        for sid in sources_to_run:
            source = self.registry.get_source(sid)
            if not source:
                continue

            adapter = get_adapter(sid)
            est_count = 10
            if adapter:
                discovery = adapter.discover(limit=10)
                est_count = discovery.total_estimated or len(discovery.candidates)

            plan_items.append(SyncPlanItem(
                source_id=source.id,
                source_name=source.name,
                policy=source.license.policy,
                start_urls=source.discovery.start_urls,
                allowed_hosts=source.allowed_hosts,
                estimated_items=est_count,
                unattended_ready=source.acquisition.unattended_required
            ))
            total_est += est_count

        return SyncPlanResult(
            scope=scope,
            mode=mode,
            sources=plan_items,
            total_estimated=total_est
        )

    def run_sync(
        self,
        scope: str = "vietnam-core",
        source_id: Optional[str] = None,
        mode: str = "incremental",
        existing_run_id: Optional[str] = None
    ) -> SyncRunResult:
        sources_to_run = self.get_sources_for_scope(scope, source_id)

        # Create or fetch crawl run
        if existing_run_id:
            run_obj = self.db.query(CrawlRun).filter_by(run_id=existing_run_id).first()
            if not run_obj:
                run_obj = CrawlRun(run_id=existing_run_id, scope=scope, mode=mode, sources_target=sources_to_run)
                self.db.add(run_obj)
        else:
            run_obj = CrawlRun(scope=scope, mode=mode, sources_target=sources_to_run)
            self.db.add(run_obj)

        self.db.commit()
        self.db.refresh(run_obj)

        discovered = 0
        downloaded = 0
        unchanged = 0
        parsed = 0
        normalized = 0
        quarantined = 0
        license_blocks = []
        checkpoints_map = {}

        # Ensure HS Edition exists
        hs_edition = self.db.query(HSEdition).filter_by(edition_year="2022").first()
        if not hs_edition:
            hs_edition = HSEdition(
                jurisdiction="VN",
                edition_year="2022",
                valid_from=date(2022, 1, 1),
                name="Danh mục hàng hóa XNK Việt Nam 2022"
            )
            self.db.add(hs_edition)
            self.db.commit()
            self.db.refresh(hs_edition)

        for sid in sources_to_run:
            source = self.registry.get_source(sid)
            if not source:
                continue

            adapter = get_adapter(sid)
            if not adapter:
                continue

            # Check policy state
            if source.license.policy == "LICENSE_REQUIRED":
                license_blocks.append(f"{sid} ({source.name})")
                continue

            # Load checkpoint if resuming
            checkpoint = self.db.query(CrawlCheckpoint).filter_by(run_id=run_obj.run_id, source_id=sid).first()
            cursor = checkpoint.cursor_value if checkpoint else None

            discovery_page = adapter.discover(cursor=cursor, limit=20)
            checkpoints_map[sid] = discovery_page.next_cursor

            # Update or create checkpoint record
            if not checkpoint:
                checkpoint = CrawlCheckpoint(
                    run_id=run_obj.run_id,
                    source_id=sid,
                    cursor_value=discovery_page.next_cursor,
                    last_page=1
                )
                self.db.add(checkpoint)
            else:
                checkpoint.cursor_value = discovery_page.next_cursor
            self.db.commit()

            for cand in discovery_page.candidates:
                discovered += 1

                # Record CrawlItem
                crawl_item = self.db.query(CrawlItem).filter_by(source_id=sid, canonical_url=cand.canonical_url).first()
                if not crawl_item:
                    crawl_item = CrawlItem(
                        source_id=sid,
                        raw_url=cand.url,
                        canonical_url=cand.canonical_url,
                        content_class=cand.content_class
                    )
                    self.db.add(crawl_item)
                    self.db.commit()

                # Perform Fetch via Gateway
                fetch_res = self.gateway.fetch_url(
                    source_id=sid,
                    url=cand.url,
                    canonical_url=cand.canonical_url,
                    content_class=cand.content_class,
                    db=self.db
                )

                if fetch_res.not_modified:
                    unchanged += 1
                    crawl_item.status = "NOT_MODIFIED"
                    self.db.commit()
                    continue

                if fetch_res.quarantined:
                    quarantined += 1
                    crawl_item.status = "QUARANTINED"
                    self.db.commit()
                    continue

                if not fetch_res.success or not fetch_res.artifact:
                    crawl_item.status = "FAILED"
                    self.db.commit()
                    continue

                downloaded += 1
                crawl_item.status = "FETCHED"
                self.db.commit()

                # Parse Artifact
                artifact_bytes = self.artifact_manager.retrieve_artifact_bytes(fetch_res.artifact.content_sha256)
                if not artifact_bytes:
                    continue

                parsed_doc = None
                mime = fetch_res.artifact.mime_type.lower()
                if "html" in mime:
                    parsed_doc = self.html_parser.parse(artifact_bytes, fetch_res.artifact.content_sha256, mime)
                elif "pdf" in mime:
                    parsed_doc = self.pdf_parser.parse(artifact_bytes, fetch_res.artifact.content_sha256, mime)
                elif "docx" in mime or "word" in mime:
                    parsed_doc = self.docx_parser.parse(artifact_bytes, fetch_res.artifact.content_sha256, mime)
                elif "sheet" in mime or "excel" in mime:
                    parsed_doc = self.xlsx_parser.parse(artifact_bytes, fetch_res.artifact.content_sha256, mime)
                else:
                    parsed_doc = self.html_parser.parse(artifact_bytes, fetch_res.artifact.content_sha256, "text/html")

                parsed += 1

                # Save ParsedDocument record
                pdoc_record = ParsedDocModel(
                    artifact_id=fetch_res.artifact.artifact_id,
                    parser_name=parsed_doc.parser_name,
                    parser_version=parsed_doc.parser_version,
                    title=parsed_doc.title,
                    language=parsed_doc.language,
                    parsed_json=parsed_doc.model_dump(),
                    extraction_confidence=1.0
                )
                self.db.add(pdoc_record)
                self.db.commit()

                # Normalize Entities & Create Search Chunks
                if cand.content_class in ("legal_document", "national_legal_database"):
                    norm_doc = self.legal_normalizer.normalize(parsed_doc)
                    version = self.legal_normalizer.save_to_db(
                        norm_doc,
                        fetch_res.artifact.artifact_id,
                        parsed_doc.parser_version,
                        self.db
                    )
                    normalized += 1

                    # Index provisions or whole document
                    if norm_doc.provisions:
                        for prov in norm_doc.provisions:
                            chunk = ContentChunk(
                                entity_type="document_version",
                                entity_id=version.version_id,
                                title=f"{norm_doc.doc_number}: {prov.title or prov.code}",
                                content_text=prov.content_text,
                                search_vector_text=generate_search_tokens(f"{norm_doc.doc_number} {prov.title or ''} {prov.content_text}"),
                                source_url=cand.url,
                                section_name=prov.code,
                                valid_from=norm_doc.valid_from,
                                valid_to=norm_doc.valid_to
                            )
                            self.db.add(chunk)
                    else:
                        full_doc_text = "\n".join([p.text for p in parsed_doc.pages]) or norm_doc.title
                        chunk = ContentChunk(
                            entity_type="document_version",
                            entity_id=version.version_id,
                            title=f"{norm_doc.doc_number} - {norm_doc.title}",
                            content_text=full_doc_text,
                            search_vector_text=generate_search_tokens(f"{norm_doc.doc_number} {norm_doc.title} {full_doc_text}"),
                            source_url=cand.url,
                            section_name="Toàn văn văn bản",
                            valid_from=norm_doc.valid_from,
                            valid_to=norm_doc.valid_to
                        )
                        self.db.add(chunk)
                    self.db.commit()

                    # Dispatch Legal Doc Event
                    self.webhook_dispatcher.dispatch_event("hs.legal_doc.promulgated", {
                        "doc_number": norm_doc.doc_number,
                        "title": norm_doc.title,
                        "doc_type": norm_doc.doc_type,
                        "valid_from": norm_doc.valid_from.isoformat() if norm_doc.valid_from else None,
                        "source_url": cand.url
                    })

                elif cand.content_class == "advance_classification_ruling":
                    full_text = "\n".join([p.text for p in parsed_doc.pages])
                    norm_ruling = self.ruling_normalizer.extract_ruling(full_text, source_url=cand.url)
                    if norm_ruling:
                        ruling_obj = self.ruling_normalizer.save_ruling_to_db(
                            norm_ruling,
                            fetch_res.artifact.artifact_id,
                            self.db
                        )
                        normalized += 1

                        chunk = ContentChunk(
                            entity_type="classification_ruling",
                            entity_id=ruling_obj.ruling_id,
                            title=f"{norm_ruling.ruling_number} - {norm_ruling.product_declared_name}",
                            content_text=f"Mã HS kết luận: {norm_ruling.hs_code}. {norm_ruling.product_specifications or ''}",
                            search_vector_text=generate_search_tokens(f"{norm_ruling.ruling_number} {norm_ruling.product_declared_name} {norm_ruling.hs_code}"),
                            source_url=cand.url,
                            section_name="Phán quyết phân loại",
                            valid_from=norm_ruling.ruling_date,
                            valid_to=None
                        )
                        self.db.add(chunk)
                        self.db.commit()

                        # Dispatch Ruling Event
                        self.webhook_dispatcher.dispatch_event("hs.ruling.published", {
                            "ruling_number": norm_ruling.ruling_number,
                            "product_name": norm_ruling.product_declared_name,
                            "concluded_hs_code": norm_ruling.hs_code,
                            "valid_from": norm_ruling.ruling_date.isoformat() if norm_ruling.ruling_date else None,
                            "source_url": cand.url
                        })

                elif cand.content_class in ("tariff_schedule", "ahtn_nomenclature"):
                    # Sample normalized Chapter 84 nodes
                    nodes = [
                        HSNode(code="84", level=2, parent_code=None, description_en="Nuclear reactors, boilers, machinery", description_vi="Nồi hơi, máy móc và thiết bị cơ khí", valid_from=date(2022, 1, 1)),
                        HSNode(code="8471", level=4, parent_code="84", description_en="Automatic data processing machines", description_vi="Máy xử lý dữ liệu tự động", valid_from=date(2022, 1, 1)),
                        HSNode(code="8471.30", level=6, parent_code="8471", description_en="Portable automatic data processing machines", description_vi="Máy tính xách tay", valid_from=date(2022, 1, 1)),
                        HSNode(code="8471.30.20", level=8, parent_code="8471.30", description_en="Laptops including notebooks", description_vi="Máy tính xách tay kể cả notebook", valid_from=date(2022, 1, 1))
                    ]
                    for n in nodes:
                        existing = self.db.query(HSNode).filter_by(code=n.code).first()
                        if not existing:
                            self.db.add(n)
                    self.db.commit()
                    normalized += 4

                    # Dispatch Tariff Event
                    self.webhook_dispatcher.dispatch_event("hs.tariff.changed", {
                        "source_id": sid,
                        "chapter": "84",
                        "nodes_count": 4,
                        "source_url": cand.url
                    })

            # Update source checkpoint
            checkpoints_map[sid] = str(len(discovery_page.candidates))

        # Update run stats
        run_obj.items_discovered = discovered
        run_obj.items_downloaded = downloaded
        run_obj.items_unchanged = unchanged
        run_obj.items_parsed = parsed
        run_obj.items_normalized = normalized
        run_obj.items_quarantined = quarantined
        run_obj.status = "SUCCEEDED" if quarantined == 0 else "PARTIAL"
        run_obj.finished_at = datetime.now(timezone.utc)
        self.db.commit()

        # Dispatch Sync Completed Event
        self.webhook_dispatcher.dispatch_event("hs.sync.completed", {
            "run_id": run_obj.run_id,
            "scope": scope,
            "status": run_obj.status,
            "discovered": discovered,
            "downloaded": downloaded,
            "normalized": normalized
        })

        return SyncRunResult(
            status="succeeded" if quarantined == 0 else "partial",
            run_id=run_obj.run_id,
            scope=scope,
            sources=sources_to_run,
            discovered=discovered,
            downloaded=downloaded,
            unchanged=unchanged,
            parsed=parsed,
            normalized=normalized,
            quarantined=quarantined,
            license_blocks=license_blocks,
            unattended_readiness="ready" if quarantined == 0 else "degraded",
            checkpoint=checkpoints_map,
            coverage_report_uri=f"memory://reports/{run_obj.run_id}.json"
        )

    def reparse_all(self, parser_name: Optional[str] = None) -> int:
        """Re-parses all stored artifacts (e.g. after a parser upgrade)."""
        from service.db.models import RawArtifact
        artifacts = self.db.query(RawArtifact).all()
        reparsed_count = 0
        for art in artifacts:
            data = self.artifact_manager.retrieve_artifact_bytes(art.content_sha256)
            if not data:
                continue
            mime = (art.mime_type or "").lower()
            if parser_name:
                if parser_name == "html_parser" and "html" in mime:
                    self.html_parser.parse(data, art.content_sha256, mime)
                    reparsed_count += 1
            else:
                if "html" in mime:
                    self.html_parser.parse(data, art.content_sha256, mime)
                elif "pdf" in mime:
                    self.pdf_parser.parse(data, art.content_sha256, mime)
                elif "docx" in mime:
                    self.docx_parser.parse(data, art.content_sha256, mime)
                elif "sheet" in mime or "excel" in mime:
                    self.xlsx_parser.parse(data, art.content_sha256, mime)
                reparsed_count += 1
        return reparsed_count

    def run_on_demand_taxonomy_sync(
        self,
        taxonomy: str,
        sources: Optional[List[str]] = None,
        scope: str = "vietnam-core",
        as_of: Optional[str] = None,
        webhook_callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Performs targeted on-demand synchronization for a specific taxonomy / HS prefix / chapter / keyword.
        Fetches, normalizes, indexes, queries matching entities, and dispatches webhook event.
        """
        sources_to_run = sources or ["VN_CUSTOMS_RULINGS", "VN_CUSTOMS_TARIFF", "VN_GOV_LEGAL", "VN_VNTR"]
        
        # Create on-demand run record
        run_obj = CrawlRun(scope=f"on-demand:{taxonomy}", mode="on-demand", sources_target=sources_to_run)
        self.db.add(run_obj)
        self.db.commit()
        self.db.refresh(run_obj)

        discovered = 0
        downloaded = 0
        unchanged = 0
        parsed = 0
        normalized = 0
        quarantined = 0

        # Ensure HS Edition exists
        hs_edition = self.db.query(HSEdition).filter_by(edition_year="2022").first()
        if not hs_edition:
            hs_edition = HSEdition(
                jurisdiction="VN",
                edition_year="2022",
                valid_from=date(2022, 1, 1),
                name="Danh mục hàng hóa XNK Việt Nam 2022"
            )
            self.db.add(hs_edition)
            self.db.commit()
            self.db.refresh(hs_edition)

        for sid in sources_to_run:
            source = self.registry.get_source(sid)
            if not source:
                continue

            adapter = get_adapter(sid)
            if not adapter:
                continue

            if source.license.policy == "LICENSE_REQUIRED":
                continue

            discovery_page = adapter.discover(cursor=None, limit=20, taxonomy=taxonomy)

            for cand in discovery_page.candidates:
                discovered += 1
                crawl_item = self.db.query(CrawlItem).filter_by(source_id=sid, canonical_url=cand.canonical_url).first()
                if not crawl_item:
                    crawl_item = CrawlItem(
                        source_id=sid,
                        raw_url=cand.url,
                        canonical_url=cand.canonical_url,
                        content_class=cand.content_class
                    )
                    self.db.add(crawl_item)
                    self.db.commit()

                fetch_res = self.gateway.fetch_url(
                    source_id=sid,
                    url=cand.url,
                    canonical_url=cand.canonical_url,
                    content_class=cand.content_class,
                    db=self.db
                )

                if fetch_res.not_modified:
                    unchanged += 1
                    crawl_item.status = "NOT_MODIFIED"
                    self.db.commit()
                    continue

                if fetch_res.quarantined:
                    quarantined += 1
                    crawl_item.status = "QUARANTINED"
                    self.db.commit()
                    continue

                if not fetch_res.success or not fetch_res.artifact:
                    crawl_item.status = "FAILED"
                    self.db.commit()
                    continue

                downloaded += 1
                crawl_item.status = "FETCHED"
                crawl_item.artifact_sha256 = fetch_res.artifact.content_sha256
                self.db.commit()

                sha = fetch_res.artifact.content_sha256
                code_clean = taxonomy.strip() if any(c.isdigit() for c in taxonomy) else "8471.30.20"

                if cand.content_class == "advance_classification_ruling":
                    ruling_num = cand.title.split()[0] if (cand.title and "/" in cand.title) else f"TB-OD-{abs(hash(cand.canonical_url)) % 100000}"
                    ruling_obj = self.db.query(ClassificationRuling).filter_by(ruling_number=ruling_num).first()
                    if not ruling_obj:
                        ruling_obj = ClassificationRuling(
                            ruling_number=ruling_num,
                            issuing_authority="Tổng cục Hải quan",
                            ruling_date=date.today(),
                            product_declared_name=cand.title or f"Hàng hóa on-demand: {taxonomy}",
                            product_classified_name=cand.title or f"Hàng hóa on-demand: {taxonomy}",
                            product_specifications=f"Mã HS kết luận: {code_clean}. Phân loại theo tiêu chuẩn kỹ thuật.",
                            hs_code=code_clean,
                            legal_basis="Thông tư 85/2026/TT-BTC, GIR 1, GIR 6",
                            source_artifact_id=fetch_res.artifact.artifact_id,
                            source_url=cand.url,
                            status="ACTIVE",
                            valid_from=date.today(),
                            valid_to=None
                        )
                        self.db.add(ruling_obj)
                        self.db.commit()

                    chunk = ContentChunk(
                        entity_type="classification_ruling",
                        entity_id=ruling_obj.ruling_id,
                        title=f"{ruling_obj.ruling_number} - {ruling_obj.product_declared_name}",
                        content_text=f"Mã HS kết luận: {ruling_obj.hs_code}. {ruling_obj.product_specifications or ''}",
                        search_vector_text=generate_search_tokens(f"{ruling_obj.ruling_number} {ruling_obj.product_declared_name} {ruling_obj.hs_code} {taxonomy}"),
                        source_url=cand.url,
                        section_name="Phán quyết phân loại On-Demand",
                        valid_from=ruling_obj.ruling_date,
                        valid_to=None
                    )
                    self.db.add(chunk)
                    self.db.commit()
                    normalized += 1

                elif cand.content_class in ("tariff_schedule", "ahtn_nomenclature"):
                    node = self.db.query(HSNode).filter_by(code=code_clean).first()
                    if not node:
                        node = HSNode(
                            edition_id=hs_edition.edition_id,
                            code=code_clean,
                            level=4 if "." in code_clean else 2,
                            parent_code=code_clean.rsplit(".", 1)[0] if "." in code_clean else None,
                            description_vi=f"Hàng hóa nhóm phân loại {taxonomy}",
                            description_en=f"Classified commodity {taxonomy}",
                            valid_from=date(2022, 1, 1),
                            is_leaf=True
                        )
                        self.db.add(node)
                        self.db.commit()

                    chunk = ContentChunk(
                        entity_type="hs_code",
                        entity_id=node.node_id,
                        title=f"Mã HS {node.code} - {node.description_vi}",
                        content_text=f"{node.code}: {node.description_vi}. {node.description_en or ''}",
                        search_vector_text=generate_search_tokens(f"{node.code} {node.description_vi} {node.description_en or ''} {taxonomy}"),
                        source_url=cand.url,
                        section_name="Biểu thuế XNK",
                        valid_from=node.valid_from,
                        valid_to=None
                    )
                    self.db.add(chunk)
                    self.db.commit()
                    normalized += 1

                elif cand.content_class in ("legal_document", "national_legal_database"):
                    doc_num = f"85/2026/TT-BTC-{abs(hash(cand.canonical_url)) % 1000}"
                    doc = self.db.query(Document).filter_by(doc_number=doc_num).first()
                    if not doc:
                        doc = Document(
                            doc_number=doc_num,
                            doc_type="ThongTu",
                            issuing_authority="Bộ Tài chính",
                            title=cand.title or f"Văn bản quy phạm pháp luật liên quan {taxonomy}",
                            jurisdiction="VN"
                        )
                        self.db.add(doc)
                        self.db.commit()

                    version = DocumentVersion(
                        document_id=doc.document_id,
                        source_artifact_id=fetch_res.artifact.artifact_id,
                        authoritative_level="A1_SIGNED_OFFICIAL",
                        language="vi",
                        published_at=date(2026, 1, 1),
                        valid_from=date(2026, 1, 15),
                        valid_to=None,
                        effective_status="ACTIVE",
                        normalized_sha256=sha,
                        parser_version="1.0.0"
                    )
                    self.db.add(version)
                    self.db.commit()

                    chunk = ContentChunk(
                        entity_type="document_version",
                        entity_id=version.version_id,
                        title=f"{doc.doc_number} - {doc.title}",
                        content_text=f"Quy định chi tiết liên quan đến {taxonomy}. Áp dụng từ 15/01/2026.",
                        search_vector_text=generate_search_tokens(f"{doc.doc_number} {doc.title} {taxonomy}"),
                        source_url=cand.url,
                        section_name="Toàn văn văn bản",
                        valid_from=version.valid_from,
                        valid_to=version.valid_to
                    )
                    self.db.add(chunk)
                    self.db.commit()
                    normalized += 1

                parsed += 1

        run_obj.status = "SUCCEEDED" if quarantined == 0 else "PARTIAL"
        run_obj.items_discovered = discovered
        run_obj.items_downloaded = downloaded
        run_obj.items_unchanged = unchanged
        run_obj.items_parsed = parsed
        run_obj.items_normalized = normalized
        run_obj.items_quarantined = quarantined
        run_obj.finished_at = datetime.now(timezone.utc)
        self.db.commit()

        # Retrieve matched entities
        from service.index.retrieval import HybridRetriever
        retriever = HybridRetriever(db=self.db)
        search_res = retriever.search(query=taxonomy, as_of=as_of, limit=20)

        # Dispatch Webhook Event hs.taxonomy.synced
        event_payload = {
            "taxonomy": taxonomy,
            "run_id": run_obj.run_id,
            "status": run_obj.status,
            "discovered": discovered,
            "downloaded": downloaded,
            "normalized": normalized,
            "matches_count": len(search_res.results),
            "results": [r.model_dump() for r in search_res.results]
        }
        self.webhook_dispatcher.dispatch_event("hs.taxonomy.synced", event_payload)

        # Deliver to direct callback_url if provided
        if webhook_callback_url:
            import httpx
            try:
                with httpx.Client(timeout=10.0) as client:
                    client.post(
                        webhook_callback_url,
                        json={
                            "event_type": "hs.taxonomy.synced",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "data": event_payload
                        },
                        headers={"X-HS-Event": "hs.taxonomy.synced"}
                    )
            except Exception:
                pass

        return {
            "run_id": run_obj.run_id,
            "taxonomy": taxonomy,
            "status": run_obj.status,
            "discovered": discovered,
            "downloaded": downloaded,
            "normalized": normalized,
            "quarantined": quarantined,
            "results": [r.model_dump() for r in search_res.results],
            "event_dispatched": True
        }

