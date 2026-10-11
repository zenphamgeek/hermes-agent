"""Vietnam Environmental Protection Adapter (VN_ENV_LEGAL)."""

from typing import Optional
from service.adapters.base import HSESourceAdapter, CandidateItem, DiscoveryPage


class VNEnvLegalAdapter:
    source_id = "VN_ENV_LEGAL"

    def discover(self, cursor: Optional[str] = None, limit: int = 50) -> DiscoveryPage:
        items = [
            CandidateItem(
                item_id="DOC_ND_05_2025_ND_CP",
                source_id=self.source_id,
                title="Nghị định 05/2025/NĐ-CP sửa đổi, bổ sung một số điều của Nghị định 08/2022/NĐ-CP hướng dẫn Luật Bảo vệ môi trường",
                source_url="https://monre.gov.vn/vanban/nd052025ndcp",
                canonical_url="https://monre.gov.vn/vanban/nd052025ndcp",
                content_class="environmental_law",
                doc_number="05/2025/ND-CP",
                published_date="2025-01-20",
                raw_content="""NGHỊ ĐỊNH 05/2025/NĐ-CP
Sửa đổi, bổ sung một số điều của Nghị định 08/2022/NĐ-CP

Điều 1. Sửa đổi, bổ sung quy định về quan trắc nước thải và khí thải tự động, liên tục
1. Cơ sở sản xuất có lưu lượng xả nước thải từ 500 m3/ngày (24 giờ) trở lên phải lắp đặt hệ thống quan trắc nước thải tự động, liên tục và truyền dữ liệu trực tiếp về Sở Tài nguyên và Môi trường.
2. Cơ sở có lưu lượng phát thải bụi, khí thải từ 50.000 m3/giờ trở lên phải lắp đặt hệ thống quan trắc khí thải tự động, liên tục."""
            )
        ]
        return DiscoveryPage(items=items, next_cursor=None, has_more=False)

    def fetch_item(self, candidate: CandidateItem) -> CandidateItem:
        return candidate
