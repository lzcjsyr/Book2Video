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
    assert "{skill_path_context}" in prompt
    assert "{embedded_skill_bundle}" not in prompt
    assert "{style_context}" in prompt
    assert "{payload_json}" in prompt
    assert "durationSeconds" in prompt
    assert "data-start" in prompt
    assert "STEP4_HYPERFRAMES_PROMPT_VERSION: 2026-06-21-layout-structure-v6" in prompt
    assert "visualKeywords" in prompt
    assert "禁止依赖外部 `keywords`" in prompt
    assert "禁止直接展示 `content` 原句" in prompt
    assert "版式结构选择" in prompt
    assert "left_list_right_verdict" in prompt
    assert "number_to_conclusion" in prompt
    assert "清晰阅读路径" in prompt
    assert "空半屏" in prompt
    assert "任何可读文字不得小于 60px" in prompt
    assert "辅助短语透明度不得低于 `rgba(..., 0.68)`" in prompt
    assert "标签类文字透明度不得低于 `rgba(..., 0.55)`" in prompt
    assert "低于 `0.4` 透明度的颜色只能用于纯装饰" in prompt
    assert "npx --yes hyperframes@0.6.115 validate --json" in prompt
    assert "npx --yes hyperframes@0.6.115 inspect --json --samples 15" in prompt
    assert "### A. 代码自检" in prompt
    assert "### B. 视觉自检" in prompt
    assert "先做代码层面检查，再生成截图" in prompt
    assert "列出所有可读文字的 `文本 / font-size / opacity`" in prompt
    assert "任一可读文字低于当前分辨率最小字号或透明度阈值" in prompt
    assert "逐项核对根尺寸、data-duration、data-start、data-track-index" in prompt
    assert "npx --yes hyperframes@0.6.115 snapshot --frames 5" in prompt
    assert "查看 `snapshots/` 中的 PNG 关键帧" in prompt
    assert "修复后必须重新完成代码自检、重新运行 `snapshot --frames 5` 并再次读图确认" in prompt
    assert "是否能明确看出所选结构模板" in prompt
    assert "布局是否有遮挡、贴边、偏角落" in prompt
    assert "孤立数字、空半屏或无关系的信息岛" in prompt
    assert "必须加入 2-3 层非文字视觉层" in prompt
    assert "不要只生成静态大字 + 分隔线 + 淡入上移" in prompt
    assert len(prompt.splitlines()) <= 170


def test_step4_hyperframes_prompt_is_loaded_from_prompt_file(monkeypatch):
    from core.infra.ai import claude_agent

    monkeypatch.setattr(
        claude_agent,
        "STEP4_HYPERFRAMES_AGENT_PROMPT_TEMPLATE",
        "PROMPT_FILE_MARKER\n{skill_path_context}\n{style_context}\n{payload_json}\n{target_index_html_path}",
    )

    prompt = claude_agent._build_step4_hyperframes_prompt(
        segment_payload={"index": 1, "durationSeconds": 1.25},
        style_preset="data_driven",
        skill_path_context="STEP4_SKILLS_ROOT=/dynamic/project/skills/step4",
        target_index_html_path="/test/path/index.html",
    )

    assert prompt.startswith("PROMPT_FILE_MARKER")
    assert "HyperFrames rules" not in prompt
    assert "STEP4_SKILLS_ROOT=/dynamic/project/skills/step4" in prompt
    assert "data_driven" in prompt
    assert "Swiss Pulse" in prompt
    assert '"durationSeconds": 1.25' in prompt
    assert "/test/path/index.html" in prompt


def test_step4_skill_discovery_context_lists_frontmatter_and_entry_paths(tmp_path):
    from core.infra.hyperframes.skill_loader import build_step4_hyperframes_skill_path_context

    skills_root = tmp_path / "skills" / "step4"
    (skills_root / "hyperframes").mkdir(parents=True)
    (skills_root / "hyperframes" / "SKILL.md").write_text(
        "---\n"
        "name: hyperframes\n"
        "description: >\n"
        "  READ THIS FIRST for HyperFrames video tasks.\n"
        "metadata: { \"tags\": \"router\" }\n"
        "---\n"
        "\n"
        "# Body should not be embedded\n",
        encoding="utf-8",
    )
    (skills_root / "hyperframes-cli").mkdir()
    (skills_root / "hyperframes-cli" / "SKILL.md").write_text(
        "---\n"
        "name: hyperframes-cli\n"
        "description: HyperFrames CLI dev loop.\n"
        "---\n"
        "\n"
        "# CLI body should not be embedded\n",
        encoding="utf-8",
    )

    context = build_step4_hyperframes_skill_path_context(skills_root / "hyperframes")

    assert f"STEP4_SKILLS_ROOT={skills_root}" in context
    assert "可用 Step4 Skills" in context
    assert "name: hyperframes" in context
    assert f"entry_path: {skills_root / 'hyperframes/SKILL.md'}" in context
    assert "description: READ THIS FIRST for HyperFrames video tasks." in context
    assert "metadata: {\"tags\": \"router\"}" in context
    assert "name: hyperframes-cli" in context
    assert f"entry_path: {skills_root / 'hyperframes-cli/SKILL.md'}" in context
    assert "禁止跳过该 skill 的 SKILL.md 直接读取它的 references" in context
    assert "如果读取了某个目录下的 reference/palette/adapter/rule 文件，必须已经先读取同目录对应的 SKILL.md" in context
    assert "# Body should not be embedded" not in context
    assert "必读入口文件绝对路径" not in context
