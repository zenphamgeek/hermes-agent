"""IFC EHS Guidelines & US NIOSH / OSHA Adapters."""

from typing import Optional
from service.adapters.base import HSESourceAdapter, CandidateItem, DiscoveryPage


class IFCEhsAdapter:
    source_id = "IFC_EHS"

    def discover(self, cursor: Optional[str] = None, limit: int = 50) -> DiscoveryPage:
        items = [
            CandidateItem(
                item_id="DOC_IFC_GEN_EHS_2007",
                source_id=self.source_id,
                title="IFC World Bank Group General Environmental, Health, and Safety Guidelines",
                source_url="https://www.ifc.org/ehs-general",
                canonical_url="https://www.ifc.org/ehs-general",
                content_class="giip_environmental_limits",
                doc_number="IFC-EHS-GEN",
                published_date="2007-04-30",
                raw_content="""IFC GENERAL EHS GUIDELINES (GIIP)
Section 1.1 Air Emissions and Ambient Air Quality
Section 1.3 Wastewater and Ambient Water Quality
Table 1.3.1 Indicative Values for Treated Sanitary Sewage Discharges:
- pH: 6 - 9
- BOD5: 30 mg/L
- COD: 125 mg/L
- TSS: 50 mg/L
- Total Nitrogen: 10 mg/L
- Total Phosphorus: 2 mg/L"""
            )
        ]
        return DiscoveryPage(items=items, next_cursor=None, has_more=False)

    def fetch_item(self, candidate: CandidateItem) -> CandidateItem:
        return candidate


class USNioshNpgAdapter:
    source_id = "US_NIOSH_NPG"

    def discover(self, cursor: Optional[str] = None, limit: int = 50) -> DiscoveryPage:
        items = [
            CandidateItem(
                item_id="DOC_NIOSH_TOLUENE_0619",
                source_id=self.source_id,
                title="NIOSH Pocket Guide: Toluene (NPG 0619)",
                source_url="https://www.cdc.gov/niosh/npg/npgd0619.html",
                canonical_url="https://www.cdc.gov/niosh/npg/npgd0619.html",
                content_class="niosh_rel_limits",
                doc_number="NPG-0619",
                published_date="2023-11-01",
                raw_content="""NIOSH POCKET GUIDE TO CHEMICAL HAZARDS: TOLUENE
CAS Number: 108-88-3
Formula: C6H5CH3

Exposure Limits:
- NIOSH REL: TWA 100 ppm (375 mg/m3), STEL 150 ppm (560 mg/m3)
- OSHA PEL: TWA 200 ppm, Ceiling 300 ppm
- ACGIH TLV (2024): TWA 20 ppm (Skin, A4 - Not Classifiable as Human Carcinogen)

Respirator Recommendations:
- Up to 500 ppm: Chemical cartridge respirator with organic vapor cartridge(s)."""
            )
        ]
        return DiscoveryPage(items=items, next_cursor=None, has_more=False)

    def fetch_item(self, candidate: CandidateItem) -> CandidateItem:
        return candidate


class USOSHAAdapter:
    source_id = "US_OSHA"

    def discover(self, cursor: Optional[str] = None, limit: int = 50) -> DiscoveryPage:
        items = [
            CandidateItem(
                item_id="DOC_OSHA_1910_1200",
                source_id=self.source_id,
                title="OSHA 29 CFR 1910.1200 Hazard Communication Standard",
                source_url="https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1200",
                canonical_url="https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1200",
                content_class="osha_standard",
                doc_number="29-CFR-1910.1200",
                published_date="2024-05-20",
                raw_content="""OSHA 29 CFR 1910.1200 HAZARD COMMUNICATION STANDARD
(a) Purpose. To ensure that the hazards of all chemicals produced or imported are classified, and that information concerning the classified hazards is transmitted to employers and employees.
(g) Safety Data Sheets. Chemical manufacturers and importers shall obtain or develop a safety data sheet for each hazardous chemical they produce or import."""
            )
        ]
        return DiscoveryPage(items=items, next_cursor=None, has_more=False)

    def fetch_item(self, candidate: CandidateItem) -> CandidateItem:
        return candidate
