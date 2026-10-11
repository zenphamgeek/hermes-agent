"""Vietnam National Legal Database Adapter (vbpl.vn)."""

from typing import Optional, List
from .base import SourceAdapter, Candidate, DiscoveryPage


class VNVBPLAdapter(SourceAdapter):
    source_id = "VN_VBPL"
    name = "Vietnam National Legal Database"
    jurisdiction = "VN"

    def discover(self, cursor: Optional[str] = None, limit: int = 50, taxonomy: Optional[str] = None) -> DiscoveryPage:
        page_num = int(cursor) if cursor and cursor.isdigit() else 1

        sample_urls = [
            ("https://vbpl.vn/pages/vbpq-toanvan.aspx?ItemID=165200", "Luật Hải quan số 54/2014/QH13"),
            ("https://vbpl.vn/pages/vbpq-toanvan.aspx?ItemID=172300", "Luật Thuế xuất khẩu, thuế nhập khẩu số 107/2016/QH13")
        ]

        candidates = []
        for url, title in sample_urls:
            canon = self.canonicalize_url(url)
            candidates.append(Candidate(
                url=url,
                canonical_url=canon,
                content_class="national_legal_database",
                title=title
            ))

        next_page = str(page_num + 1) if page_num < 2 else None
        return DiscoveryPage(
            candidates=candidates,
            next_cursor=next_page,
            has_more=(next_page is not None),
            total_estimated=len(candidates) * 2
        )
