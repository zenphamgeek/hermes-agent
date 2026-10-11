"""Legal document normalization and structural provision extraction (FR-050 - FR-054)."""

import re
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from service.db.models import Document, DocumentVersion, LegalProvision, DocumentRelation
from service.parsers.base import ParsedDocument
from service.parsers.vietnamese import normalize_vietnamese_text


class NormalizedProvision(BaseModel):
    provision_type: str  # CHUONG, MUC, DIEU, KHOAN, DIEM, PHU_LUC
    code: str
    title: Optional[str] = None
    content_text: str
    order_index: int


class NormalizedLegalDoc(BaseModel):
    doc_number: str
    doc_type: str
    issuing_authority: str
    title: str
    published_at: Optional[date] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    effective_status: str = "ACTIVE"
    provisions: List[NormalizedProvision] = Field(default_factory=list)
    related_doc_numbers: List[Dict[str, str]] = Field(default_factory=list)  # {"type": "REPLACES", "number": "..."}


class LegalDocNormalizer:
    @staticmethod
    def infer_doc_type(doc_number: str, title: str) -> str:
        text = f"{doc_number} {title}".lower()
        if "/tt-" in text or "thông tư" in text:
            return "ThongTu"
        if "/nd-cp" in text or "nghị định" in text:
            return "NghiDinh"
        if "/qd-" in text or "quyết định" in text:
            return "QuyetDinh"
        if "luật" in text or "/qh" in text:
            return "Luat"
        if "/tb-" in text or "thông báo" in text:
            return "ThongBao"
        return "VanBanPhapLuat"

    @staticmethod
    def extract_provisions(text: str) -> List[NormalizedProvision]:
        provisions = []
        # Regex for Articles (Điều X. ...)
        pattern = r'(Điều\s+([0-9]+)\.?\s*([^\n]*))\n([\s\S]*?)(?=(?:Điều\s+[0-9]+\.|$))'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        order = 0
        for m in matches:
            order += 1
            full_header, article_num, article_title, body = m.groups()
            provisions.append(NormalizedProvision(
                provision_type="DIEU",
                code=f"DIEU_{article_num}",
                title=normalize_vietnamese_text(article_title.strip() or full_header),
                content_text=normalize_vietnamese_text(body.strip()),
                order_index=order
            ))
        return provisions

    def normalize(self, parsed: ParsedDocument, source_authority_level: str = "A1_SIGNED_OFFICIAL") -> NormalizedLegalDoc:
        doc_number = parsed.doc_number or "UNKNOWN_DOC_NUM"
        title = parsed.title or "Văn bản quy phạm pháp luật"
        doc_type = self.infer_doc_type(doc_number, title)
        
        full_text = "\n\n".join([p.text for p in parsed.pages])
        provisions = self.extract_provisions(full_text)

        valid_from = None
        if parsed.issuing_date:
            try:
                valid_from = datetime.strptime(parsed.issuing_date, "%Y-%m-%d").date()
            except ValueError:
                pass

        return NormalizedLegalDoc(
            doc_number=doc_number,
            doc_type=doc_type,
            issuing_authority="Cơ quan ban hành",
            title=title,
            published_at=valid_from,
            valid_from=valid_from,
            valid_to=None,
            effective_status="ACTIVE",
            provisions=provisions,
            related_doc_numbers=[]
        )

    def save_to_db(self, normalized: NormalizedLegalDoc, artifact_id: str, parser_version: str, db: Session) -> DocumentVersion:
        doc = db.query(Document).filter_by(doc_number=normalized.doc_number).first()
        if not doc:
            doc = Document(
                doc_number=normalized.doc_number,
                doc_type=normalized.doc_type,
                issuing_authority=normalized.issuing_authority,
                title=normalized.title,
                jurisdiction="VN"
            )
            db.add(doc)
            db.flush()

        version = DocumentVersion(
            document_id=doc.document_id,
            source_artifact_id=artifact_id,
            authoritative_level="A1_SIGNED_OFFICIAL",
            language="vi",
            published_at=normalized.published_at,
            valid_from=normalized.valid_from,
            valid_to=normalized.valid_to,
            effective_status=normalized.effective_status,
            normalized_sha256=artifact_id,
            parser_version=parser_version,
            is_current=True
        )
        db.add(version)
        db.flush()

        for prov in normalized.provisions:
            lp = LegalProvision(
                document_version_id=version.version_id,
                provision_type=prov.provision_type,
                code=prov.code,
                title=prov.title,
                content_text=prov.content_text,
                order_index=prov.order_index
            )
            db.add(lp)

        db.commit()
        return version
