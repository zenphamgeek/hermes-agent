"""Test entity normalization (Legal, HS hierarchy, Tariff, Rulings) (FR-050 - FR-084)."""

import pytest
from datetime import date
from service.normalization.hs_tree import HSTreeNormalizer, NormalizedHSNode
from service.normalization.legal_doc import LegalDocNormalizer
from service.normalization.tariff_rules import TariffNormalizer
from service.normalization.rulings import RulingNormalizer


def test_hs_tree_code_cleaning_and_formatting():
    assert HSTreeNormalizer.clean_code(" 84.71.30.20 ") == "84713020"
    assert HSTreeNormalizer.format_code("84") == "84"
    assert HSTreeNormalizer.format_code("8471") == "8471"
    assert HSTreeNormalizer.format_code("847130") == "8471.30"
    assert HSTreeNormalizer.format_code("84713020") == "8471.30.20"


def test_hs_tree_level_and_parent():
    lvl, parent = HSTreeNormalizer.infer_level_and_parent("8471.30.20")
    assert lvl == 4
    assert parent == "8471.30"

    lvl3, p3 = HSTreeNormalizer.infer_level_and_parent("8471.30")
    assert lvl3 == 3
    assert p3 == "8471"


def test_hs_tree_parent_child_validation():
    valid_nodes = [
        NormalizedHSNode(code="84", level=1, parent_code=None, description_vi="Cơ khí"),
        NormalizedHSNode(code="8471", level=2, parent_code="84", description_vi="Máy tính"),
        NormalizedHSNode(code="8471.30", level=3, parent_code="8471", description_vi="Laptop")
    ]
    issues = HSTreeNormalizer.validate_parent_child(valid_nodes)
    assert len(issues) == 0

    invalid_nodes = [
        NormalizedHSNode(code="8471.30", level=3, parent_code="9999", description_vi="Orphan Laptop")
    ]
    issues_bad = HSTreeNormalizer.validate_parent_child(invalid_nodes)
    assert len(issues_bad) == 1
    assert issues_bad[0].issue_type == "MISSING_PARENT"


def test_tariff_rate_parsing():
    t, val, unit, cond = TariffNormalizer.parse_rate_string("5%")
    assert t == "ad_valorem"
    assert val == 5.0
    assert unit == "%"

    t2, val2, unit2, cond2 = TariffNormalizer.parse_rate_string("Miễn thuế")
    assert t2 == "conditional"
    assert "Miễn thuế" in cond2


def test_ruling_extraction():
    sample_text = """
    Tổng cục Hải quan thông báo:
    Số: 8921/TB-TCHQ
    ngày 15 tháng 08 năm 2026
    Tên thương mại: Bộ điều khiển lập trình PLC Siemens S7-1200
    mã số: 8537.10.19
    Căn cứ Thông tư 85/2026/TT-BTC.
    """
    ruling = RulingNormalizer.extract_ruling(sample_text, source_url="https://customs.gov.vn/ruling/8921")
    assert ruling is not None
    assert ruling.ruling_number == "8921/TB-TCHQ"
    assert ruling.ruling_date == date(2026, 8, 15)
    assert ruling.hs_code == "8537.10.19"
    assert "PLC Siemens" in ruling.product_declared_name
