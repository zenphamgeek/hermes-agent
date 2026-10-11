"""Hazard, Control and Environmental Limits Normalizers."""

from typing import Tuple, List
from sqlalchemy.orm import Session

from service.db.models import Hazard, Control, EnvironmentalLimit


class HazardControlNormalizer:
    @staticmethod
    def normalize_hazard_and_controls(
        hazard_code: str,
        category: str,
        title: str,
        description: str,
        controls_list: List[dict],
        db: Session
    ) -> Tuple[Hazard, List[Control]]:
        hazard = db.query(Hazard).filter_by(code=hazard_code).first()
        if not hazard:
            hazard = Hazard(
                code=hazard_code,
                category=category,
                title=title,
                description=description
            )
            db.add(hazard)
            db.flush()

        saved_controls = []
        for ctrl_data in controls_list:
            ctrl = Control(
                hazard_id=hazard.hazard_id,
                hierarchy_level=ctrl_data["hierarchy_level"],
                title=ctrl_data["title"],
                verification_method=ctrl_data.get("verification_method"),
                frequency=ctrl_data.get("frequency", "continuous")
            )
            db.add(ctrl)
            saved_controls.append(ctrl)

        db.commit()
        return hazard, saved_controls


class EnvironmentalLimitNormalizer:
    @staticmethod
    def normalize_limit(
        pollutant_name: str,
        medium: str,
        max_concentration: float,
        unit: str,
        source_reg: str,
        db: Session
    ) -> EnvironmentalLimit:
        limit = EnvironmentalLimit(
            pollutant_name=pollutant_name,
            medium=medium,
            max_concentration=max_concentration,
            unit=unit,
            source_regulation=source_reg,
            authority_level="A2_MANDATORY_TECH_REG"
        )
        db.add(limit)
        db.commit()
        return limit
