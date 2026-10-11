"""Parser Base Protocol and Schema (FR-040 - FR-047)."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TableData(BaseModel):
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    caption: Optional[str] = None


class PageContent(BaseModel):
    page: int = 1
    text: str = ""
    blocks: List[str] = Field(default_factory=list)
    tables: List[TableData] = Field(default_factory=list)
    ocr: bool = False
    confidence: float = 1.0


class ParsedDocument(BaseModel):
    artifact_sha256: str
    parser_name: str
    parser_version: str
    language: str = "vi"
    title: Optional[str] = None
    doc_number: Optional[str] = None
    issuing_date: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    pages: List[PageContent] = Field(default_factory=list)
    attachments: List[Dict[str, str]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class BaseParser:
    name: str = "base_parser"
    version: str = "1.0.0"
    supported_mime_types: List[str] = []

    def parse(self, raw_bytes: bytes, artifact_sha256: str, mime_type: str) -> ParsedDocument:
        raise NotImplementedError
