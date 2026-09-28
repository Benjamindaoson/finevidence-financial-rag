from __future__ import annotations

import re


STRUCTURE_FIELDS = ("row_order", "column_alignment", "multi_level_header", "unit_preservation", "footnote_association", "cross_page_continuity", "caption_association", "multi_column_reading_order")


def structure_fidelity(text: str) -> dict[str, bool | str]:
    """Small parser-regression probe; it does not claim table reconstruction."""
    return {
        "row_order": bool(text.strip()),
        "column_alignment": "N/A: no structured table parser in B3 CPU slice",
        "multi_level_header": "N/A: no structured table parser in B3 CPU slice",
        "unit_preservation": bool(re.search(r"%|USD|HKD|GBP|million|billion|bn", text, re.I)),
        "footnote_association": "N/A: page parser does not expose footnote edges",
        "cross_page_continuity": "N/A: page parser emits independent page blocks",
        "caption_association": bool(re.search(r"table|figure|exhibit", text, re.I)),
        "multi_column_reading_order": "N/A: pypdf text order is not layout audited",
    }
