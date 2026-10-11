"""Hybrid Search & Retrieval with As-Of Temporal Filters (FR-090 - FR-094)."""

from datetime import date, datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from service.db.models import ContentChunk, HSNode, ClassificationRuling, TariffRate
from service.parsers.vietnamese import generate_search_tokens, remove_vietnamese_diacritics
from .embeddings import get_embedding_client


class Citation(BaseModel):
    source_url: Optional[str] = None
    document_id: Optional[str] = None
    artifact_sha256: Optional[str] = None
    page: Optional[int] = None
    section: Optional[str] = None


class SearchResultItem(BaseModel):
    entity_type: str  # classification_ruling, hs_node, tariff_rate, document_version
    entity_id: str
    title: str
    content_snippet: str
    score: float
    authority_level: str = "A2_OFFICIAL_DATABASE"
    citation: Citation
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    as_of: str
    results: List[SearchResultItem] = Field(default_factory=list)


class HybridRetriever:
    def __init__(self, db: Session):
        self.db = db
        self.embedder = get_embedding_client()

    def search(
        self,
        query: str,
        as_of: Optional[str] = None,
        limit: int = 10
    ) -> SearchResponse:
        as_of_date = None
        if as_of:
            try:
                as_of_date = datetime.strptime(as_of, "%Y-%m-%d").date()
            except ValueError:
                as_of_date = date.today()
        else:
            as_of_date = date.today()

        as_of_str = as_of_date.isoformat()
        search_tokens = generate_search_tokens(query).split()
        clean_q = remove_vietnamese_diacritics(query).lower().strip()

        results: List[SearchResultItem] = []

        # 1. Search HS Nodes
        hs_nodes = self.db.query(HSNode).all()
        for node in hs_nodes:
            score = 0.0
            node_clean = remove_vietnamese_diacritics(f"{node.code} {node.description_vi or ''}").lower()
            
            # Exact HS code match boost
            if clean_q in node.code.lower() or node.code.lower() in clean_q:
                score += 0.95
            elif any(tok in node_clean for tok in search_tokens):
                score += 0.65

            if score > 0.0:
                results.append(SearchResultItem(
                    entity_type="hs_node",
                    entity_id=node.code,
                    title=f"Mã HS {node.code}: {node.description_vi or ''}",
                    content_snippet=f"Level {node.level} - Parent: {node.parent_code or 'None'}. {node.description_vi or ''}",
                    score=score,
                    authority_level="A1_SIGNED_OFFICIAL",
                    citation=Citation(section=f"HS Chapter {node.code[:2]}"),
                    valid_from=node.valid_from.isoformat() if node.valid_from else "2022-01-01",
                    valid_to=node.valid_to.isoformat() if node.valid_to else None
                ))

        # 2. Search Classification Rulings
        rulings = self.db.query(ClassificationRuling).all()
        for ruling in rulings:
            # Temporal filter: valid_from <= as_of and (valid_to is null or valid_to >= as_of)
            if ruling.valid_from and ruling.valid_from > as_of_date:
                continue
            if ruling.valid_to and ruling.valid_to < as_of_date:
                continue

            ruling_text = remove_vietnamese_diacritics(
                f"{ruling.ruling_number} {ruling.product_declared_name} {ruling.product_specifications or ''} {ruling.hs_code}"
            ).lower()

            score = 0.0
            if clean_q in ruling.hs_code.lower() or ruling.ruling_number.lower() in clean_q:
                score += 0.92
            elif any(tok in ruling_text for tok in search_tokens):
                score += 0.75

            if score > 0.0:
                results.append(SearchResultItem(
                    entity_type="classification_ruling",
                    entity_id=ruling.ruling_id,
                    title=f"{ruling.ruling_number} - {ruling.product_declared_name}",
                    content_snippet=f"Mã kết luận: {ruling.hs_code}. {ruling.product_specifications or ''}",
                    score=score,
                    authority_level="A2_OFFICIAL_DATABASE",
                    citation=Citation(
                        source_url=ruling.source_url,
                        document_id=ruling.ruling_number,
                        artifact_sha256=ruling.source_artifact_id,
                        page=1,
                        section="Kết quả phân loại"
                    ),
                    valid_from=ruling.valid_from.isoformat() if ruling.valid_from else None,
                    valid_to=ruling.valid_to.isoformat() if ruling.valid_to else None
                ))

        # 3. Search Content Chunks
        chunks = self.db.query(ContentChunk).all()
        for chunk in chunks:
            if chunk.valid_from and chunk.valid_from > as_of_date:
                continue
            if chunk.valid_to and chunk.valid_to < as_of_date:
                continue

            chunk_text = chunk.search_vector_text.lower()
            score = 0.0
            if any(tok in chunk_text for tok in search_tokens):
                score += 0.60

            if score > 0.0:
                results.append(SearchResultItem(
                    entity_type=chunk.entity_type,
                    entity_id=chunk.entity_id,
                    title=chunk.title or "Nội dung văn bản",
                    content_snippet=chunk.content_text[:300],
                    score=score,
                    authority_level="A1_SIGNED_OFFICIAL",
                    citation=Citation(
                        source_url=chunk.source_url,
                        page=chunk.page_number,
                        section=chunk.section_name
                    ),
                    valid_from=chunk.valid_from.isoformat() if chunk.valid_from else None,
                    valid_to=chunk.valid_to.isoformat() if chunk.valid_to else None
                ))

        # Sort by score descending and take top limit
        results.sort(key=lambda x: x.score, reverse=True)
        return SearchResponse(
            query=query,
            as_of=as_of_str,
            results=results[:limit]
        )
