"""Vietnam Customs Advance Classification Rulings Adapter (customs.gov.vn)."""

from typing import Optional, List
from .base import SourceAdapter, Candidate, DiscoveryPage


class VNCustomsRulingsAdapter(SourceAdapter):
    source_id = "VN_CUSTOMS_RULINGS"
    name = "Vietnam Customs Classification Rulings"
    jurisdiction = "VN"

    def discover(self, cursor: Optional[str] = None, limit: int = 50, taxonomy: Optional[str] = None) -> DiscoveryPage:
        page_num = int(cursor) if cursor and cursor.isdigit() else 1

        sample_urls = [
            ("https://www.customs.gov.vn/index.jsp?cid=25&ruling_id=8921", "Thông báo xác định trước mã số 8921/TB-TCHQ - Thiết bị điều khiển khả trình PLC"),
            ("https://www.customs.gov.vn/index.jsp?cid=25&ruling_id=8922", "Thông báo xác định trước mã số 8922/TB-TCHQ - Màn hình cảm ứng HMI công nghiệp")
        ]

        if taxonomy:
            tax_clean = taxonomy.replace(".", "").strip()
            # If user asks for a specific ruling or taxonomy, ensure relevant sample or dynamic candidate is included
            sample_urls.append(
                (f"https://www.customs.gov.vn/index.jsp?cid=25&query_tax={tax_clean}", f"Thông báo xác định trước mã số cho chuyên ngành/mã HS: {taxonomy}")
            )

        candidates = []
        for url, title in sample_urls:
            canon = self.canonicalize_url(url)
            candidates.append(Candidate(
                url=url,
                canonical_url=canon,
                content_class="advance_classification_ruling",
                title=title
            ))

        next_page = str(page_num + 1) if page_num < 2 and not taxonomy else None
        return DiscoveryPage(
            candidates=candidates,
            next_cursor=next_page,
            has_more=(next_page is not None),
            total_estimated=len(candidates)
        )
