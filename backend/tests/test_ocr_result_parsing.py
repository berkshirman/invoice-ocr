import numpy as np

from app.services.ocr_service import OCRService


def _v3_result() -> list[dict]:
    return [
        {
            "rec_texts": [
                "发票号码：25952000000233223073",
                "开票日期：2025年11月05日",
            ],
            "rec_scores": [0.98, 0.95],
            "rec_polys": [
                np.array(
                    [[10, 40], [310, 40], [310, 56], [10, 56]],
                    dtype=np.float32,
                ),
                np.array(
                    [[10, 20], [210, 20], [210, 36], [10, 36]],
                    dtype=np.float32,
                ),
            ],
        }
    ]


def test_extract_text_from_paddleocr_v3_result():
    service = OCRService()

    texts, confidences, lines = service._extract_text_from_result(_v3_result())

    assert texts == [
        "发票号码：25952000000233223073",
        "开票日期：2025年11月05日",
    ]
    assert confidences == [98.0, 95.0]
    assert lines[0]["bbox"] == [
        [10.0, 40.0],
        [310.0, 40.0],
        [310.0, 56.0],
        [10.0, 56.0],
    ]
    assert lines[0]["min_x"] == 10.0
    assert lines[0]["max_x"] == 310.0
    assert lines[0]["min_y"] == 40.0
    assert lines[0]["max_y"] == 56.0
    assert lines[0]["center_x"] == 160.0
    assert lines[0]["center_y"] == 48.0


def test_extract_text_from_v3_result_sorts_by_position():
    service = OCRService()
    _, _, lines = service._extract_text_from_result(_v3_result())

    sorted_lines = service._sort_lines_by_position(lines)

    assert [line["text"] for line in sorted_lines] == [
        "开票日期：2025年11月05日",
        "发票号码：25952000000233223073",
    ]


def test_extract_text_from_empty_v3_result():
    service = OCRService()

    assert service._extract_text_from_result([]) == ([], [], [])
    assert service._extract_text_from_result(
        [{"rec_texts": [], "rec_scores": [], "rec_polys": []}]
    ) == ([], [], [])
