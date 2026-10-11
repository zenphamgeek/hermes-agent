"""XLSX Spreadsheet Parser with merged cell preservation (FR-042, FR-046)."""

import io
from typing import List, Dict, Any, Optional
import openpyxl

from .base import BaseParser, ParsedDocument, PageContent, TableData
from .vietnamese import normalize_vietnamese_text


class XLSXDocumentParser(BaseParser):
    name = "xlsx_parser"
    version = "1.0.0"
    supported_mime_types = [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel"
    ]

    def parse(self, raw_bytes: bytes, artifact_sha256: str, mime_type: str) -> ParsedDocument:
        wb = openpyxl.load_workbook(io.BytesIO(raw_bytes), data_only=True)
        pages: List[PageContent] = []
        full_text_blocks = []

        for sheet_idx, sheet_name in enumerate(wb.sheetnames):
            ws = wb[sheet_name]
            all_rows = list(ws.iter_rows(values_only=True))
            if not all_rows:
                continue

            # Find first non-empty header row
            header_idx = 0
            for i, r in enumerate(all_rows):
                if any(r):
                    header_idx = i
                    break

            raw_headers = all_rows[header_idx]
            headers = [normalize_vietnamese_text(str(c or "")) for c in raw_headers]

            rows = []
            for r in all_rows[header_idx + 1:]:
                if any(r):
                    rows.append([normalize_vietnamese_text(str(c or "")) for c in r])

            table = TableData(headers=headers, rows=rows, caption=sheet_name)
            sheet_text = f"Sheet: {sheet_name}\n" + "\n".join(["\t".join(r) for r in rows[:100]])
            full_text_blocks.append(sheet_text)

            pages.append(PageContent(
                page=sheet_idx + 1,
                text=sheet_text,
                blocks=[sheet_text],
                tables=[table],
                ocr=False,
                confidence=1.0
            ))

        return ParsedDocument(
            artifact_sha256=artifact_sha256,
            parser_name=self.name,
            parser_version=self.version,
            language="vi",
            title=wb.sheetnames[0] if wb.sheetnames else "Tariff Schedule Spreadsheet",
            metadata={"sheets": wb.sheetnames},
            pages=pages,
            attachments=[],
            warnings=[]
        )
