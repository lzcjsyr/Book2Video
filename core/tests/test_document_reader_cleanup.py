import os
import sys
from types import SimpleNamespace

from core.domain.reader import DocumentReader


def test_mobi_extraction_cleans_temporary_files_after_failure(monkeypatch):
    captured = {}

    def fail_extract(path):
        captured["path"] = path
        raise RuntimeError("broken mobi")

    monkeypatch.setitem(sys.modules, "mobi", SimpleNamespace(extract=fail_extract))

    result = DocumentReader()._extract_mobi_text(
        "这是一段足够长的中文内容，用于回退提取。".encode()
    )

    assert result
    assert not os.path.exists(captured["path"])


def test_mobi_extraction_cleans_extracted_directory(monkeypatch, tmp_path):
    extracted_dir = tmp_path / "extracted"
    extracted_dir.mkdir()
    (extracted_dir / "book.html").write_text("<p>有效内容</p>", encoding="utf-8")

    monkeypatch.setitem(
        sys.modules,
        "mobi",
        SimpleNamespace(
            extract=lambda _path: (str(extracted_dir), str(extracted_dir / "book.html"))
        ),
    )

    assert DocumentReader()._extract_mobi_text(b"mobi") == "有效内容"
    assert not extracted_dir.exists()
