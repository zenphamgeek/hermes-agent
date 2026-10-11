"""Vietnam Occupational Safety & Health Portal Adapter (VN_OSH_LEGAL)."""

from typing import Optional
from service.adapters.base import HSESourceAdapter, CandidateItem, DiscoveryPage


class VNOshLegalAdapter:
    source_id = "VN_OSH_LEGAL"

    def discover(self, cursor: Optional[str] = None, limit: int = 50) -> DiscoveryPage:
        items = [
            CandidateItem(
                item_id="DOC_TT_06_2020_BLDTBXH",
                source_id=self.source_id,
                title="Thông tư 06/2020/TT-BLĐTBXH ban hành Danh mục công việc có yêu cầu nghiêm ngặt về an toàn, vệ sinh lao động",
                source_url="http://antoanlaodong.gov.vn/vanban/tt062020bldtbxh",
                canonical_url="http://antoanlaodong.gov.vn/vanban/tt062020bldtbxh",
                content_class="strict_safety_equipment",
                doc_number="06/2020/TT-BLDTBXH",
                published_date="2020-08-20",
                raw_content="""THÔNG TƯ 06/2020/TT-BLĐTBXH
Danh mục công việc có yêu cầu nghiêm ngặt về an toàn, vệ sinh lao động

Điều 1. Danh mục công việc có yêu cầu nghiêm ngặt về ATVSLĐ
1. Chế tạo, lắp ráp, vận hành, bảo dưỡng, sửa chữa, tháo dỡ, kiểm tra, kiểm định kỹ thuật an toàn lao động các loại máy, thiết bị nâng, thang máy, thang cuốn.
2. Chế tạo, lắp ráp, vận hành, bảo dưỡng, sửa chữa, kiểm định nồi hơi, bình chịu áp lực, hệ thống đường ống dẫn khí nén, khí đốt.
3. Làm việc trong không gian hạn chế (hầm, bể chứa, giếng, đường ống, cống ngầm).
4. Làm việc trên cao cách mặt sàn, mặt đất từ 2 mét trở lên."""
            )
        ]
        return DiscoveryPage(items=items, next_cursor=None, has_more=False)

    def fetch_item(self, candidate: CandidateItem) -> CandidateItem:
        return candidate
