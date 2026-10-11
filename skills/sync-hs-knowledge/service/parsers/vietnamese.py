"""Vietnamese text normalization and lexical token generator (FR-047)."""

import re
import unicodedata

# Mapping for removing Vietnamese diacritics for search indexing
VIETNAMESE_ACCENTS = {
    'a': 'aàảãáạăằẳẵắặâầẩẫấậ',
    'A': 'AÀẢÃÁẠĂẰẲẴẮẶÂẦẨẪẤẬ',
    'd': 'dđ',
    'D': 'DĐ',
    'e': 'eèẻẽéẹêềểễếệ',
    'E': 'EÈẺẼÉẸÊỀỂỄẾỆ',
    'i': 'iìỉĩíị',
    'I': 'IÌỈĨÍỊ',
    'o': 'oòỏõóọôồổỗốộơờởỡớợ',
    'O': 'OÒỎÕÓỌÔỒỔỖỐỘƠỜỞỠỚỢ',
    'u': 'uùủũúụưừửữứự',
    'U': 'UÙỦŨÚỤƯỪỬỮỨỰ',
    'y': 'yỳỷỹýỵ',
    'Y': 'YỲỶỸÝỴ'
}

_CHAR_MAP = {}
for base_char, accented_chars in VIETNAMESE_ACCENTS.items():
    for char in accented_chars:
        _CHAR_MAP[char] = base_char


def normalize_vietnamese_text(text: str) -> str:
    """Normalizes string to Unicode NFC without losing accents."""
    if not text:
        return ""
    return unicodedata.normalize("NFC", text.strip())


def remove_vietnamese_diacritics(text: str) -> str:
    """Strips tone marks for fuzzy/unaccented search match."""
    normalized = unicodedata.normalize("NFC", text)
    result = []
    for ch in normalized:
        result.append(_CHAR_MAP.get(ch, ch))
    return "".join(result)


def generate_search_tokens(text: str) -> str:
    """Generates dual search tokens: original NFC + diacritic-stripped."""
    if not text:
        return ""
    nfc_text = normalize_vietnamese_text(text)
    stripped = remove_vietnamese_diacritics(nfc_text).lower()
    clean_nfc = nfc_text.lower()
    # Return combined searchable tokens
    return f"{clean_nfc} {stripped}"
