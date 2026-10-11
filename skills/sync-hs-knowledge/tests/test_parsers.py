"""Test document parsers for HTML, Vietnamese normalization, and structure extraction (FR-040 - FR-047)."""

import pytest
from service.parsers.vietnamese import normalize_vietnamese_text, remove_vietnamese_diacritics, generate_search_tokens
from service.parsers.html_parser import HTMLDocumentParser


def test_vietnamese_normalization():
    raw_vn = "Thông tư 85/2026/TT-BTC quy định về phân loại hàng hóa xuất nhập khẩu"
    nfc = normalize_vietnamese_text(raw_vn)
    assert "Thông tư" in nfc

    stripped = remove_vietnamese_diacritics(raw_vn)
    assert "Thong tu" in stripped or "thong tu" in stripped.lower()

    tokens = generate_search_tokens("Bộ điều khiển PLC")
    assert "bộ điều khiển plc" in tokens
    assert "bo dieu khien plc" in tokens


def test_html_parser():
    sample_html = b"""
    <html>
    <head><title>Thong Tu 85/2026/TT-BTC</title></head>
    <body>
    <h1>Th\xc3\xb4ng t\xc6\xb0 s\xe1\xbb\x91 85/2026/TT-BTC</h1>
    <p>Ban h\xc3\xa0nh ng\xc3\xa0y 20 th\xc3\xa1ng 08 n\xc4\x83m 2026.</p>
    <table>
      <caption>Bi\xe1\xbb\x83u m\xe1\xba\xabu</caption>
      <tr><th>M\xc3\xa3 HS</th><th>T\xc3\xaan h\xc3\xa0ng</th></tr>
      <tr><td>8471.30.20</td><td>M\xc3\xa1y t\xc3\xadnh x\xc3\xa1ch tay</td></tr>
    </table>
    <a href="/files/thongtu85.pdf">T\xe1\xba\xa3i v\xe1\xbb\x81 PDF</a>
    </body>
    </html>
    """
    parser = HTMLDocumentParser()
    parsed = parser.parse(sample_html, "sha256_mock_123", "text/html")

    assert parsed.doc_number == "85/2026/TT-BTC"
    assert parsed.issuing_date == "2026-08-20"
    assert len(parsed.pages[0].tables) == 1
    assert len(parsed.attachments) == 1
    assert parsed.attachments[0]["url"] == "/files/thongtu85.pdf"
