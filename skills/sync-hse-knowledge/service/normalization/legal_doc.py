"""Legal Document and Obligation Normalizers."""

from typing import List, Dict, Any, Optional, Tuple
from datetime import date
from sqlalchemy.orm import Session

from service.parsers.base import ParsedDocumentResult, ParsedSection
from service.db.models import Document, DocumentVersion, LegalProvision, Obligation, ObligationVersion


class LegalDocumentNormalizer:
    @staticmethod
    def normalize_document(
        parsed: ParsedDocumentResult,
        source_id: str,
        artifact_id: str,
        authority_level: str,
        db: Session
    ) -> Tuple[Document, DocumentVersion, List[LegalProvision]]:
        doc_number = parsed.doc_number or f"DOC-{source_id}-{date.today()}"
        doc_type = "Luat" if "Luật" in (parsed.title or "") else ("QCVN" if "QCVN" in (parsed.title or "") else "NghiDinh")

        # 1. Document record
        doc = db.query(Document).filter_by(doc_number=doc_number).first()
        if not doc:
            doc = Document(
                doc_number=doc_number,
                doc_type=doc_type,
                issuing_authority=parsed.issuing_authority or "Quốc hội / Chính phủ / Bộ",
                title=parsed.title or doc_number,
                jurisdiction="VN"
            )
            db.add(doc)
            db.flush()

        # 2. Document Version
        version = DocumentVersion(
            document_id=doc.document_id,
            version_number=1,
            source_artifact_id=artifact_id,
            authoritative_level=authority_level,
            normalized_sha256="normalized_" + doc_number,
            parser_version=parsed.parser_version,
            is_current=True
        )
        db.add(version)
        db.flush()

        # 3. Provisions
        provisions = []
        for idx, sec in enumerate(parsed.sections):
            prov = LegalProvision(
                version_id=version.version_id,
                provision_type=sec.section_type,
                code=sec.code,
                title=sec.title,
                content_text=sec.content,
                order_index=idx
            )
            db.add(prov)
            provisions.append(prov)

        db.commit()
        return doc, version, provisions


class ObligationExtractor:
    @staticmethod
    def extract_obligations(
        provision: LegalProvision,
        doc_number: str,
        authority_level: str,
        db: Session
    ) -> List[ObligationVersion]:
        extracted = []
        content = provision.content_text.lower()

        # Rule heuristics for obligation keywords
        if "phải" in content or "có trách nhiệm" in content or "yêu cầu" in content:
            code = f"OBL_{doc_number}_{provision.code}".replace("/", "_").replace(":", "_").replace(" ", "_")
            
            obl = db.query(Obligation).filter_by(code=code).first()
            if not obl:
                domain = "safety"
                if "môi trường" in content or "xả thải" in content:
                    domain = "environment"
                elif "hóa chất" in content or "sds" in content:
                    domain = "chemical"
                elif "pccc" in content or "chữa cháy" in content:
                    domain = "fire"
                elif "y tế" in content or "khám sức khỏe" in content:
                    domain = "health"

                obl = Obligation(
                    code=code,
                    title=f"Nghĩa vụ theo {doc_number} {provision.title or provision.code}",
                    domain=domain
                )
                db.add(obl)
                db.flush()

            actor = "employer" if "người sử dụng lao động" in content else ("facility_owner" if "cơ sở" in content else "operator")
            action = "inspect" if "kiểm định" in content else ("report" if "báo cáo" in content else "comply")
            target = "equipment" if "máy" in content or "thiết bị" in content else "facility"

            obl_ver = ObligationVersion(
                obligation_id=obl.obligation_id,
                actor_type=actor,
                action_type=action,
                object_type=target,
                requirement_text=provision.content_text,
                authority_level=authority_level,
                source_provision_id=provision.provision_id,
                rule_review_status="APPROVED",
                confidence=0.95
            )
            db.add(obl_ver)
            extracted.append(obl_ver)

        db.commit()
        return extracted
