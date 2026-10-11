"""HS Hierarchy and Nomenclature Normalizer (FR-060 - FR-065)."""

import re
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from service.db.models import HSEdition, HSNode, QualityIssue
from service.parsers.vietnamese import normalize_vietnamese_text


class NormalizedHSNode(BaseModel):
    code: str  # Clean formatted code e.g. 84, 8471, 8471.30, 8471.30.20
    level: int  # 1: Chapter(2), 2: Heading(4), 3: Subheading(6), 4: National(8/10)
    parent_code: Optional[str] = None
    description_vi: str
    description_en: Optional[str] = None
    is_leaf: bool = False


class HSTreeNormalizer:
    @staticmethod
    def clean_code(raw_code: str) -> str:
        """Removes spaces, dots, dashes for standardization."""
        return re.sub(r'[^0-9A-Za-z]', '', raw_code.strip())

    @staticmethod
    def format_code(clean_digits: str) -> str:
        """Formats clean digits into standard dotted notation: 84 -> 84, 8471 -> 8471, 847130 -> 8471.30, 84713020 -> 8471.30.20."""
        n = len(clean_digits)
        if n == 2:
            return clean_digits
        if n == 4:
            return clean_digits
        if n == 6:
            return f"{clean_digits[:4]}.{clean_digits[4:6]}"
        if n == 8:
            return f"{clean_digits[:4]}.{clean_digits[4:6]}.{clean_digits[6:8]}"
        if n == 10:
            return f"{clean_digits[:4]}.{clean_digits[4:6]}.{clean_digits[6:8]}.{clean_digits[8:10]}"
        return clean_digits

    @classmethod
    def infer_level_and_parent(cls, formatted_code: str) -> Tuple[int, Optional[str]]:
        digits = cls.clean_code(formatted_code)
        n = len(digits)
        if n <= 2:
            return 1, None
        if n <= 4:
            return 2, cls.format_code(digits[:2])
        if n <= 6:
            return 3, cls.format_code(digits[:4])
        if n <= 8:
            return 4, cls.format_code(digits[:6])
        return 5, cls.format_code(digits[:8])

    @classmethod
    def validate_parent_child(cls, nodes: List[NormalizedHSNode]) -> List[QualityIssue]:
        """Ensures all children have existing parents in the same tree batch."""
        known_codes = {n.code for n in nodes}
        issues = []
        for n in nodes:
            if n.parent_code and n.parent_code not in known_codes and n.level > 1:
                issues.append(QualityIssue(
                    entity_type="hs_node",
                    entity_id=n.code,
                    severity="CRITICAL",
                    issue_type="MISSING_PARENT",
                    description=f"HS code {n.code} is missing parent {n.parent_code} in the edition"
                ))
        return issues

    def save_nodes_to_db(self, edition_id: str, nodes: List[NormalizedHSNode], db: Session):
        for n in nodes:
            existing = db.query(HSNode).filter_by(edition_id=edition_id, code=n.code).first()
            if not existing:
                node = HSNode(
                    edition_id=edition_id,
                    code=n.code,
                    level=n.level,
                    parent_code=n.parent_code,
                    description_vi=normalize_vietnamese_text(n.description_vi),
                    description_en=n.description_en,
                    is_leaf=n.is_leaf
                )
                db.add(node)
            else:
                existing.description_vi = normalize_vietnamese_text(n.description_vi)
        db.commit()
