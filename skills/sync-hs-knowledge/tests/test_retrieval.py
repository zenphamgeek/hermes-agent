"""Test hybrid retrieval with temporal filters (FR-090 - FR-094, AC-010)."""

import pytest
from datetime import date
from service.db.models import ClassificationRuling, HSNode, HSEdition
from service.index.retrieval import HybridRetriever


def test_retrieval_and_as_of_filtering(db_session):
    # Setup test edition and nodes
    edition = HSEdition(
        jurisdiction="VN",
        edition_year="2022",
        valid_from=date(2022, 1, 1),
        name="Danh mục 2022"
    )
    db_session.add(edition)
    db_session.flush()

    node = HSNode(
        edition_id=edition.edition_id,
        code="8471.30.20",
        level=4,
        parent_code="8471.30",
        description_vi="Máy tính xách tay",
        valid_from=date(2022, 1, 1),
        is_leaf=True
    )
    db_session.add(node)

    # Ruling active from 2026-08-15
    ruling = ClassificationRuling(
        ruling_number="8921/TB-TCHQ",
        issuing_authority="Tổng cục Hải quan",
        ruling_date=date(2026, 8, 15),
        product_declared_name="Bộ điều khiển PLC",
        hs_code="8537.10.19",
        valid_from=date(2026, 8, 15),
        valid_to=None,
        status="ACTIVE"
    )
    db_session.add(ruling)
    db_session.commit()

    retriever = HybridRetriever(db=db_session)

    # Search for HS code
    res_hs = retriever.search(query="8471.30.20", as_of="2026-08-20")
    assert len(res_hs.results) > 0
    assert res_hs.results[0].entity_id == "8471.30.20"

    # Search for ruling AFTER effective date (2026-08-20) -> should be found
    res_after = retriever.search(query="PLC", as_of="2026-08-20")
    ruling_ids = [r.entity_id for r in res_after.results]
    assert ruling.ruling_id in ruling_ids

    # Search for ruling BEFORE effective date (2026-01-01) -> should NOT be found (AC-010)
    res_before = retriever.search(query="PLC", as_of="2026-01-01")
    ruling_ids_before = [r.entity_id for r in res_before.results]
    assert ruling.ruling_id not in ruling_ids_before
