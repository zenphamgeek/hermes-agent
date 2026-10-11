"""Vietnam Government Legal Portal Adapter (vanban.chinhphu.vn)."""

from typing import Optional, List
from .base import SourceAdapter, Candidate, DiscoveryPage


class VNGovLegalAdapter(SourceAdapter):
    source_id = "VN_GOV_LEGAL"
    name = "Vietnam Government Legal Portal"
    jurisdiction = "VN"

    def discover(self, cursor: Optional[str] = None, limit: int = 50, taxonomy: Optional[str] = None) -> DiscoveryPage:
        page_num = int(cursor) if cursor and cursor.isdigit() else 1
        
        # Base candidates representing official legal circulars / decrees
        sample_urls = [
            ("https://vanban.chinhphu.vn/?pageid=27160&docid=218770", "Thông tư 85/2026/TT-BTC quy định về phân loại hàng hóa xuất nhập khẩu"),
            ("https://vanban.chinhphu.vn/?pageid=27160&docid=218500", "Nghị định 08/2015/NĐ-CP quy định chi tiết và biện pháp thi hành Luật Hải quan")
        ]

        candidates = []
        for url, title in sample_urls:
            canon = self.canonicalize_url(url)
            candidates.append(Candidate(
                url=url,
                canonical_url=canon,
                content_class="legal_document",
                title=title
            ))

        next_page = str(page_num + 1) if page_num < 3 else None
        return DiscoveryPage(
            candidates=candidates,
            next_cursor=next_page,
            has_more=(next_page is not None),
            total_estimated=len(candidates) * 3
        )
