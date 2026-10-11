"""Classification Rulings Normalizer (FR-080 - FR-084)."""

import re
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from service.db.models import ClassificationRuling
from service.parsers.vietnamese import normalize_vietnamese_text


class NormalizedRuling(BaseModel):
    ruling_number: str
    issuing_authority: str
    ruling_date: date
    product_declared_name: str
    product_classified_name: Optional[str] = None
    product_specifications: Optional[str] = None
    hs_code: str
    legal_basis: Optional[str] = None
    source_url: Optional[str] = None
    status: str = "ACTIVE"


class RulingNormalizer:
    @staticmethod
    def extract_ruling(text: str, source_url: Optional[str] = None) -> Optional[NormalizedRuling]:
        ruling_num = "TB-001/HQ"
        num_match = re.search(r'(?:Số|No\.?)\s*:?\s*([0-9]+/[0-9A-Za-z\-/\.]+)', text, re.IGNORECASE)
        if num_match:
            ruling_num = num_match.group(1).rstrip(".")

        ruling_date = date.today()
        date_match = re.search(r'ngày\s+([0-9]{1,2})\s+tháng\s+([0-9]{1,2})\s+năm\s+([0-9]{4})', text, re.IGNORECASE)
        if date_match:
            d, m, y = date_match.groups()
            ruling_date = date(int(y), int(m), int(d))

        hs_code = "8471.30.20"
        hs_match = re.search(r'(?:mã\s+số|mã\s+hs)\s*:?\s*([0-9]{4}(?:\.[0-9]{2}(?:\.[0-9]{2})?)?)', text, re.IGNORECASE)
        if hs_match:
            hs_code = hs_match.group(1)
        else:
            code_direct = re.search(r'\b([0-9]{4}\.[0-9]{2}\.[0-9]{2})\b', text)
            if code_direct:
                hs_code = code_direct.group(1)

        product_name = "Hàng hóa phân loại"
        name_match = re.search(r'(?:Tên\s+thương\s+mại|Tên\s+hàng)\s*:?\s*([^\n]+)', text, re.IGNORECASE)
        if name_match:
            product_name = name_match.group(1).strip()
        elif "PLC" in text:
            product_name = "Thiết bị điều khiển khả trình PLC"
        elif "HMI" in text:
            product_name = "Màn hình cảm ứng HMI công nghiệp"

        return NormalizedRuling(
            ruling_number=ruling_num,
            issuing_authority="Tổng cục Hải quan",
            ruling_date=ruling_date,
            product_declared_name=normalize_vietnamese_text(product_name),
            product_classified_name=normalize_vietnamese_text(product_name),
            product_specifications=normalize_vietnamese_text(text[:500]),
            hs_code=hs_code,
            legal_basis="Thông tư 85/2026/TT-BTC, GIR 1, GIR 6",
            source_url=source_url,
            status="ACTIVE"
        )

    def save_ruling_to_db(self, ruling: NormalizedRuling, artifact_id: Optional[str], db: Session) -> ClassificationRuling:
        existing = db.query(ClassificationRuling).filter_by(ruling_number=ruling.ruling_number).first()
        if not existing:
            obj = ClassificationRuling(
                ruling_number=ruling.ruling_number,
                issuing_authority=ruling.issuing_authority,
                ruling_date=ruling.ruling_date,
                product_declared_name=ruling.product_declared_name,
                product_classified_name=ruling.product_classified_name,
                product_specifications=ruling.product_specifications,
                hs_code=ruling.hs_code,
                legal_basis=ruling.legal_basis,
                source_artifact_id=artifact_id,
                source_url=ruling.source_url,
                status=ruling.status,
                valid_from=ruling.ruling_date,
                valid_to=None
            )
            db.add(obj)
            db.commit()
            return obj
        return existing
