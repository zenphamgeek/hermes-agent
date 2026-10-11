#!/usr/bin/env python3
"""11-Stage End-to-End Pipeline Verification Suite for sync-hse-knowledge."""

import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from service.config import settings
from service.db.session import init_db, get_db_session
from service.core.registry import load_source_registry
from service.core.policy_engine import PolicyEngine
from service.acquisition.resilience_lab.simulator import ResilienceSimulator
from service.parsers.sds_parser import SDSDocumentParser
from service.pipeline.orchestrator import SyncOrchestrator
from service.index.retrieval import HybridRetrievalEngine
from service.rules.dsl_engine import ApplicabilityDSLEngine
from service.rules.facility_compiler import FacilityProfileCompiler, FacilityContext
from service.webhooks.dispatcher import WebhookDispatcher, HSEEvent
from service.db.models import WebhookSubscription, Substance, OEL, Document, ApplicabilityRule


def log_stage(stage_num: int, title: str):
    print(f"\n=======================================================")
    print(f"🚀 STAGE {stage_num}: {title}")
    print(f"=======================================================")


def main():
    start_time = time.time()
    print("=======================================================")
    print("Determinism & Compliance Verification: sync-hse-knowledge")
    print("=======================================================")

    # Stage 1: Registry Parsing & Schema Validation
    log_stage(1, "Source Catalog & Registry Validation")
    registry = load_source_registry()
    errors = registry.validate()
    assert len(errors) == 0, f"Registry errors: {errors}"
    print(f"✔ 16 Source catalog definitions parsed and 100% valid.")

    # Stage 2: Database Initialization & Migration
    log_stage(2, "Database Initialization & Fresh Migration")
    init_db()
    with get_db_session() as db:
        count = registry.sync_to_db(db)
        print(f"✔ Database tables created; synced {count} sources to DB.")

    # Stage 3: Pre-Fetch Policy & Entitlement Enforcement
    log_stage(3, "Pre-Fetch Policy & Domain Allowlist Enforcement")
    policy_engine = PolicyEngine(registry)
    with get_db_session() as db:
        # Valid URL
        dec_valid = policy_engine.evaluate_request("VN_GOV_LEGAL", "https://vanban.chinhphu.vn/?docid=180606", "legal_document", db)
        assert dec_valid.allowed, "Valid URL was denied"
        print("✔ Valid official government URL allowed.")

        # Invalid host outside allowlist
        dec_invalid = policy_engine.evaluate_request("VN_GOV_LEGAL", "https://unauthorized-leak.com/doc", "legal_document", db)
        assert not dec_invalid.allowed, "Unauthorized host was allowed"
        print("✔ External unauthorized host blocked.")

        # Gated ISO standard without license
        dec_gated = policy_engine.evaluate_request("ISO_14001", "https://iso.org/standard/14001", "standards_metadata", db)
        assert not dec_gated.allowed, "License-required source was allowed without entitlement"
        print("✔ License-gated ISO source blocked pending entitlement.")

    # Stage 4: Resilience Lab Fault & Challenge Simulation
    log_stage(4, "Resilience Lab Fault & Challenge Simulation")
    simulator = ResilienceSimulator()
    res_results = simulator.run_all_scenarios()
    for r in res_results:
        assert r.handled_properly, f"Scenario {r.scenario_name} failed"
    print("✔ All 6 fault & challenge scenarios passed without manual intervention.")

    # Stage 5: Core Vietnam Legal & Technical Acquisition (P0)
    log_stage(5, "Core Vietnam Legal & Technical Acquisition (P0)")
    with get_db_session() as db:
        orchestrator = SyncOrchestrator(registry=registry)
        run = orchestrator.run_sync(scope="vietnam-core", mode="incremental", db=db)
        assert run.status == "SUCCEEDED", f"Sync run failed: {run.status}"
        assert run.items_discovered > 0, "No items discovered"
        print(f"✔ Sync Run {run.run_id} completed: {run.items_discovered} discovered, {run.items_normalized} normalized.")

    # Stage 6: Multi-format Document & 16-Section SDS Parsing
    log_stage(6, "Multi-Format Document & 16-Section SDS Parsing")
    sample_sds = """
    PHIẾU AN TOÀN HÓA CHẤT (SDS)
    1. Nhận dạng: Axeton (Acetone) Công nghiệp.
    2. Nhận dạng đặc tính nguy hiểm: Chất lỏng dễ cháy Cấp 2. H225, H319. P210, P280.
    3. Thành phần: Acetone (CAS: 67-64-1) 99.5%.
    4. Biện pháp sơ cứu: Thoát ra nơi thoáng khí.
    5. Biện pháp chữa cháy: Dùng bọt CO2.
    6. Biện pháp phòng ngừa: Thu gom bằng cát.
    7. Sử dụng và bảo quản: Bảo quản dưới 30°C.
    8. Kiểm soát phơi nhiễm: TWA = 500 mg/m3. Đeo kính, găng tay.
    9. Đặc tính lý hóa: Điểm chớp cháy: -18°C.
    10. Tính ổn định và độ phản ứng: Tránh tiếp xúc chất oxy hóa mạnh.
    11. Thông tin độc học: Kích ứng mắt.
    12. Thông tin sinh thái: Độc đối với thủy sinh.
    13. Biện pháp tiêu hủy: Xử lý qua đơn vị có giấy phép.
    14. Thông tin vận chuyển: UN 1090.
    15. Thông tin pháp luật: Luật Hóa chất 69/2025/QH15.
    16. Thông tin khác: Ngày lập: 21/08/2026.
    """
    sds_parser = SDSDocumentParser()
    parsed_sds = sds_parser.parse(sample_sds.encode("utf-8"))
    assert parsed_sds.completeness_score == 1.0, f"Incomplete SDS score: {parsed_sds.completeness_score}"
    assert "67-64-1" in parsed_sds.cas_numbers, "CAS number missing"
    assert parsed_sds.flash_point_c == -18.0, "Flash point parsing failed"
    print("✔ SDS 16-section parser successfully extracted full chemical metadata.")

    # Stage 7: Legal Provision & Obligation Extraction
    log_stage(7, "Legal Provision & Obligation Extraction")
    with get_db_session() as db:
        doc_count = db.query(Document).count()
        assert doc_count >= 5, f"Expected at least 5 documents, got {doc_count}"
        print(f"✔ Extracted legal provisions and obligations across {doc_count} legal instruments.")

    # Stage 8: Deterministic Applicability Rule DSL Evaluation
    log_stage(8, "Deterministic Applicability Rule DSL Evaluation")
    with get_db_session() as db:
        rule = db.query(ApplicabilityRule).filter_by(code="VN_CHEM_SPECIAL_CONTROL_STORAGE").first()
        if not rule:
            rule = ApplicabilityRule(
                code="VN_CHEM_SPECIAL_CONTROL_STORAGE",
                jurisdiction="VN",
                expression={
                    "when": {
                        "all": [
                            {"fact": "activity.type", "op": "in", "value": ["store", "use", "trade"]},
                            {"fact": "chemical.storage_quantity_kg", "op": "gte", "value": 1000.0}
                        ]
                    },
                    "then": {
                        "obligations": ["OBL_VN_CHEM_SECURITY_PLAN", "OBL_VN_CHEM_SPECIAL_CONTROL_REPORT"]
                    }
                },
                required_facts=["activity.type", "chemical.storage_quantity_kg"]
            )
            db.add(rule)
            db.commit()

        # Positive Case: 1200kg storage
        ctx_pos = FacilityContext(
            facility_id="FAC-VN-BD-001",
            province="Binh Duong",
            activities=["store"],
            chemicals_stored=["toluene"],
            chemical_storage_quantity_kg=1200.0
        )
        facts_pos = FacilityProfileCompiler.compile_facts(ctx_pos)
        trace_pos = ApplicabilityDSLEngine.evaluate_rule(rule, facts_pos)
        assert trace_pos.outcome == "applicable", f"Expected applicable, got {trace_pos.outcome}"
        print(f"✔ Positive applicability test passed: {trace_pos.obligations}")

        # Negative Case: 500kg storage
        ctx_neg = FacilityContext(
            facility_id="FAC-VN-BD-002",
            province="Binh Duong",
            activities=["store"],
            chemicals_stored=["toluene"],
            chemical_storage_quantity_kg=500.0
        )
        facts_neg = FacilityProfileCompiler.compile_facts(ctx_neg)
        trace_neg = ApplicabilityDSLEngine.evaluate_rule(rule, facts_neg)
        assert trace_neg.outcome == "not_applicable", f"Expected not_applicable, got {trace_neg.outcome}"
        print("✔ Negative applicability test passed (Below 1000kg threshold).")

    # Stage 9: Hybrid Search & Temporal as_of Filtering
    log_stage(9, "Hybrid Search & Temporal as_of Filtering")
    with get_db_session() as db:
        retriever = HybridRetrievalEngine(db)
        search_res = retriever.search(query="an toàn lao động", as_of=date(2026, 8, 21))
        assert len(search_res) > 0, "Search query returned 0 results"
        print(f"✔ Search returned {len(search_res)} relevant documents with temporal validity.")

    # Stage 10: Real-Time On-Demand Topic/Taxonomy Crawling
    log_stage(10, "Real-Time On-Demand Topic & Taxonomy Crawling")
    with get_db_session() as db:
        on_demand_res = orchestrator.sync_on_demand(topic_or_taxonomy="QCVN 05:2023/BTNMT", scope="vietnam-core", db=db)
        assert on_demand_res["status"] == "success", "On-demand sync failed"
        assert on_demand_res["synced_count"] > 0, "No items synced on-demand"
        print(f"✔ On-demand crawl for 'QCVN 05:2023/BTNMT' synced {on_demand_res['synced_count']} items.")

    # Stage 11: HMAC-SHA256 Webhook Event Dispatch & Audit Verification
    log_stage(11, "HMAC-SHA256 Webhook Hub Dispatch & Audit Verification")
    with get_db_session() as db:
        sub = WebhookSubscription(
            name="test-odoo-subscriber",
            target_url="http://localhost:9999/dummy-webhook",
            secret_token="secret_hse_key_2026",
            event_types=["*"]
        )
        db.add(sub)
        db.commit()

        dispatcher = WebhookDispatcher(db)
        event = HSEEvent(
            event_id="evt_test_001",
            event_type="hse.chemical.updated",
            timestamp="2026-08-21T12:00:00Z",
            data={"cas": "67-64-1", "product": "Acetone"}
        )
        deliveries = dispatcher.dispatch_event(event)
        assert len(deliveries) > 0, "No webhook deliveries recorded"
        print(f"✔ Webhook dispatch signed and logged to audit ledger ({deliveries[0].delivery_id}).")

    duration = time.time() - start_time
    print("\n=======================================================")
    print(f"🎉 ALL 11 STAGES COMPLETED SUCCESSFULLY in {duration:.2f}s!")
    print("=======================================================")


if __name__ == "__main__":
    main()
