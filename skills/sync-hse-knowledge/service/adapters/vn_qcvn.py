"""Vietnam National Technical Regulations (QCVN) Adapter (VN_QCVN)."""

from typing import Optional
from service.adapters.base import HSESourceAdapter, CandidateItem, DiscoveryPage


class VNQcvnAdapter:
    source_id = "VN_QCVN"

    def discover(self, cursor: Optional[str] = None, limit: int = 50) -> DiscoveryPage:
        items = [
            CandidateItem(
                item_id="DOC_QCVN_05_2023_BTNMT",
                source_id=self.source_id,
                title="QCVN 05:2023/BTNMT - Quy chuẩn kỹ thuật quốc gia về chất lượng không khí",
                source_url="https://tcvn.gov.vn/qcvn052023btnmt",
                canonical_url="https://tcvn.gov.vn/qcvn052023btnmt",
                content_class="mandatory_qcvn",
                doc_number="QCVN 05:2023/BTNMT",
                published_date="2023-03-01",
                raw_content="""QUY CHUẨN KỸ THUẬT QUỐC GIA VỀ CHẤT LƯỢNG KHÔNG KHÍ
Ký hiệu: QCVN 05:2023/BTNMT

Bảng 1: Giá trị giới hạn các thông số cơ bản trong không khí xung quanh
1. Tổng bụi lơ lửng (TSP): Trung bình 1 giờ: 300 µg/m3; Trung bình 24 giờ: 200 µg/m3; Trung bình năm: 100 µg/m3.
2. Bụi mịn PM10: Trung bình 24 giờ: 100 µg/m3; Trung bình năm: 50 µg/m3.
3. Bụi mịn PM2.5: Trung bình 24 giờ: 50 µg/m3; Trung bình năm: 25 µg/m3.
4. Sunfua đioxit (SO2): Trung bình 1 giờ: 350 µg/m3; Trung bình 24 giờ: 125 µg/m3.
5. Nitơ đioxit (NO2): Trung bình 1 giờ: 200 µg/m3; Trung bình 24 giờ: 100 µg/m3.
6. Cacbon monoxit (CO): Trung bình 1 giờ: 30.000 µg/m3; Trung bình 8 giờ: 10.000 µg/m3."""
            ),
            CandidateItem(
                item_id="DOC_QCVN_40_2011_BTNMT",
                source_id=self.source_id,
                title="QCVN 40:2011/BTNMT - Quy chuẩn kỹ thuật quốc gia về nước thải công nghiệp",
                source_url="https://tcvn.gov.vn/qcvn402011btnmt",
                canonical_url="https://tcvn.gov.vn/qcvn402011btnmt",
                content_class="emission_discharge_limits",
                doc_number="QCVN 40:2011/BTNMT",
                published_date="2011-12-15",
                raw_content="""QUY CHUẨN KỸ THUẬT QUỐC GIA VỀ NƯỚC THẢI CÔNG NGHIỆP
Ký hiệu: QCVN 40:2011/BTNMT

Bảng 1: Giá trị giới hạn các thông số ô nhiễm trong nước thải công nghiệp
1. pH: Cột A: 6-9; Cột B: 5.5-9
2. BOD5 (20°C): Cột A: 30 mg/L; Cột B: 50 mg/L
3. COD: Cột A: 75 mg/L; Cột B: 150 mg/L
4. Tổng chất rắn lơ lửng (TSS): Cột A: 50 mg/L; Cột B: 100 mg/L
5. Amoni (tính theo N): Cột A: 5 mg/L; Cột B: 10 mg/L
6. Tổng Nitơ: Cột A: 20 mg/L; Cột B: 40 mg/L
7. Tổng Photpho: Cột A: 4 mg/L; Cột B: 6 mg/L
8. Kim loại nặng Tổng Crom: Cột A: 0.5 mg/L; Cột B: 1.0 mg/L"""
            ),
            CandidateItem(
                item_id="DOC_QCVN_03_2019_BYT",
                source_id=self.source_id,
                title="QCVN 03:2019/BYT - Quy chuẩn kỹ thuật quốc gia về giá trị giới hạn tiếp xúc cho phép của 50 yếu tố hóa học tại nơi làm việc",
                source_url="https://tcvn.gov.vn/qcvn032019byt",
                canonical_url="https://tcvn.gov.vn/qcvn032019byt",
                content_class="occupational_exposure_limits",
                doc_number="QCVN 03:2019/BYT",
                published_date="2019-06-10",
                raw_content="""QUY CHUẨN KỸ THUẬT QUỐC GIA VỀ GIÁ TRỊ GIỚI HẠN TIẾP XÚC CHO PHÉP 50 YẾU TỐ HÓA HỌC TẠI NƠI LÀM VIỆC
Ký hiệu: QCVN 03:2019/BYT

Bảng 1: Giá trị giới hạn tiếp xúc cho phép hóa chất tại nơi làm việc
1. Axeton (CAS 67-64-1): TWA = 500 mg/m3; STEL = 1000 mg/m3.
2. Toluen (CAS 108-88-3): TWA = 100 mg/m3; STEL = 300 mg/m3.
3. Axit Sunfuric (CAS 7664-93-9): TWA = 1 mg/m3; STEL = 3 mg/m3.
4. Benzen (CAS 71-43-2): TWA = 5 mg/m3; STEL = 10 mg/m3."""
            )
        ]
        return DiscoveryPage(items=items, next_cursor=None, has_more=False)

    def fetch_item(self, candidate: CandidateItem) -> CandidateItem:
        return candidate
