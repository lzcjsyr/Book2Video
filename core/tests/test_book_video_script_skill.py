from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "step1" / "book-video-script_V2"


def test_writing_standard_keeps_single_clean_raw_json_schema():
    standard = (SKILL_DIR / "references" / "writing-standard.md").read_text(encoding="utf-8")
    final_contract = standard.split("## 最终 JSON 输出契约", 1)[1]

    for field in [
        "source_name",
        "video_titles",
        "cover_titles",
        "cover_subtitles",
        "golden_quotes",
        "content",
        "total_length",
    ]:
        assert final_contract.count(f'"{field}"') == 1

    assert '"comment_hook_options"' not in standard
    assert '"share_hook_options"' not in standard
    assert '"target_segments"' not in final_contract
    assert "保留自然段落换行" in final_contract
    assert "去掉换行" not in standard
    assert "没有分段" not in standard

    assert "不要使用 Markdown" in standard
    assert "JSON 没有尾随逗号" in standard


def test_skill_entry_requires_coverage_ledger_before_scripting():
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    reading = (SKILL_DIR / "references" / "reading-strategy.md").read_text(encoding="utf-8")

    assert "_coverage_ledger.json" in reading
    assert "coverage_check.passed=true" in skill
    assert "行覆盖率" in reading


def test_reading_strategy_keeps_core_execution_rules():
    reading = (SKILL_DIR / "references" / "reading-strategy.md").read_text(encoding="utf-8")

    for marker in [
        "Bash",
        "Read",
        "23000",
        "150000",
        "200000",
        "required_coverage_ratio: 1.0",
        "required_coverage_ratio: 0.8",
        "required_coverage_ratio: 0.5",
        "_coverage_ledger.json",
        "coverage_check.passed=true",
        "减半",
        "partial",
        "禁止",
    ]:
        assert marker in reading

    assert "阶段稿" in reading
    assert "不要用 `Read` 扫全文" in reading
    assert "Read` 只用于 skill、references、小配置文件" not in reading


def test_revision_workflow_keeps_v1_simple_and_auditable():
    workflow = (SKILL_DIR / "references" / "revision-workflow.md").read_text(encoding="utf-8")

    assert "第一稿的目标" in workflow
    assert "按 `_angle_brief.json` 和 `writing-standard.md` 写出完整初稿" in workflow
    assert "达到 `draft_min_chars`" in workflow
    assert "先复制 `_draft_v1.txt` 为 `_draft_final.txt`" in workflow
    assert "只有初稿主线明显错误且局部修改无法补救时，才允许整篇重写" in workflow
    assert "_revision_audit.json" in workflow
    assert "before/after" in workflow
