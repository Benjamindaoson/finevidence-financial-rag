from __future__ import annotations

from finevidence.evidence.pdf_table import words_to_rows


def test_pdf_words_reconstruct_label_and_numeric_columns() -> None:
    words = [
        {"text": "Revenue", "x0": 40, "x1": 80, "top": 20, "bottom": 30},
        {"text": "2025", "x0": 100, "x1": 120, "top": 10, "bottom": 20},
        {"text": "2024", "x0": 140, "x1": 160, "top": 10, "bottom": 20},
        {"text": "68,274", "x0": 100, "x1": 130, "top": 20, "bottom": 30},
        {"text": "65,854", "x0": 140, "x1": 170, "top": 20, "bottom": 30},
    ]
    rows, boxes = words_to_rows(words, anchors=[100, 140])
    assert rows == [["", "2025", "2024"], ["Revenue", "68,274", "65,854"]]
    assert boxes[1][0] == (40.0, 20.0, 80.0, 30.0)
    assert boxes[1][1] == (100.0, 20.0, 130.0, 30.0)
