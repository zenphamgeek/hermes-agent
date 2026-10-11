"""DOCX Document Parser (FR-042)."""

import io
from typing import List, Dict, Any, Optional
import docx

from .base import BaseParser, ParsedDocument, PageContent, TableData
from .vietnamese import normalize_vietnamese_text


class DOCXDocumentParser(BaseParser):
    name = "docx_parser"
    version = "1.0.0"
    supported_mime_types = [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword"
    ]

    def parse(self, raw_bytes: bytes, artifact_sha256: str, mime_type: str) -> ParsedDocument:
        doc = docx.Document(io.BytesIO(raw_bytes))
        blocks: List[str] = []
        for p in doc.paragraphs:
            text = normalize_vietnamese_text(p.text)
            if text:
                blocks.append(text)

        tables: List[TableData] = []
        for table in doc.tables:
            if not table.rows:
                continue
            headers = [normalize_vietnamese_text(cell.text) for cell in table.rows[0].cells]
            rows = []
            for row in table.rows[1:]:
                rows.append([normalize_vietnamese_text(cell.text) for cell in row.cells])
            tables.append(TableData(headers=headers, rows=rows))

        full_text = "\n\n".join(blocks)
        title = blocks[0] if blocks else None

        page = PageContent(
            page=1,
            text=full_text,
            blocks=blocks,
            tables=tables,
            ocr=False,
            confidence=1.0
        )

        return ParsedDocument(
            artifact_sha256=artifact_sha256,
            parser_name=self.name,
            parser_version=self.version,
            language="vi",
            title=title,
            metadata={"paragraph_count": len(blocks), "table_count": len(tables)},
            pages=[page],
            attachments=[],
            warnings=[]
        )
