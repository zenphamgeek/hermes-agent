"""Vietnam Customs Tariff and HS Nomenclature Adapter (customs.gov.vn)."""

from typing import Optional, List
from .base import SourceAdapter, Candidate, DiscoveryPage


class VNCustomsTariffAdapter(SourceAdapter):
    source_id = "VN_CUSTOMS_TARIFF"
    name = "Vietnam Customs Tariff & Nomenclature"
    jurisdiction = "VN"

    def discover(self, cursor: Optional[str] = None, limit: int = 50, taxonomy: Optional[str] = None) -> DiscoveryPage:
        page_num = int(cursor) if cursor and cursor.isdigit() else 1

        sample_urls = [
            ("https://www.customs.gov.vn/index.jsp?aid=183995&cid=25&pageId=2", "Danh mục hàng hóa xuất khẩu, nhập khẩu Việt Nam 2022/2026"),
            ("https://www.customs.gov.vn/index.jsp?aid=184001&cid=25&pageId=3", "Biểu thuế xuất nhập khẩu ưu đãi MFN 2026")
        ]

        if taxonomy:
            sample_urls.append(
                (f"https://www.customs.gov.vn/index.jsp?aid=184005&cid=25&chapter={taxonomy}", f"Biểu thuế & phân loại phân nhóm: {taxonomy}")
            )

        candidates = []
        for url, title in sample_urls:
            canon = self.canonicalize_url(url)
            candidates.append(Candidate(
                url=url,
                canonical_url=canon,
                content_class="tariff_schedule",
                title=title
            ))

        next_page = str(page_num + 1) if page_num < 2 and not taxonomy else None
        return DiscoveryPage(
            candidates=candidates,
            next_cursor=next_page,
            has_more=(next_page is not None),
            total_estimated=len(candidates)
        )
