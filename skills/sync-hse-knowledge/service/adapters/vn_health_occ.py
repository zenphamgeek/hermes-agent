"""Vietnam Ministry of Health Occupational Hygiene Adapter (VN_HEALTH_OCC)."""

from typing import Optional
from service.adapters.base import HSESourceAdapter, CandidateItem, DiscoveryPage


class VNHealthOccAdapter:
    source_id = "VN_HEALTH_OCC"

    def discover(self, cursor: Optional[str] = None, limit: int = 50) -> DiscoveryPage:
        items = [
            CandidateItem(
                item_id="DOC_TT_19_2016_BYT",
                source_id=self.source_id,
                title="Thông tư 19/2016/TT-BYT hướng dẫn quản lý vệ sinh lao động và sức khỏe người lao động",
                source_url="https://moh.gov.vn/vanban/tt192016byt",
                canonical_url="https://moh.gov.vn/vanban/tt192016byt",
                content_class="occupational_hygiene",
                doc_number="19/2016/TT-BYT",
                published_date="2016-06-30",
                raw_content="""THÔNG TƯ 19/2016/TT-BYT
Hướng dẫn quản lý vệ sinh lao động và sức khỏe người lao động

Điều 5. Quan trắc môi trường lao động
1. Cơ sở lao động phải tổ chức thực hiện quan trắc môi trường lao động để đánh giá các yếu tố có hại ít nhất 01 lần trong một năm.
2. Đơn vị thực hiện quan trắc môi trường lao động phải đáp ứng đủ điều kiện theo quy định tại Nghị định số 44/2016/NĐ-CP.

Điều 7. Khám sức khỏe định kỳ và khám phát hiện bệnh nghề nghiệp
1. Hằng năm, người sử dụng lao động phải tổ chức khám sức khỏe định kỳ cho người lao động, kể cả người học nghề, tập nghề.
2. Người lao động làm công việc nặng nhọc, độc hại, nguy hiểm hoặc đặc biệt nặng nhọc, độc hại, nguy hiểm phải được khám sức khỏe ít nhất 06 tháng một lần."""
            )
        ]
        return DiscoveryPage(items=items, next_cursor=None, has_more=False)

    def fetch_item(self, candidate: CandidateItem) -> CandidateItem:
        return candidate
