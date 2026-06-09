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
    prompt = prompt_path.read_text(encoding="utf-8")
    assert "{embedded_skill_bundle}" in prompt
    assert "{style_preset}" in prompt
    assert "{payload_json}" in prompt
    assert "durationSeconds" in prompt
    assert "data-start" in prompt
    assert "Inter" in prompt
    assert "当前工作目录" in prompt


def test_step4_hyperframes_prompt_is_loaded_from_prompt_file(monkeypatch):
    from core.infra.ai import claude_agent

    monkeypatch.setattr(
        claude_agent,
        "STEP4_HYPERFRAMES_AGENT_PROMPT_TEMPLATE",
        "PROMPT_FILE_MARKER\n{embedded_skill_bundle}\n{style_preset}\n{payload_json}",
    )

    prompt = claude_agent._build_step4_hyperframes_prompt(
        segment_payload={"index": 1, "durationSeconds": 1.25},
        style_preset="data_driven",
        embedded_skill_bundle="HyperFrames rules",
    )

    assert prompt.startswith("PROMPT_FILE_MARKER")
    assert "HyperFrames rules" in prompt
    assert "data_driven" in prompt
    assert '"durationSeconds": 1.25' in prompt
