import json
from pathlib import Path

import anyio
from claude_agent_sdk import ResultMessage

from core.infra.ai import claude_agent
from core.pipeline import steps


def _valid_raw(target_segments: int = 70) -> dict:
    return {
        "source_name": "正义论",
        "video_titles": ["为什么正义不只是好心"],
        "cover_titles": ["正义之问"],
        "cover_subtitles": ["制度如何塑造命运"],
        "golden_quotes": ["真正的正义，要先问最弱的人站在哪里。"],
        "comment_hook_options": ["你觉得公平更像结果，还是更像规则？"],
        "share_hook_options": ["这条适合转给正在讨论公平的人。"],
        "content": "这是一段没有换行的完整口播终稿。",
        "total_length": 17,
        "target_segments": target_segments,
    }


def test_run_step_1_uses_claude_agent_skill_and_loads_raw_json(monkeypatch, tmp_path: Path):
    input_file = tmp_path / "book.md"
    input_file.write_text("source text", encoding="utf-8")

    captured = {}

    def fake_run_step1_agent(
        *,
        input_file,
        output_json,
        extract_path,
        coverage_ledger_path,
        session_log_path,
        text_dir,
        num_segments,
        skill_path,
        repo_root,
    ):
        captured.update(
            input_file=input_file,
            output_json=output_json,
            extract_path=extract_path,
            coverage_ledger_path=coverage_ledger_path,
            session_log_path=session_log_path,
            text_dir=text_dir,
            num_segments=num_segments,
            skill_path=skill_path,
            repo_root=repo_root,
        )
        Path(output_json).write_text(json.dumps(_valid_raw(num_segments), ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr(steps, "run_step1_agent", fake_run_step1_agent)
    monkeypatch.setattr(steps, "export_raw_to_docx", lambda *args, **kwargs: None)

    result = steps.run_step_1(str(input_file), str(tmp_path / "output"), num_segments=70)

    assert result["success"] is True
    raw_json_path = Path(result["raw"]["raw_json_path"])
    assert raw_json_path.name == "raw.json"
    assert raw_json_path.parent.name == "text"
    assert captured["input_file"] == str(input_file)
    assert captured["output_json"] == str(raw_json_path)
    assert Path(captured["extract_path"]).name == claude_agent.STEP1_EXTRACT_NAME
    assert Path(captured["coverage_ledger_path"]).name == claude_agent.STEP1_COVERAGE_LEDGER_NAME
    assert Path(captured["session_log_path"]).name == claude_agent.STEP1_SESSION_LOG_NAME
    assert captured["num_segments"] == 70
    assert captured["skill_path"].endswith("core/skills/video-book-direct-read")
    assert captured["repo_root"] == steps._get_project_root()
    assert result["raw"]["total_length"] == 17


def test_step_1_rejects_agent_output_that_does_not_match_raw_contract(tmp_path: Path):
    invalid_path = tmp_path / "raw.json"
    invalid_path.write_text(json.dumps({"content": "缺少字段"}, ensure_ascii=False), encoding="utf-8")

    try:
        steps.load_step1_agent_raw(str(invalid_path), expected_segments=70)
    except ValueError as exc:
        assert "comment_hook_options" in str(exc)
        assert "target_segments" in str(exc)
    else:
        raise AssertionError("invalid Step 1 raw JSON should be rejected")


def test_build_step1_agent_env_uses_mimo_gateway(monkeypatch):
    monkeypatch.setattr(
        "core.infra.ai.claude_agent.config.MIMO_API_KEY",
        "test-mimo-key",
        raising=False,
    )
    env = claude_agent.build_step1_agent_env()
    assert env["ANTHROPIC_BASE_URL"] == "https://token-plan-sgp.xiaomimimo.com/anthropic"
    assert env["ANTHROPIC_API_KEY"] == "test-mimo-key"
    assert env["ANTHROPIC_MODEL"] == "mimo-v2.5"


def test_step1_agent_allows_200_turns(monkeypatch, tmp_path: Path):
    captured = {}
    output_json = tmp_path / "text" / "raw.json"

    async def fake_query(*, prompt, options):
        captured["max_turns"] = options.max_turns
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(_valid_raw(), ensure_ascii=False), encoding="utf-8")
        yield ResultMessage(
            subtype="success",
            duration_ms=0,
            duration_api_ms=0,
            is_error=False,
            num_turns=1,
            session_id="test-session",
        )

    monkeypatch.setattr(claude_agent, "query", fake_query)
    monkeypatch.setattr(claude_agent, "build_step1_agent_env", lambda: {})

    async def run_agent():
        await claude_agent._run_step1_agent_async(
            input_file=str(tmp_path / "book.pdf"),
            output_json=str(output_json),
            extract_path=str(tmp_path / "text" / claude_agent.STEP1_EXTRACT_NAME),
            coverage_ledger_path=str(tmp_path / "text" / claude_agent.STEP1_COVERAGE_LEDGER_NAME),
            session_log_path=str(tmp_path / "text" / claude_agent.STEP1_SESSION_LOG_NAME),
            text_dir=str(tmp_path / "text"),
            num_segments=70,
            skill_path=str(tmp_path / "core" / "skills" / "video-book-direct-read"),
            repo_root=str(tmp_path),
        )

    anyio.run(run_agent)

    assert captured["max_turns"] == 200


def test_step1_agent_prompt_includes_absolute_skill_path_and_target_segments(tmp_path: Path):
    from core.prompts import build_step1_agent_prompt

    skill_path = tmp_path / "core" / "skills" / "video-book-direct-read"
    skill_path.mkdir(parents=True)

    prompt = build_step1_agent_prompt(
        input_file=str(tmp_path / "book.pdf"),
        output_json=str(tmp_path / "output" / "text" / "raw.json"),
        extract_path=str(tmp_path / "output" / "text" / "_extract.txt"),
        coverage_ledger_path=str(tmp_path / "output" / "text" / "_coverage_ledger.json"),
        text_dir=str(tmp_path / "output" / "text"),
        num_segments=70,
        skill_path=str(skill_path),
    )

    assert str(skill_path) in prompt
    assert str(skill_path).startswith("/")
    assert "`target_segments` 必须写为 70" in prompt
    assert "_coverage_ledger.json" in prompt
    assert "覆盖自检" in prompt
    assert ".md/.txt" in prompt
    assert "复制或规范化" in prompt


def test_agent_session_log_appends_jsonl_records(tmp_path: Path):
    log_path = tmp_path / "text" / claude_agent.STEP1_SESSION_LOG_NAME
    session_log = claude_agent.AgentSessionLog(log_path)
    session_log.append("session_start", {"step": "step_1"})
    session_log.append("message", {"message": {"kind": "UserMessage", "content": "hi"}})

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert first["event"] == "session_start"
    assert first["seq"] == 1
    assert second["event"] == "message"
    assert second["seq"] == 2
    assert "ts" in first
