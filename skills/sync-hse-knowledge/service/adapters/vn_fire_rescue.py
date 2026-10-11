"""Vietnam Fire Safety & Rescue Police Department Adapter (VN_FIRE_RESCUE)."""

from typing import Optional
from service.adapters.base import HSESourceAdapter, CandidateItem, DiscoveryPage


class VNFireRescueAdapter:
    source_id = "VN_FIRE_RESCUE"

    def discover(self, cursor: Optional[str] = None, limit: int = 50) -> DiscoveryPage:
        items = [
            CandidateItem(
                item_id="DOC_55_2024_QH15",
                source_id=self.source_id,
                title="Luật Phòng cháy, chữa cháy và cứu nạn, cứu hộ số 55/2024/QH15",
                source_url="http://canhsatpccc.gov.vn/vanban/luatpccc552024qh15",
                canonical_url="http://canhsatpccc.gov.vn/vanban/luatpccc552024qh15",
                content_class="fire_safety_law",
                doc_number="55/2024/QH15",
                published_date="2024-11-20",
                raw_content="""LUẬT PHÒNG CHÁY, CHỮA CHÁY VÀ CỨU NẠN, CỨU HỘ
Số: 55/2024/QH15 (Có hiệu lực từ 01/07/2025)

Chương II: PHÒNG CHÁY VÀ CỨU NẠN, CỨU HỘ
Điều 12. Trách nhiệm phòng cháy của người đứng đầu cơ sở
1. Thành lập, duy trì hoạt động của đội phòng cháy và chữa cháy cơ sở hoặc đội phòng cháy và chữa cháy chuyên ngành.
2. Xây dựng, phê duyệt phương án chữa cháy, cứu nạn cứu hộ và tổ chức thực tập phương án ít nhất 01 lần trong một năm.
3. Trang bị đầy đủ phương tiện phòng cháy, chữa cháy và cứu nạn, cứu hộ theo quy định tại tiêu chuẩn, quy chuẩn kỹ thuật."""
            ),
            CandidateItem(
                item_id="DOC_ND_105_2025_ND_CP",
                source_id=self.source_id,
                title="Nghị định 105/2025/NĐ-CP hướng dẫn thi hành Luật Phòng cháy, chữa cháy và cứu nạn, cứu hộ",
                source_url="http://canhsatpccc.gov.vn/vanban/nd1052025ndcp",
                canonical_url="http://canhsatpccc.gov.vn/vanban/nd1052025ndcp",
                content_class="fire_prevention_standard",
                doc_number="105/2025/ND-CP",
                published_date="2025-05-15",
                raw_content="""NGHỊ ĐỊNH 105/2025/NĐ-CP
Hướng dẫn Luật Phòng cháy, chữa cháy và cứu nạn, cứu hộ

Điều 8. Kiểm tra an toàn phòng cháy, chữa cháy và cứu nạn, cứu hộ
1. Người đứng đầu cơ sở phải tự tổ chức kiểm tra an toàn PCCC thường xuyên và định kỳ 06 tháng một lần.
2. Cơ quan Công an thực hiện kiểm tra định kỳ đối với cơ sở có nguy hiểm cháy, nổ cao 01 năm một lần."""
            )
        ]
        return DiscoveryPage(items=items, next_cursor=None, has_more=False)

    def fetch_item(self, candidate: CandidateItem) -> CandidateItem:
        return candidate
