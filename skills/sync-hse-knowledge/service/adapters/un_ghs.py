"""UNECE GHS Rev. 11 & International Chemical Safety Cards Adapters."""

from typing import Optional
from service.adapters.base import HSESourceAdapter, CandidateItem, DiscoveryPage


class UNGhsAdapter:
    source_id = "UN_GHS"

    def discover(self, cursor: Optional[str] = None, limit: int = 50) -> DiscoveryPage:
        items = [
            CandidateItem(
                item_id="DOC_GHS_REV_11_2025",
                source_id=self.source_id,
                title="Globally Harmonized System of Classification and Labelling of Chemicals (GHS Rev. 11, 2025)",
                source_url="https://unece.org/transport/dangerous-goods/ghs-rev11-2025",
                canonical_url="https://unece.org/transport/dangerous-goods/ghs-rev11-2025",
                content_class="ghs_classification",
                doc_number="GHS-Rev-11",
                published_date="2025-07-01",
                raw_content="""UNECE GHS REVISION 11 (2025)
Standardized Hazard Statements and Precautionary Statements

1. Physical Hazards:
- H225: Highly flammable liquid and vapour.
- H226: Flammable liquid and vapour.
- H280: Contains gas under pressure; may explode if heated.

2. Health Hazards:
- H302: Harmful if swallowed.
- H314: Causes severe skin burns and eye damage.
- H319: Causes serious eye irritation.
- H361d: Suspected of damaging the unborn child.

3. Precautionary Statements:
- P210: Keep away from heat, hot surfaces, sparks, open flames and other ignition sources. No smoking.
- P280: Wear protective gloves/protective clothing/eye protection/face protection.
- P305+P351+P338: IF IN EYES: Rinse cautiously with water for several minutes."""
            )
        ]
        return DiscoveryPage(items=items, next_cursor=None, has_more=False)

    def fetch_item(self, candidate: CandidateItem) -> CandidateItem:
        return candidate


class ILOWHOIcscAdapter:
    source_id = "ILO_WHO_ICSC"

    def discover(self, cursor: Optional[str] = None, limit: int = 50) -> DiscoveryPage:
        items = [
            CandidateItem(
                item_id="DOC_ICSC_0087_ACETONE",
                source_id=self.source_id,
                title="ICSC 0087 - Acetone (Chemical Safety Card)",
                source_url="https://www.ilo.org/dyn/icsc/showcard.display?p_card_id=0087",
                canonical_url="https://www.ilo.org/dyn/icsc/showcard.display?p_card_id=0087",
                content_class="chemical_safety_card",
                doc_number="ICSC-0087",
                published_date="2024-04-10",
                raw_content="""INTERNATIONAL CHEMICAL SAFETY CARD: ACETONE (ICSC 0087)
CAS Number: 67-64-1
UN Number: 1090
Molecular Formula: C3H6O / (CH3)2CO

Physical State: Colourless liquid with characteristic pungent odour.
Boiling Point: 56 °C
Flash Point: -18 °C c.c.
Explosive Limits: 2.2 - 13.0 vol% in air

First Aid:
- Inhalation: Fresh air, rest.
- Skin: Remove contaminated clothes, rinse skin with water.
- Eyes: First rinse with plenty of water for several minutes.
- Ingestion: Rinse mouth."""
            )
        ]
        return DiscoveryPage(items=items, next_cursor=None, has_more=False)

    def fetch_item(self, candidate: CandidateItem) -> CandidateItem:
        return candidate
