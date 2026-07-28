import importlib.util
import json
from pathlib import Path

import pytest


SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "step1" / "book-commerce-video-script"


def test_commerce_skill_is_single_run_and_does_not_call_subagents():
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    for marker in [
        "单次运行、单份终稿、单次最终包装",
        "本 skill 内不调用 subagent",
        "正文只形成一个最终版本",
        "不创建初稿、轮次稿或评分稿",
        "只落盘一次",
    ]:
        assert marker in skill

    assert "commerce-script-writer" not in skill
    assert "commerce-script-scorer" not in skill


def test_commerce_skill_keeps_duration_and_raw_contract():
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    contract = (SKILL_DIR / "references" / "output-contract.md").read_text(encoding="utf-8")

    assert "1050" in skill
    assert "950-1150" in skill
    assert "load_step1_agent_raw" in skill
    assert "步骤 1.5" in skill
    final_contract = contract.split("## 最终 raw JSON", 1)[1]
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

    for forbidden in ["_commerce_round_", "_commerce_score_", "_draft_v1.txt"]:
        assert forbidden not in contract


def test_commerce_skill_prioritizes_emotion_and_purchase_desire():
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    writing_rules = (SKILL_DIR / "references" / "conversion-writing.md").read_text(encoding="utf-8")

    for marker in [
        "这句话在说我",
        "至少完成一次完整强反转",
        "为什么是这本书",
        "一个真心推荐的人",
    ]:
        assert marker in skill
    for marker in [
        "卖点是书有什么，买点是观众为什么此刻想拥有它",
        "被看见",
        "被说中",
        "书带来反转",
        "从理解到想拥有",
        "克制成交",
    ]:
        assert marker in writing_rules


def test_commerce_skill_has_no_case_specific_reference():
    all_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in SKILL_DIR.rglob("*")
        if path.is_file() and path.suffix in {".md", ".yaml", ".py"}
    )

    for forbidden in [
        "奥斯维辛",
        "大屠杀",
        "纳粹",
    ]:
        assert forbidden not in all_text


def _load_validator():
    path = SKILL_DIR / "scripts" / "validate_raw.py"
    spec = importlib.util.spec_from_file_location("book_commerce_validate_raw", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _valid_raw(content: str) -> dict:
    return {
        "source_name": "《测试书》",
        "video_titles": ["标题一", "标题二", "标题三"],
        "cover_titles": ["封面一", "封面二", "封面三"],
        "cover_subtitles": ["副标题一", "副标题二", "副标题三"],
        "golden_quotes": ["金句一", "金句二", "金句三"],
        "content": content,
        "total_length": len(content),
    }


def test_commerce_raw_validator_enforces_exact_downstream_contract(tmp_path):
    validator = _load_validator()
    draft = tmp_path / "_draft_final.txt"
    raw = tmp_path / "raw.json"
    content = "这是一段完整口播。" * 125
    draft.write_text(content, encoding="utf-8")
    raw.write_text(json.dumps(_valid_raw(content), ensure_ascii=False), encoding="utf-8")

    loaded = validator.validate(raw, draft)
    assert loaded["total_length"] == len(loaded["content"])

    invalid = _valid_raw(content)
    invalid["extra"] = "不允许"
    raw.write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="字段集合错误"):
        validator.validate(raw, draft)


def test_commerce_raw_validator_rejects_wrong_duration_and_cover_lengths(tmp_path):
    validator = _load_validator()
    raw = tmp_path / "raw.json"

    too_short = _valid_raw("太短")
    raw.write_text(json.dumps(too_short, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="950到1150"):
        validator.validate(raw)

    content = "这是一段完整口播。" * 125
    long_cover = _valid_raw(content)
    long_cover["cover_titles"][0] = "这是一个明显超过十个字符的封面标题"
    raw.write_text(json.dumps(long_cover, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="不得超过10字符"):
        validator.validate(raw)


def test_commerce_skill_is_default_and_prompt_allows_single_run_override():
    example_config = Path("config.example.yaml").read_text(encoding="utf-8")
    prompt = Path("prompts/step1_agent.md").read_text(encoding="utf-8")

    assert "agent_skill: book-commerce-video-script" in example_config
    assert "明确禁止调用 subagent" in prompt


def test_run_step_1_automatically_validates_commerce_output(monkeypatch, tmp_path):
    from core.pipeline import steps

    input_file = tmp_path / "book.epub"
    input_file.write_text("source", encoding="utf-8")
    content = "这是一段完整口播。" * 125

    def fake_run_step1_agent(**kwargs):
        Path(kwargs["output_json"]).write_text(
            json.dumps(_valid_raw(content), ensure_ascii=False),
            encoding="utf-8",
        )

    monkeypatch.setattr(steps, "run_step1_agent", fake_run_step1_agent)
    monkeypatch.setattr(steps, "export_raw_to_docx", lambda *args, **kwargs: None)
    monkeypatch.setattr(steps.config, "STEP1_AGENT_SKILL", "book-commerce-video-script")

    result = steps.run_step_1(str(input_file), str(tmp_path / "output"), num_segments=50)

    assert result["success"] is True
    assert result["raw"]["total_length"] == len(content)
