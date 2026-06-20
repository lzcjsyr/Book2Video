from pathlib import Path


PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


def test_static_visual_prompts_are_named_for_step4():
    assert (PROMPTS_DIR / "step4_description.md").exists()
    assert (PROMPTS_DIR / "step4_safety.md").exists()
    assert (PROMPTS_DIR / "step4_styles.yaml").exists()

    assert not (PROMPTS_DIR / "step3_description.md").exists()
    assert not (PROMPTS_DIR / "step3_safety.md").exists()
    assert not (PROMPTS_DIR / "step3_styles.yaml").exists()


def test_hyperframes_agent_has_dedicated_step4_prompt_file():
    prompt_path = PROMPTS_DIR / "step4_hyperframes_agent.md"

    assert prompt_path.exists()
    assert (PROMPTS_DIR / "step4_hyperframes_styles.yaml").exists()
    prompt = prompt_path.read_text(encoding="utf-8")
    assert "{embedded_skill_bundle}" in prompt
    assert "{style_context}" in prompt
    assert "{payload_json}" in prompt
    assert "durationSeconds" in prompt
    assert "data-start" in prompt
    assert "Inter" in prompt
    assert "STEP4_HYPERFRAMES_PROMPT_VERSION: 2026-06-20-structure-review-v4" in prompt
    assert "visualKeywords" in prompt
    assert "禁止依赖外部 `keywords`" in prompt
    assert "禁止直接展示 `content` 原句" in prompt
    assert "版式结构选择" in prompt
    assert "left_list_right_verdict" in prompt
    assert "number_to_conclusion" in prompt
    assert "清晰阅读路径" in prompt
    assert "不能一侧空着" in prompt
    assert "任何可读文字不得小于 60px" in prompt
    assert "辅助短语透明度不得低于 `rgba(..., 0.68)`" in prompt
    assert "标签类文字透明度不得低于 `rgba(..., 0.55)`" in prompt
    assert "低于 `0.4` 透明度的颜色只能用于纯装饰" in prompt
    assert "npx --yes hyperframes@0.6.115 validate --json" in prompt
    assert "npx --yes hyperframes@0.6.115 inspect --json --samples 15" in prompt
    assert "npx --yes hyperframes@0.6.115 snapshot --frames 5" in prompt
    assert "查看 `snapshots/` 中的 PNG 关键帧" in prompt
    assert "是否能明确看出所选结构模板" in prompt
    assert "孤立数字、空半屏或无关系的信息岛" in prompt


def test_step4_hyperframes_prompt_is_loaded_from_prompt_file(monkeypatch):
    from core.infra.ai import claude_agent

    monkeypatch.setattr(
        claude_agent,
        "STEP4_HYPERFRAMES_AGENT_PROMPT_TEMPLATE",
        "PROMPT_FILE_MARKER\n{embedded_skill_bundle}\n{style_context}\n{payload_json}\n{target_index_html_path}",
    )

    prompt = claude_agent._build_step4_hyperframes_prompt(
        segment_payload={"index": 1, "durationSeconds": 1.25},
        style_preset="data_driven",
        embedded_skill_bundle="HyperFrames rules",
        target_index_html_path="/test/path/index.html",
    )

    assert prompt.startswith("PROMPT_FILE_MARKER")
    assert "HyperFrames rules" in prompt
    assert "data_driven" in prompt
    assert "Swiss Pulse" in prompt
    assert '"durationSeconds": 1.25' in prompt
    assert "/test/path/index.html" in prompt
