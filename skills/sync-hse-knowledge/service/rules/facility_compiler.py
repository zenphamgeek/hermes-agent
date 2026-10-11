"""Facility Profile Facts Compiler (FR-045)."""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel


class FacilityContext(BaseModel):
    facility_id: str
    province: str
    industrial_zone: Optional[str] = None
    worker_count: int = 100
    activities: List[str] = []
    chemicals_stored: List[str] = []
    chemical_storage_quantity_kg: float = 0.0
    wastewater_flow_m3_day: float = 0.0
    stack_emission_flow_m3_h: float = 0.0
    has_boiler: bool = False
    has_lifting_equipment: bool = False
    has_confined_space: bool = False
    iso_certifications: List[str] = []


class FacilityProfileCompiler:
    @staticmethod
    def compile_facts(ctx: FacilityContext) -> Dict[str, Any]:
        """Flattens structured facility context into evaluator fact dictionary."""
        facts: Dict[str, Any] = {
            "facility.id": ctx.facility_id,
            "facility.province": ctx.province,
            "facility.industrial_zone": ctx.industrial_zone,
            "facility.worker_count": ctx.worker_count,
            "activity.types": ctx.activities,
            "chemical.stored_substances": ctx.chemicals_stored,
            "chemical.storage_quantity_kg": ctx.chemical_storage_quantity_kg,
            "environmental.wastewater_flow_m3_day": ctx.wastewater_flow_m3_day,
            "environmental.stack_emission_flow_m3_h": ctx.stack_emission_flow_m3_h,
            "asset.has_boiler": ctx.has_boiler,
            "asset.has_lifting_equipment": ctx.has_lifting_equipment,
            "asset.has_confined_space": ctx.has_confined_space,
            "commitments.iso": ctx.iso_certifications
        }

        # Derive helper tags
        if "store" in ctx.activities or ctx.chemical_storage_quantity_kg > 0:
            facts["activity.type"] = "store"
        if any(c in ["toluene", "acetone", "solvent"] for c in [chem.lower() for chem in ctx.chemicals_stored]):
            facts["chemical.list_membership"] = ["hazardous", "special_control"]

        return facts
