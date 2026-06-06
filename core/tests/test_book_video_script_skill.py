from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "book-video-script"


def test_writing_standard_keeps_single_clean_raw_json_schema():
    standard = (SKILL_DIR / "references" / "writing-standard.md").read_text(encoding="utf-8")

    for field in [
        "source_name",
        "video_titles",
        "cover_titles",
        "cover_subtitles",
        "golden_quotes",
        "comment_hook_options",
        "share_hook_options",
        "content",
        "total_length",
        "target_segments",
    ]:
        assert standard.count(f'"{field}"') == 1

    assert "不要使用 Markdown" in standard
    assert "JSON 没有尾随逗号" in standard


def test_skill_entry_requires_coverage_ledger_before_scripting():
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    reading = (SKILL_DIR / "references" / "reading-strategy.md").read_text(encoding="utf-8")

    assert "_coverage_ledger.json" in reading
    assert "coverage_check.passed=true" in skill
    assert "行覆盖率" in reading
