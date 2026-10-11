"""ISO Standards Gated Adapters (ISO 14001:2026, ISO 45001:2018)."""

from typing import Optional
from service.adapters.base import HSESourceAdapter, CandidateItem, DiscoveryPage


class ISOGatedAdapter:
    def __init__(self, source_id: str = "ISO_14001"):
        self.source_id = source_id

    def discover(self, cursor: Optional[str] = None, limit: int = 50) -> DiscoveryPage:
        if self.source_id == "ISO_14001":
            items = [
                CandidateItem(
                    item_id="DOC_ISO_14001_2026",
                    source_id=self.source_id,
                    title="ISO 14001:2026 Environmental Management Systems - Requirements with guidance for use",
                    source_url="https://www.iso.org/standard/14001",
                    canonical_url="https://www.iso.org/standard/14001",
                    content_class="standards_metadata",
                    doc_number="ISO-14001:2026",
                    published_date="2026-03-15",
                    raw_content="""ISO 14001:2026 (METADATA ONLY - LICENSE GATED)
Edition: 4th Edition (2026)
Status: Published / Active
Scope: Specifies requirements for an environmental management system that an organization can use to enhance its environmental performance.
Clauses Summary:
4. Context of the organization
5. Leadership
6. Planning (6.1 Actions to address risks and opportunities, 6.1.2 Environmental aspects, 6.1.3 Compliance obligations)
7. Support
8. Operation (8.1 Operational planning and control, 8.2 Emergency preparedness and response)
9. Performance evaluation (9.1.2 Evaluation of compliance)
10. Improvement"""
                )
            ]
        else:
            items = [
                CandidateItem(
                    item_id="DOC_ISO_45001_2018",
                    source_id=self.source_id,
                    title="ISO 45001:2018 Occupational health and safety management systems",
                    source_url="https://www.iso.org/standard/63787.html",
                    canonical_url="https://www.iso.org/standard/63787.html",
                    content_class="standards_metadata",
                    doc_number="ISO-45001:2018",
                    published_date="2018-03-12",
                    raw_content="""ISO 45001:2018 (METADATA ONLY - LICENSE GATED)
Edition: 1st Edition (2018 + Amd 1:2024)
Status: Published / Active
Clauses Summary:
4. Context of the organization
5. Leadership and worker participation
6. Planning (6.1.2 Hazard identification and assessment of risks and opportunities)
7. Support
8. Operation (8.1.2 Eliminating hazards and reducing OH&S risks)
9. Performance evaluation
10. Improvement"""
                )
            ]
        return DiscoveryPage(items=items, next_cursor=None, has_more=False)

    def fetch_item(self, candidate: CandidateItem) -> CandidateItem:
        return candidate
