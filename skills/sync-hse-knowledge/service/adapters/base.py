"""HSE Source Adapter Protocol and Base Implementations."""

from typing import Protocol, List, Optional, Dict, Any
from pydantic import BaseModel


class CandidateItem(BaseModel):
    item_id: str
    source_id: str
    title: str
    source_url: str
    canonical_url: str
    content_class: str
    doc_number: Optional[str] = None
    published_date: Optional[str] = None
    raw_content: Optional[str] = None


class DiscoveryPage(BaseModel):
    items: List[CandidateItem]
    next_cursor: Optional[str] = None
    has_more: bool = False


class HSESourceAdapter(Protocol):
    source_id: str

    def discover(self, cursor: Optional[str] = None, limit: int = 50) -> DiscoveryPage:
        ...

    def fetch_item(self, candidate: CandidateItem) -> CandidateItem:
        ...
