"""Vietnam National Legal Database Adapter (VN_VBPL)."""

from typing import Optional
from service.adapters.base import HSESourceAdapter, CandidateItem, DiscoveryPage


class VNVbplAdapter:
    source_id = "VN_VBPL"

    def discover(self, cursor: Optional[str] = None, limit: int = 50) -> DiscoveryPage:
        items = [
            CandidateItem(
                item_id="DOC_72_2020_QH14",
                source_id=self.source_id,
                title="Luật Bảo vệ môi trường số 72/2020/QH14",
                source_url="https://vbpl.vn/pages/portal.aspx?ItemID=145321",
                canonical_url="https://vbpl.vn/pages/portal.aspx?ItemID=145321",
                content_class="national_legal_database",
                doc_number="72/2020/QH14",
                published_date="2020-11-17",
                raw_content="""LUẬT BẢO VỆ MÔI TRƯỜNG
Số: 72/2020/QH14

Chương IV: ĐÁNH GIÁ MÔI TRƯỜNG CHIẾN LƯỢC, ĐÁNH GIÁ TÁC ĐỘNG MÔI TRƯỜNG VÀ GIẤY PHÉP MÔI TRƯỜNG
Điều 39. Đối tượng phải có giấy phép môi trường
1. Dự án đầu tư nhóm I, nhóm II và nhóm III có phát sinh nước thải, bụi, khí thải xả ra môi trường phải được xử lý hoặc phát sinh chất thải nguy hại phải được quản lý theo quy định về quản lý chất thải khi đi vào vận hành chính thức.
2. Cơ sở sản xuất, kinh doanh, dịch vụ, khu sản xuất, kinh doanh, dịch vụ tập trung, cụm công nghiệp hoạt động trước ngày Luật này có hiệu lực thi hành có tiêu chí về môi trường như đối tượng quy định tại khoản 1 Điều này.

Điều 42. Nội dung giấy phép môi trường
1. Nội dung cấp phép môi trường gồm có:
a) Nguồn phát sinh nước thải; lưu lượng xả nước thải tối đa; dòng nước thải; các chất ô nhiễm và giá trị giới hạn của các chất ô nhiễm theo dòng nước thải; vị trí, phương thức xả nước thải và nguồn tiếp nhận nước thải;
b) Nguồn phát sinh khí thải; lưu lượng xả khí thải tối đa; dòng khí thải; các chất ô nhiễm và giá trị giới hạn của các chất ô nhiễm theo dòng khí thải; vị trí, phương thức xả khí thải;
c) Nguồn phát sinh và giá trị giới hạn đối với tiếng ồn, độ rung;
d) Công trình, hệ thống thiết bị xử lý chất thải nguy hại; mã chất thải nguy hại và khối lượng được phép xử lý, số lượng trạm trung chuyển chất thải nguy hại, địa bàn hoạt động đối với dự án đầu tư, cơ sở thực hiện dịch vụ xử lý chất thải nguy hại cấp tỉnh;
đ) Loại, khối lượng phế liệu được phép nhập khẩu từ nước ngoài làm nguyên liệu sản xuất đối với dự án đầu tư, cơ sở có nhập khẩu phế liệu từ nước ngoài làm nguyên liệu sản xuất."""
            ),
            CandidateItem(
                item_id="DOC_08_2022_ND_CP",
                source_id=self.source_id,
                title="Nghị định 08/2022/NĐ-CP quy định chi tiết một số điều của Luật Bảo vệ môi trường",
                source_url="https://vbpl.vn/pages/portal.aspx?ItemID=151892",
                canonical_url="https://vbpl.vn/pages/portal.aspx?ItemID=151892",
                content_class="consolidated_document",
                doc_number="08/2022/ND-CP",
                published_date="2022-01-10",
                raw_content="""NGHỊ ĐỊNH 08/2022/NĐ-CP
Quy định chi tiết thi hành Luật Bảo vệ môi trường

Chương VI: QUẢN LÝ CHẤT THẢI VÀ KIỂM SOÁT CÁC CHẤT Ô NHIỄM KHÁC
Mục 1: QUẢN LÝ CHẤT THẢI NGUY HẠI
Điều 71. Trách nhiệm của chủ nguồn thải chất thải nguy hại
1. Khai báo khối lượng, loại chất thải nguy hại trong hồ sơ đề nghị cấp giấy phép môi trường hoặc đăng ký môi trường.
2. Thực hiện phân định, phân loại, thu gom, lưu giữ riêng và không để lẫn với chất thải không nguy hại, bảo đảm không gây ô nhiễm môi trường.
3. Tự tái sử dụng, tái chế, xử lý, đồng xử lý, thu hồi năng lượng theo quy định hoặc ký hợp đồng chuyển giao chất thải nguy hại cho cơ sở có giấy phép môi trường phù hợp."""
            )
        ]
        return DiscoveryPage(items=items, next_cursor=None, has_more=False)

    def fetch_item(self, candidate: CandidateItem) -> CandidateItem:
        return candidate
