"""Vietnam Chemicals Agency & Safety Adapter (VN_CHEMICALS)."""

from typing import Optional
from service.adapters.base import HSESourceAdapter, CandidateItem, DiscoveryPage


class VNChemicalsAdapter:
    source_id = "VN_CHEMICALS"

    def discover(self, cursor: Optional[str] = None, limit: int = 50) -> DiscoveryPage:
        items = [
            CandidateItem(
                item_id="DOC_69_2025_QH15",
                source_id=self.source_id,
                title="Luật Hóa chất số 69/2025/QH15",
                source_url="http://cuchoachat.gov.vn/vanban/luathoachat692025qh15",
                canonical_url="http://cuchoachat.gov.vn/vanban/luathoachat692025qh15",
                content_class="chemical_law",
                doc_number="69/2025/QH15",
                published_date="2025-06-20",
                raw_content="""LUẬT HÓA CHẤT
Số: 69/2025/QH15 (Có hiệu lực từ 01/01/2026)

Chương II: AN TOÀN TRONG HOẠT ĐỘNG HÓA CHẤT
Điều 15. Phân loại hóa chất và Phiếu an toàn hóa chất (SDS)
1. Tổ chức, cá nhân sản xuất, nhập khẩu hóa chất nguy hiểm phải phân loại hóa chất theo Hệ thống hài hòa toàn cầu về phân loại và ghi nhãn hóa chất (GHS) và lập Phiếu an toàn hóa chất bằng tiếng Việt.
2. Phiếu an toàn hóa chất phải bao gồm đầy đủ 16 mục theo quy định.

Điều 20. Kế hoạch và Biện pháp phòng ngừa, ứng phó sự cố hóa chất
1. Chủ cơ sở hoạt động hóa chất thuộc Danh mục hóa chất nguy hiểm phải xây dựng Kế hoạch phòng ngừa, ứng phó sự cố hóa chất trình cơ quan có thẩm quyền phê duyệt trước khi đưa dự án vào hoạt động.
2. Cơ sở tồn trữ hóa chất dễ cháy, nổ với khối lượng từ 1.000 kg trở lên phải thiết lập hệ thống phát hiện rò rỉ và phương tiện chữa cháy chuyên dùng."""
            ),
            CandidateItem(
                item_id="DOC_ND_24_2026_ND_CP",
                source_id=self.source_id,
                title="Nghị định 24/2026/NĐ-CP ban hành Danh mục hóa chất nguy hiểm, hóa chất phải khai báo và hóa chất kiểm soát đặc biệt",
                source_url="http://cuchoachat.gov.vn/vanban/nd242026ndcp",
                canonical_url="http://cuchoachat.gov.vn/vanban/nd242026ndcp",
                content_class="controlled_chemicals_list",
                doc_number="24/2026/ND-CP",
                published_date="2026-02-15",
                raw_content="""NGHỊ ĐỊNH 24/2026/NĐ-CP
Danh mục hóa chất nguy hiểm và hóa chất kiểm soát đặc biệt

Phụ lục I: DANH MỤC HÓA CHẤT NGUY HIỂM PHẢI KHAI BÁO
1. Axeton (Acetone) - CAS: 67-64-1 - Phân loại GHS: Chất lỏng dễ cháy Cấp 2 (H225), Kích ứng mắt Cấp 2 (H319).
2. Toluen (Toluene) - CAS: 108-88-3 - Phân loại GHS: Chất lỏng dễ cháy Cấp 2 (H225), Độc tính sinh sản Cấp 2 (H361d).
3. Axit Sunfuric (Sulfuric acid) - CAS: 7664-93-9 - Phân loại GHS: Ăn mòn da Cấp 1A (H314)."""
            )
        ]
        return DiscoveryPage(items=items, next_cursor=None, has_more=False)

    def fetch_item(self, candidate: CandidateItem) -> CandidateItem:
        return candidate
