"""Vietnam National Trade Repository Adapter (vntr.moit.gov.vn)."""

from typing import Optional, List
from .base import SourceAdapter, Candidate, DiscoveryPage


class VNVNTRAdapter(SourceAdapter):
    source_id = "VN_VNTR"
    name = "Vietnam National Trade Repository"
    jurisdiction = "VN"

    def discover(self, cursor: Optional[str] = None, limit: int = 50, taxonomy: Optional[str] = None) -> DiscoveryPage:
        page_num = int(cursor) if cursor and cursor.isdigit() else 1

        sample_urls = [
            ("https://vntr.moit.gov.vn/vi/administrative_rulings/ruling-01", "Phán quyết hành chính xác định mã số HS nhóm 8471"),
            ("https://vntr.moit.gov.vn/vi/question-and-answer/faq-02", "Hướng dẫn áp dụng thuế suất ưu đãi EVFTA cho linh kiện điện tử")
        ]

        candidates = []
        for url, title in sample_urls:
            canon = self.canonicalize_url(url)
            candidates.append(Candidate(
                url=url,
                canonical_url=canon,
                content_class="administrative_rulings",
                title=title
            ))

        next_page = str(page_num + 1) if page_num < 2 else None
        return DiscoveryPage(
            candidates=candidates,
            next_cursor=next_page,
            has_more=(next_page is not None),
            total_estimated=len(candidates)
        )
