"""Chemical SDS, GHS and OEL Normalizers."""

from datetime import date
from typing import Tuple, List
from sqlalchemy.orm import Session

from service.parsers.sds_parser import ParsedSDSResult
from service.db.models import Substance, ChemicalProduct, SDS, GHSProfile, OEL


class ChemicalSDSNormalizer:
    @staticmethod
    def normalize_sds(
        parsed_sds: ParsedSDSResult,
        artifact_id: str,
        db: Session
    ) -> Tuple[ChemicalProduct, SDS, GHSProfile, List[Substance]]:
        # 1. Chemical Product
        product = db.query(ChemicalProduct).filter_by(trade_name=parsed_sds.product_name).first()
        if not product:
            product = ChemicalProduct(
                trade_name=parsed_sds.product_name,
                supplier_name=parsed_sds.supplier_name or "Chemical Supplier",
                flash_point_c=parsed_sds.flash_point_c,
                is_mixture=len(parsed_sds.cas_numbers) > 1
            )
            db.add(product)
            db.flush()

        # 2. SDS record
        sds = SDS(
            product_id=product.product_id,
            revision_date=date.today(),
            language="vi",
            source_artifact_id=artifact_id,
            sections_json={str(k): v for k, v in parsed_sds.sections.items()},
            completeness_score=parsed_sds.completeness_score,
            is_current=True
        )
        db.add(sds)
        db.flush()

        # 3. GHS Profile
        ghs = GHSProfile(
            product_id=product.product_id,
            edition="Rev_11",
            signal_word=parsed_sds.ghs_signal_word or "WARNING",
            pictograms=["GHS02", "GHS07"] if parsed_sds.flash_point_c and parsed_sds.flash_point_c < 23 else ["GHS07"],
            h_statements=parsed_sds.ghs_h_statements,
            p_statements=parsed_sds.ghs_p_statements
        )
        db.add(ghs)

        # 4. Substances
        substances = []
        for cas in parsed_sds.cas_numbers:
            sub = db.query(Substance).filter_by(cas_number=cas).first()
            if not sub:
                sub = Substance(
                    cas_number=cas,
                    chemical_name_en=f"Substance {cas}",
                    chemical_name_vi=f"Hóa chất {cas}"
                )
                db.add(sub)
                db.flush()
            substances.append(sub)

        db.commit()
        return product, sds, ghs, substances


class OELNormalizer:
    @staticmethod
    def normalize_oel(
        cas_number: str,
        jurisdiction: str,
        twa_mg_m3: float,
        stel_mg_m3: float,
        source_doc: str,
        authority_level: str,
        db: Session
    ) -> OEL:
        sub = db.query(Substance).filter_by(cas_number=cas_number).first()
        if not sub:
            sub = Substance(
                cas_number=cas_number,
                chemical_name_en=f"Substance {cas_number}",
                chemical_name_vi=f"Hóa chất {cas_number}"
            )
            db.add(sub)
            db.flush()

        oel = OEL(
            substance_id=sub.substance_id,
            jurisdiction=jurisdiction,
            authority_level=authority_level,
            twa_mg_m3=twa_mg_m3,
            stel_mg_m3=stel_mg_m3,
            source_doc_number=source_doc
        )
        db.add(oel)
        db.commit()
        return oel
