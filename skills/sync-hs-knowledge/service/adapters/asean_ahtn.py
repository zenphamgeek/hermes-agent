"""ASEAN Harmonised Tariff Nomenclature Adapter (asean.org)."""

from typing import Optional, List
from .base import SourceAdapter, Candidate, DiscoveryPage


class ASEANAHTNAdapter(SourceAdapter):
    source_id = "ASEAN_AHTN"
    name = "ASEAN Harmonised Tariff Nomenclature"
    jurisdiction = "ASEAN"

    def discover(self, cursor: Optional[str] = None, limit: int = 50, taxonomy: Optional[str] = None) -> DiscoveryPage:
        page_num = int(cursor) if cursor and cursor.isdigit() else 1

        sample_urls = [
            ("https://asean.org/annex-2-tariff-schedules/atiga-ahtn-2022.pdf", "ASEAN AHTN 2022 Nomenclature Schedule"),
            ("https://asean.org/annex-2-tariff-schedules/correlation-table.xlsx", "AHTN 2017 - 2022 Correlation Table")
        ]

        candidates = []
        for url, title in sample_urls:
            canon = self.canonicalize_url(url)
            candidates.append(Candidate(
                url=url,
                canonical_url=canon,
                content_class="ahtn_nomenclature",
                title=title
            ))

        next_page = str(page_num + 1) if page_num < 2 else None
        return DiscoveryPage(
            candidates=candidates,
            next_cursor=next_page,
            has_more=(next_page is not None),
            total_estimated=len(candidates)
        )
