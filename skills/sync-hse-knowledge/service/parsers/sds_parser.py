"""Safety Data Sheet (SDS) 16-Section Parser (FR-029, FR-060-067)."""

import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from service.parsers.base import ParsedDocumentResult, ParsedSection
from service.parsers.vietnamese import VietnameseLegalParser


SDS_16_SECTION_HEADERS = [
    (1, "Identification", [r"1\.\s*(nhận dạng|identification|product and company identification)", r"mục 1[:\.]"]),
    (2, "Hazard Identification", [r"2\.\s*(nhận dạng đặc tính nguy hiểm|hazard.*identification|nhận dạng nguy hiểm)", r"mục 2[:\.]"]),
    (3, "Composition", [r"3\.\s*(thông tin về thành phần|composition|ingredients|thành phần)", r"mục 3[:\.]"]),
    (4, "First-Aid Measures", [r"4\.\s*(biện pháp sơ cứu|first-aid measures|sơ cứu)", r"mục 4[:\.]"]),
    (5, "Fire-Fighting Measures", [r"5\.\s*(biện pháp chữa cháy|fire-fighting measures|chữa cháy)", r"mục 5[:\.]"]),
    (6, "Accidental Release Measures", [r"6\.\s*(biện pháp phòng ngừa|accidental release|phòng ngừa tràn đổ)", r"mục 6[:\.]"]),
    (7, "Handling and Storage", [r"7\.\s*(sử dụng và bảo quản|handling and storage|bảo quản)", r"mục 7[:\.]"]),
    (8, "Exposure Controls / PPE", [r"8\.\s*(kiểm soát phơi nhiễm|exposure controls|personal protection|trang thiết bị bảo hộ)", r"mục 8[:\.]"]),
    (9, "Physical and Chemical Properties", [r"9\.\s*(đặc tính lý hóa|physical and chemical properties|tính chất lý hóa)", r"mục 9[:\.]"]),
    (10, "Stability and Reactivity", [r"10\.\s*(tính ổn định và độ phản ứng|stability and reactivity|độ ổn định)", r"mục 10[:\.]"]),
    (11, "Toxicological Information", [r"11\.\s*(thông tin độc học|toxicological information|độc học)", r"mục 11[:\.]"]),
    (12, "Ecological Information", [r"12\.\s*(thông tin sinh thái|ecological information|sinh thái)", r"mục 12[:\.]"]),
    (13, "Disposal Considerations", [r"13\.\s*(biện pháp tiêu hủy|disposal considerations|thải bỏ)", r"mục 13[:\.]"]),
    (14, "Transport Information", [r"14\.\s*(thông tin vận chuyển|transport information|vận chuyển)", r"mục 14[:\.]"]),
    (15, "Regulatory Information", [r"15\.\s*(thông tin pháp luật|regulatory information|quy định pháp luật)", r"mục 15[:\.]"]),
    (16, "Other Information", [r"16\.\s*(thông tin khác|other information)", r"mục 16[:\.]"])
]


class ParsedSDSResult(BaseModel):
    product_name: str
    supplier_name: Optional[str] = None
    cas_numbers: List[str] = []
    un_number: Optional[str] = None
    flash_point_c: Optional[float] = None
    ghs_signal_word: Optional[str] = "DANGER"
    ghs_h_statements: List[str] = []
    ghs_p_statements: List[str] = []
    sections: Dict[int, str] = {}
    completeness_score: float = 1.0


class SDSDocumentParser:
    parser_name = "sds_parser"
    parser_version = "1.0.0"

    def parse(self, raw_bytes: bytes, mime_type: str = "text/plain") -> ParsedSDSResult:
        full_text = VietnameseLegalParser.normalize_text(raw_bytes.decode("utf-8", errors="replace"))

        sections_dict: Dict[int, str] = {}
        for sec_num, sec_title, patterns in SDS_16_SECTION_HEADERS:
            combined_pattern = "|".join(patterns)
            match = re.search(combined_pattern, full_text, re.IGNORECASE)
            if match:
                # Find start of section
                start_pos = match.start()
                # Find next section
                next_pos = len(full_text)
                for next_num, _, next_patterns in SDS_16_SECTION_HEADERS:
                    if next_num > sec_num:
                        n_match = re.search("|".join(next_patterns), full_text[start_pos + 20:], re.IGNORECASE)
                        if n_match:
                            next_pos = start_pos + 20 + n_match.start()
                            break
                sections_dict[sec_num] = full_text[start_pos:next_pos].strip()

        # Extract CAS numbers
        cas_matches = re.findall(r"\b\d{2,7}-\d{2}-\d\b", full_text)
        cas_numbers = list(set(cas_matches))

        # Extract UN numbers
        un_match = re.search(r"\bUN\s*(\d{4})\b", full_text, re.IGNORECASE)
        un_number = f"UN {un_match.group(1)}" if un_match else None

        # Extract Flash Point
        fp_match = re.search(r"(điểm chớp cháy|flash point)[:\s]*([-\d\.]+)\s*°?C", full_text, re.IGNORECASE)
        flash_point = float(fp_match.group(2)) if fp_match else None

        # Extract H-Statements & P-Statements
        h_statements = list(set(re.findall(r"\bH[234]\d{2}[a-z]?\b", full_text, re.IGNORECASE)))
        p_statements = list(set(re.findall(r"\bP[2345]\d{2}\b", full_text, re.IGNORECASE)))

        # Extract Product Name
        prod_name = "Chemical Product"
        name_match = re.search(r"(tên thương phẩm|product name|tên hóa chất)[:\s]*([^\n\r]+)", full_text, re.IGNORECASE)
        if name_match:
            prod_name = name_match.group(2).strip()

        completeness = len(sections_dict) / 16.0

        return ParsedSDSResult(
            product_name=prod_name,
            supplier_name="Chemical Supplier Co.",
            cas_numbers=cas_numbers,
            un_number=un_number,
            flash_point_c=flash_point,
            ghs_signal_word="DANGER" if "H225" in h_statements or "H314" in h_statements else "WARNING",
            ghs_h_statements=h_statements,
            ghs_p_statements=p_statements,
            sections=sections_dict,
            completeness_score=completeness
        )
