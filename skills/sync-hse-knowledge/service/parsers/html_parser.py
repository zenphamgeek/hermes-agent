"""HTML Document Parser using BeautifulSoup / selectolax."""

import re
from bs4 import BeautifulSoup
from service.parsers.base import ParsedDocumentResult, ParsedSection
from service.parsers.vietnamese import VietnameseLegalParser


class HTMLDocumentParser:
    parser_name = "html_parser"
    parser_version = "1.0.0"

    def parse(self, raw_bytes: bytes, mime_type: str = "text/html") -> ParsedDocumentResult:
        html_text = raw_bytes.decode("utf-8", errors="replace")
        soup = BeautifulSoup(html_text, "html.parser")

        # Strip scripts and styles
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else None
        h1 = soup.find("h1")
        if h1 and h1.get_text():
            title = h1.get_text().strip()

        full_text = VietnameseLegalParser.normalize_text(soup.get_text(separator="\n"))
        sections = VietnameseLegalParser.extract_articles(full_text)

        # Detect doc number
        doc_num_match = re.search(r"Số:\s*([0-9]+/[0-9]+/QH[0-9]+|[0-9]+/[0-9]+/NĐ-CP|[0-9]+/[0-9]+/TT-[A-Z]+|QCVN\s+[0-9:]+/[A-Z]+)", full_text, re.IGNORECASE)
        doc_number = doc_num_match.group(1).strip() if doc_num_match else None

        return ParsedDocumentResult(
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            doc_number=doc_number,
            title=title,
            sections=sections,
            raw_text=full_text,
            completeness_score=1.0
        )
