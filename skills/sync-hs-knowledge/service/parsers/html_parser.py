"""HTML Document Parser using selectolax / BeautifulSoup (FR-040)."""

from typing import List, Dict, Any, Optional
import re
from bs4 import BeautifulSoup
try:
    from selectolax.parser import HTMLParser as FastHTMLParser
    HAS_SELECTOLAX = True
except ImportError:
    HAS_SELECTOLAX = False

from .base import BaseParser, ParsedDocument, PageContent, TableData
from .vietnamese import normalize_vietnamese_text


class HTMLDocumentParser(BaseParser):
    name = "html_parser"
    version = "1.1.0"
    supported_mime_types = ["text/html", "application/xhtml+xml"]

    def parse(self, raw_bytes: bytes, artifact_sha256: str, mime_type: str) -> ParsedDocument:
        html_text = raw_bytes.decode("utf-8", errors="replace")
        soup = BeautifulSoup(html_text, "html.parser")

        # 1. Extract Title
        title = ""
        title_tag = soup.find("title") or soup.find("h1")
        if title_tag:
            title = normalize_vietnamese_text(title_tag.get_text())

        # 2. Extract Document Number & Dates using Regex
        doc_number = None
        issuing_date = None

        doc_num_match = re.search(r'(?:Số|No\.?)\s*:?\s*([0-9]+/[0-9A-Za-z\-/\.]+)', html_text, re.IGNORECASE)
        if doc_num_match:
            doc_number = doc_num_match.group(1).rstrip(".")

        date_match = re.search(r'ngày\s+([0-9]{1,2})\s+tháng\s+([0-9]{1,2})\s+năm\s+([0-9]{4})', html_text, re.IGNORECASE)
        if date_match:
            d, m, y = date_match.groups()
            issuing_date = f"{y}-{int(m):02d}-{int(d):02d}"

        # 3. Extract Tables
        tables: List[TableData] = []
        for table in soup.find_all("table"):
            headers = []
            rows = []
            for th in table.find_all("th"):
                headers.append(normalize_vietnamese_text(th.get_text()))

            for tr in table.find_all("tr"):
                cells = [normalize_vietnamese_text(td.get_text()) for td in tr.find_all("td")]
                if cells:
                    rows.append(cells)

            caption = ""
            cap_tag = table.find("caption")
            if cap_tag:
                caption = normalize_vietnamese_text(cap_tag.get_text())

            if rows:
                tables.append(TableData(headers=headers, rows=rows, caption=caption or None))

        # 4. Extract Attachments
        attachments: List[Dict[str, str]] = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if any(href.lower().endswith(ext) for ext in [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".zip"]):
                link_text = normalize_vietnamese_text(a.get_text()) or href.split("/")[-1]
                attachments.append({"url": href, "name": link_text})

        # 5. Extract Main Text Blocks
        blocks: List[str] = []
        for p in soup.find_all(["p", "div", "li"]):
            text = normalize_vietnamese_text(p.get_text())
            if text and len(text) > 15 and text not in blocks:
                blocks.append(text)

        full_text = "\n\n".join(blocks)

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
            title=title or None,
            doc_number=doc_number,
            issuing_date=issuing_date,
            metadata={"total_tables": len(tables), "total_attachments": len(attachments)},
            pages=[page],
            attachments=attachments,
            warnings=[]
        )
