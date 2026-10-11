#!/usr/bin/env python3
"""Script to validate 16-section SDS files and detect conflicts."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from service.parsers.sds_parser import SDSDocumentParser

def main():
    sample_sds = """
    PHIẾU AN TOÀN HÓA CHẤT (SDS)
    Tên hóa chất: Dung môi Acetone Công nghiệp
    1. Nhận dạng: Acetone, Nhà cung ứng Hóa Chất VN.
    2. Nhận dạng đặc tính nguy hiểm: Chất lỏng dễ cháy Cấp 2. H225, H319. P210, P280.
    3. Thành phần: Acetone (CAS: 67-64-1) 99.5%.
    4. Biện pháp sơ cứu: Đưa nạn nhân ra nơi thoáng khí.
    5. Biện pháp chữa cháy: Dùng bột khô, bọt CO2.
    6. Biện pháp phòng ngừa: Cách ly nguồn nhiệt, thu gom bằng cát.
    7. Sử dụng và bảo quản: Bảo quản nơi khô ráo, thoáng mát dưới 30°C.
    8. Kiểm soát phơi nhiễm: TWA = 500 mg/m3. Đeo kính bảo hộ, găng tay cao su.
    9. Đặc tính lý hóa: Điểm chớp cháy: -18°C.
    10. Tính ổn định và độ phản ứng: Tránh tiếp xúc với chất oxy hóa mạnh.
    11. Thông tin độc học: Kích ứng da và mắt.
    12. Thông tin sinh thái: Độc hại đối với thủy sinh nếu nồng độ cao.
    13. Biện pháp tiêu hủy: Xử lý qua đơn vị xử lý chất thải nguy hại có giấy phép.
    14. Thông tin vận chuyển: UN 1090, Nhóm đóng gói II.
    15. Thông tin pháp luật: Tuân thủ Luật Hóa chất 69/2025/QH15.
    16. Thông tin khác: Ngày lập: 21/08/2026.
    """
    parser = SDSDocumentParser()
    res = parser.parse(sample_sds.encode("utf-8"))
    print(f"Product: {res.product_name}")
    print(f"Sections parsed: {len(res.sections)}/16 (Score: {res.completeness_score:.2f})")
    print(f"CAS Numbers: {res.cas_numbers} | UN: {res.un_number} | Flash point: {res.flash_point_c}°C")
    print(f"GHS: {res.ghs_signal_word} | H: {res.ghs_h_statements} | P: {res.ghs_p_statements}")
    
    if res.completeness_score >= 0.8:
        print("SUCCESS: SDS meets 16-section completeness threshold.")
        sys.exit(0)
    else:
        print("FAILED: Incomplete SDS.")
        sys.exit(6)

if __name__ == "__main__":
    main()
