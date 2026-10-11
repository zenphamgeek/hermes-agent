"""OCR trigger and hook (FR-043)."""

from typing import Optional

def is_ocr_needed(char_count: int, page_count: int, threshold_per_page: int = 50) -> bool:
    """Evaluates if a document page has abnormally low text density and needs OCR."""
    if page_count == 0:
        return False
    return (char_count / page_count) < threshold_per_page
