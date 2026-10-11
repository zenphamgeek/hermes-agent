"""Tests for HTML and 16-Section SDS Document Parsers."""

from service.parsers.html_parser import HTMLDocumentParser
from service.parsers.sds_parser import SDSDocumentParser


def test_html_legal_parser():
    raw_html = """
    <html><head><title>Nghị định 44/2016/NĐ-CP</title></head>
    <body>
        <h1>Nghị định 44/2016/NĐ-CP</h1>
        <p>Số: 44/2016/NĐ-CP</p>
        <div>
            <h2>Điều 14. Đối tượng huấn luyện</h2>
            <p>1. Nhóm 1: Người đứng đầu đơn vị.</p>
            <p>2. Nhóm 2: Người làm công tác ATVSLĐ.</p>
        </div>
    </body></html>
    """
    parser = HTMLDocumentParser()
    res = parser.parse(raw_html.encode("utf-8"))
    assert res.doc_number == "44/2016/NĐ-CP"
    assert len(res.sections) > 0
    assert res.sections[0].code == "DIEU_14"


def test_sds_16_section_parser():
    sample_sds = """
    PHIẾU AN TOÀN HÓA CHẤT (SDS)
    1. Nhận dạng: Dung môi Toluen
    2. Nhận dạng đặc tính nguy hiểm: Chất lỏng dễ cháy Cấp 2. H225, H361d. P210, P280.
    3. Thành phần: Toluene (CAS: 108-88-3) 99%.
    4. Biện pháp sơ cứu: Di chuyển nạn nhân ra nơi thoáng khí.
    5. Biện pháp chữa cháy: Dùng bọt foam, CO2.
    6. Biện pháp phòng ngừa: Cách ly nguồn lửa.
    7. Sử dụng và bảo quản: Bảo quản kín dưới 30°C.
    8. Kiểm soát phơi nhiễm: TWA = 100 mg/m3.
    9. Đặc tính lý hóa: Điểm chớp cháy: 4.4°C.
    10. Tính ổn định và độ phản ứng: Không phản ứng ở điều kiện thường.
    11. Thông tin độc học: Nguy hiểm cho sinh sản.
    12. Thông tin sinh thái: Độc hại cho sinh vật thủy sinh.
    13. Biện pháp tiêu hủy: Đốt có thu hồi nhiệt.
    14. Thông tin vận chuyển: UN 1294.
    15. Thông tin pháp luật: Luật Hóa chất 69/2025/QH15.
    16. Thông tin khác: Bản sửa đổi lần 3.
    """
    parser = SDSDocumentParser()
    res = parser.parse(sample_sds.encode("utf-8"))
    assert res.completeness_score == 1.0
    assert "108-88-3" in res.cas_numbers
    assert res.un_number == "UN 1294"
    assert res.flash_point_c == 4.4
    assert "H225" in res.ghs_h_statements
