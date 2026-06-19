from docx import Document

from core.domain.docx_transform import export_raw_to_docx, parse_raw_from_docx


def _paragraphs_between_markers(docx_path, start_marker, end_marker):
    document = Document(str(docx_path))
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    start = paragraphs.index(start_marker)
    end = paragraphs.index(end_marker)
    return [text for text in paragraphs[start + 1:end] if text.strip()]


def test_export_raw_to_docx_writes_content_newlines_as_word_paragraphs(tmp_path):
    docx_path = tmp_path / "raw.docx"
    raw_data = {
        "source_name": "《测试书》",
        "video_titles": ["测试标题"],
        "cover_titles": ["测试封面"],
        "cover_subtitles": ["测试副标题"],
        "golden_quotes": ["测试金句。"],
        "content": "第一段内容。\n\n第二段内容。\n第三段内容。",
        "total_length": 22,
    }

    export_raw_to_docx(raw_data, str(docx_path))

    assert _paragraphs_between_markers(docx_path, "===CONTENT_START===", "===CONTENT_END===") == [
        "第一段内容。",
        "第二段内容。",
        "第三段内容。",
    ]


def test_parse_raw_from_docx_round_trips_content_paragraphs(tmp_path):
    docx_path = tmp_path / "raw.docx"
    raw_data = {
        "source_name": "《测试书》",
        "video_titles": ["测试标题"],
        "cover_titles": ["测试封面"],
        "cover_subtitles": ["测试副标题"],
        "golden_quotes": ["测试金句。"],
        "content": "第一段内容。\n第二段内容。\n第三段内容。",
        "total_length": 20,
    }

    export_raw_to_docx(raw_data, str(docx_path))
    parsed = parse_raw_from_docx(str(docx_path))

    assert parsed["content"] == "第一段内容。\n第二段内容。\n第三段内容。"
