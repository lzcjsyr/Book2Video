from pathlib import Path

from cli.project_io import scan_input_files as scan_cli_input_files
from core.pipeline.scanner import scan_input_files as scan_pipeline_input_files


def test_input_scanners_include_agent_readable_text_and_office_formats(tmp_path: Path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "source_folder").mkdir()
    for name in [
        "book.pdf",
        "book.epub",
        "book.mobi",
        "book.azw3",
        "notes.md",
        "draft.txt",
        "outline.docx",
        "legacy.doc",
        "cover.png",
    ]:
        (input_dir / name).write_text("x", encoding="utf-8")

    expected = {
        ".pdf",
        ".epub",
        ".mobi",
        ".azw3",
        ".md",
        ".txt",
        ".docx",
        ".doc",
    }

    cli_extensions = {item["extension"] for item in scan_cli_input_files(str(input_dir))}
    pipeline_extensions = {item["extension"] for item in scan_pipeline_input_files(str(input_dir))}
    cli_directories = {item["name"] for item in scan_cli_input_files(str(input_dir)) if item.get("is_directory")}
    pipeline_directories = {item["name"] for item in scan_pipeline_input_files(str(input_dir)) if item.get("is_directory")}

    assert expected <= cli_extensions
    assert ".png" not in cli_extensions
    assert "source_folder" in cli_directories
    assert expected <= pipeline_extensions
    assert ".png" not in pipeline_extensions
    assert "source_folder" in pipeline_directories
