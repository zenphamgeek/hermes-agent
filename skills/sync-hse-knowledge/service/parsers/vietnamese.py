"""Vietnamese text normalizer and legal structure extractor."""

import re
import unicodedata
from typing import List, Tuple, Optional
from service.parsers.base import ParsedSection


class VietnameseLegalParser:
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalizes Unicode to NFC and preserves Vietnamese diacritics."""
        if not text:
            return ""
        norm = unicodedata.normalize("NFC", text)
        return re.sub(r"\s+", " ", norm).strip()

    @staticmethod
    def extract_articles(full_text: str) -> List[ParsedSection]:
        sections: List[ParsedSection] = []
        # Match "Điều <number>. <title>"
        article_pattern = re.compile(r"(Điều\s+(\d+[a-z]?)\.?\s*([^\n\r]*))", re.IGNORECASE)
        matches = list(article_pattern.finditer(full_text))

        for i, match in enumerate(matches):
            header = match.group(1).strip()
            art_num = match.group(2).strip()
            title = match.group(3).strip()
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
            body = full_text[start_pos:end_pos].strip()

            sections.append(ParsedSection(
                section_type="DIEU",
                code=f"DIEU_{art_num}",
                title=title or f"Điều {art_num}",
                content=body
            ))
        return sections
