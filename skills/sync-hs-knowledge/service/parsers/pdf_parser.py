"""PDF Document Parser (FR-041)."""

import io
from typing import List, Dict, Any, Optional
import re

from .base import BaseParser, ParsedDocument, PageContent, TableData
from .vietnamese import normalize_vietnamese_text


class PDFDocumentParser(BaseParser):
    name = "pdf_parser"
    version = "1.1.0"
    supported_mime_types = ["application/pdf"]

    def parse(self, raw_bytes: bytes, artifact_sha256: str, mime_type: str) -> ParsedDocument:
        pages: List[PageContent] = []
        full_text_list = []
        doc_number = None
        issuing_date = None
        title = None
        warnings = []

        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
                for idx, pdf_page in enumerate(pdf.pages):
                    page_num = idx + 1
                    page_text = pdf_page.extract_text() or ""
                    page_text = normalize_vietnamese_text(page_text)
                    full_text_list.append(page_text)

                    # Extract tables from page
                    tables: List[TableData] = []
                    extracted_tables = pdf_page.extract_tables() or []
                    for t in extracted_tables:
                        if t and len(t) > 1:
                            headers = [normalize_vietnamese_text(str(c or "")) for c in t[0]]
                            rows = [[normalize_vietnamese_text(str(c or "")) for c in r] for r in t[1:]]
                            tables.append(TableData(headers=headers, rows=rows))

                    blocks = [b.strip() for b in page_text.split("\n\n") if b.strip()]

                    pages.append(PageContent(
                        page=page_num,
                        text=page_text,
                        blocks=blocks,
                        tables=tables,
                        ocr=False,
                        confidence=1.0 if len(page_text) > 50 else 0.5
                    ))
        except Exception as e:
            warnings.append(f"PDF extraction error: {str(e)}")
            # Fallback simple text extraction
            text_guess = raw_bytes.decode("latin1", errors="ignore")
            pages.append(PageContent(
                page=1,
                text=text_guess[:1000],
                blocks=[],
                tables=[],
                ocr=False,
                confidence=0.1
            ))

        combined_text = "\n".join(full_text_list)

        # Regex for document number and date
        doc_num_match = re.search(r'(Số|No\.?):\s*([0-9]+/[0-9A-Z\-]+)', combined_text, re.IGNORECASE)
        if doc_num_match:
            doc_number = doc_num_match.group(2)

        date_match = re.search(r'ngày\s+([0-9]{1,2})\s+tháng\s+([0-9]{1,2})\s+năm\s+([0-9]{4})', combined_text, re.IGNORECASE)
        if date_match:
            d, m, y = date_match.groups()
            issuing_date = f"{y}-{int(m):02d}-{int(d):02d}"

        # First prominent non-empty line as title
        lines = [line.strip() for line in combined_text.split("\n") if len(line.strip()) > 10]
        if lines:
            title = lines[0]

        return ParsedDocument(
            artifact_sha256=artifact_sha256,
            parser_name=self.name,
            parser_version=self.version,
            language="vi",
            title=title,
            doc_number=doc_number,
            issuing_date=issuing_date,
            metadata={"page_count": len(pages)},
            pages=pages,
            attachments=[],
            warnings=warnings
        )
