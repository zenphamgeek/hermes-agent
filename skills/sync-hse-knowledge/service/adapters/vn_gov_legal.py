"""Vietnam Government & National Gazette Adapter (VN_GOV_LEGAL)."""

from typing import Optional, List
from service.adapters.base import HSESourceAdapter, CandidateItem, DiscoveryPage


class VNGovLegalAdapter:
    source_id = "VN_GOV_LEGAL"

    def discover(self, cursor: Optional[str] = None, limit: int = 50) -> DiscoveryPage:
        # P0 Golden fixtures for Vietnam Core HSE Legislation
        items = [
            CandidateItem(
                item_id="DOC_84_2015_QH13",
                source_id=self.source_id,
                title="Luật An toàn, vệ sinh lao động số 84/2015/QH13",
                source_url="https://vanban.chinhphu.vn/?docid=180606&pageid=27160",
                canonical_url="https://vanban.chinhphu.vn/?docid=180606&pageid=27160",
                content_class="legal_document",
                doc_number="84/2015/QH13",
                published_date="2015-06-25",
                raw_content="""LUẬT AN TOÀN, VỆ SINH LAO ĐỘNG
Số: 84/2015/QH13

Chương I: QUY ĐỊNH CHUNG
Điều 1. Phạm vi điều chỉnh
Luật này quy định việc bảo đảm an toàn, vệ sinh lao động; chính sách, chế độ đối với người bị tai nạn lao động, bệnh nghề nghiệp...

Điều 15. Kiểm định máy, thiết bị, vật tư có yêu cầu nghiêm ngặt về an toàn lao động
1. Các loại máy, thiết bị, vật tư có yêu cầu nghiêm ngặt về an toàn lao động phải được kiểm định kỹ thuật an toàn trước khi đưa vào sử dụng và kiểm định định kỳ trong quá trình sử dụng.
2. Tổ chức hoạt động kiểm định kỹ thuật an toàn lao động phải đáp ứng các điều kiện theo quy định của Chính phủ."""
            ),
            CandidateItem(
                item_id="DOC_44_2016_ND_CP",
                source_id=self.source_id,
                title="Nghị định 44/2016/NĐ-CP quy định chi tiết một số điều của Luật an toàn, vệ sinh lao động về hoạt động kiểm định kỹ thuật an toàn lao động, huấn luyện an toàn, vệ sinh lao động và quan trắc môi trường lao động",
                source_url="https://vanban.chinhphu.vn/default.aspx?docid=185117&pageid=27160",
                canonical_url="https://vanban.chinhphu.vn/default.aspx?docid=185117&pageid=27160",
                content_class="national_decree",
                doc_number="44/2016/ND-CP",
                published_date="2016-05-15",
                raw_content="""NGHỊ ĐỊNH 44/2016/NĐ-CP
Quy định chi tiết về kiểm định an toàn, huấn luyện ATVSLĐ và quan trắc môi trường lao động

Chương III: HUẤN LUYỆN AN TOÀN, VỆ SINH LAO ĐỘNG
Điều 14. Đối tượng tham dự khóa huấn luyện an toàn, vệ sinh lao động
1. Nhóm 1: Người đứng đầu đơn vị, cơ sở sản xuất, kinh doanh và phòng, ban, chi nhánh trực thuộc.
2. Nhóm 2: Người làm công tác an toàn, vệ sinh lao động.
3. Nhóm 3: Người lao động làm công việc có yêu cầu nghiêm ngặt về an toàn, vệ sinh lao động.
4. Nhóm 4: Người lao động không thuộc các nhóm 1, 2, 3, 5, 6.
5. Nhóm 5: Người làm công tác y tế.
6. Nhóm 6: An toàn, vệ sinh viên.

Điều 18. Thời gian huấn luyện lần đầu
1. Huấn luyện Nhóm 1, Nhóm 4: Ít nhất 16 giờ.
2. Huấn luyện Nhóm 2: Ít nhất 48 giờ.
3. Huấn luyện Nhóm 3: Ít nhất 24 giờ.
4. Huấn luyện Nhóm 5: Ít nhất 56 giờ.
5. Huấn luyện Nhóm 6: Ít nhất 4 giờ ngoài thời gian huấn luyện của nhóm 4."""
            )
        ]
        return DiscoveryPage(items=items, next_cursor=None, has_more=False)

    def fetch_item(self, candidate: CandidateItem) -> CandidateItem:
        return candidate
