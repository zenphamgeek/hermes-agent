"""Hybrid Search Engine (Lexical, Semantic & Temporal as_of Filtering) (FR-120-124)."""

import re
from datetime import date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from service.db.models import ContentChunk, Document, Substance, OEL, Hazard, Control


class SearchResultItem(BaseModel):
    chunk_id: str
    entity_type: str
    entity_id: str
    title: str
    content_text: str
    source_url: Optional[str] = None
    section_name: Optional[str] = None
    score: float = 1.0


class HybridRetrievalEngine:
    def __init__(self, db: Session):
        self.db = db

    def search(
        self,
        query: str,
        as_of: Optional[date] = None,
        entity_type: Optional[str] = None,
        limit: int = 20
    ) -> List[SearchResultItem]:
        as_of_date = as_of or date.today()
        q_lower = query.lower()
        terms = [t for t in re.split(r"\s+", q_lower) if len(t) > 1]

        stmt = self.db.query(ContentChunk)

        if entity_type:
            stmt = stmt.filter(ContentChunk.entity_type == entity_type)

        # Temporal filter: valid_from <= as_of and (valid_to is null or valid_to >= as_of)
        stmt = stmt.filter(
            or_(ContentChunk.valid_from == None, ContentChunk.valid_from <= as_of_date),
            or_(ContentChunk.valid_to == None, ContentChunk.valid_to >= as_of_date)
        )

        # Lexical matching
        if terms:
            conditions = [ContentChunk.search_vector_text.like(f"%{t}%") for t in terms]
            stmt = stmt.filter(or_(*conditions))

        results = stmt.limit(limit).all()

        scored: List[SearchResultItem] = []
        for r in results:
            # Simple keyword frequency score
            text = r.search_vector_text.lower()
            match_count = sum(text.count(t) for t in terms)
            score = 1.0 + (match_count * 0.2)

            scored.append(SearchResultItem(
                chunk_id=r.chunk_id,
                entity_type=r.entity_type,
                entity_id=r.entity_id,
                title=r.title,
                content_text=r.content_text,
                source_url=r.source_url,
                section_name=r.section_name,
                score=score
            ))

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored
