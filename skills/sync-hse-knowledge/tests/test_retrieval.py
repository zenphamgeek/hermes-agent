"""Tests for Hybrid Search and Retrieval Engine."""

from datetime import date
from service.index.retrieval import HybridRetrievalEngine
from service.db.models import ContentChunk


def test_retrieval_search(db_session):
    chunk = ContentChunk(
        entity_type="document",
        entity_id="PROV-001",
        title="QCVN 05:2023/BTNMT - Quy chuẩn kỹ thuật quốc gia về chất lượng không khí",
        content_text="Quy định giới hạn thông số nồng độ bụi trong không khí xung quanh.",
        search_vector_text="qcvn 05 2023 btnmt chất lượng không khí bụi",
        valid_from=date(2023, 3, 1)
    )
    db_session.add(chunk)
    db_session.commit()

    retriever = HybridRetrievalEngine(db_session)
    results = retriever.search(query="không khí bụi", as_of=date.today())
    assert len(results) > 0
    assert results[0].chunk_id == chunk.chunk_id
