"""Base parser protocol and parsed representations."""

from typing import Protocol, Dict, Any, List, Optional
from pydantic import BaseModel


class ParsedSection(BaseModel):
    section_type: str  # CHUONG, MUC, DIEU, KHOAN, DIEM, PHU_LUC, SDS_SECTION
    code: str
    title: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = {}


class ParsedDocumentResult(BaseModel):
    parser_name: str
    parser_version: str = "1.0.0"
    doc_number: Optional[str] = None
    title: Optional[str] = None
    issuing_authority: Optional[str] = None
    published_date: Optional[str] = None
    sections: List[ParsedSection] = []
    raw_text: str = ""
    completeness_score: float = 1.0


class DocumentParser(Protocol):
    parser_name: str
    parser_version: str

    def parse(self, raw_bytes: bytes, mime_type: str) -> ParsedDocumentResult:
        ...
