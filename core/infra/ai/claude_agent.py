from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import Any

import anyio
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    StreamEvent,
    SystemMessage,
    UserMessage,
    query,
)

from core.config import config
from core.prompts import build_step1_agent_prompt

STEP1_AGENT_TOOLS = ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Skill"]
STEP1_AGENT_SKILL = "video-book-direct-read"

STEP1_EXTRACT_NAME = "_extract.txt"
STEP1_COVERAGE_LEDGER_NAME = "_coverage_ledger.json"
STEP1_SESSION_LOG_NAME = "_agent_session.jsonl"

_MAX_LOG_FIELD_CHARS = 12_000


def _step1_agent_add_dirs(input_file: str) -> list[str]:
    input_path = Path(input_file)
    if input_path.is_dir():
        return [str(input_path)]
    return [str(input_path.parent)]


def build_step1_agent_env() -> dict[str, str]:
    api_key = (config.MIMO_API_KEY or "").strip()
    if not api_key:
        raise RuntimeError("步骤1需要 MIMO_API_KEY（.env），用于驱动 Claude Agent SDK")
    return {
        "ANTHROPIC_BASE_URL": config.LLM_BASE_URL_STEP1,
        "ANTHROPIC_API_KEY": api_key,
        "ANTHROPIC_MODEL": config.LLM_MODEL_STEP1,
    }


def _truncate_for_log(value: Any, *, max_chars: int = _MAX_LOG_FIELD_CHARS) -> Any:
    if isinstance(value, str) and len(value) > max_chars:
        return {
            "_truncated": True,
            "length": len(value),
            "preview": value[:max_chars],
        }
    if isinstance(value, dict):
        return {key: _truncate_for_log(item, max_chars=max_chars) for key, item in value.items()}
    if isinstance(value, list):
        return [_truncate_for_log(item, max_chars=max_chars) for item in value]
    return value


def _serialize_sdk_message(message: object) -> dict[str, Any]:
    if isinstance(message, UserMessage):
        payload = asdict(message)
        payload["kind"] = "UserMessage"
        return _truncate_for_log(payload)
    if isinstance(message, AssistantMessage):
        payload = asdict(message)
        payload["kind"] = "AssistantMessage"
        return _truncate_for_log(payload)
    if isinstance(message, SystemMessage):
        payload = asdict(message)
        payload["kind"] = "SystemMessage"
        return _truncate_for_log(payload)
    if isinstance(message, ResultMessage):
        payload = asdict(message)
        payload["kind"] = "ResultMessage"
        return payload
    if isinstance(message, StreamEvent):
        payload = asdict(message)
        payload["kind"] = "StreamEvent"
        return _truncate_for_log(payload)
    if is_dataclass(message):
        payload = asdict(message)
        payload["kind"] = type(message).__name__
        return _truncate_for_log(payload)
    return {"kind": type(message).__name__, "repr": repr(message)}


class AgentSessionLog:
    """Append-only JSONL trace for a single Claude Agent invocation."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._seq = 0

    def append(self, event: str, payload: dict[str, Any]) -> None:
        self._seq += 1
        record = {
            "seq": self._seq,
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **payload,
        }
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, default=str))
            handle.write("\n")


async def _run_step1_agent_async(
    *,
    input_file: str,
    output_json: str,
    extract_path: str,
    coverage_ledger_path: str,
    session_log_path: str,
    text_dir: str,
    num_segments: int,
    skill_path: str,
    repo_root: str,
) -> None:
    prompt = build_step1_agent_prompt(
        input_file=input_file,
        output_json=output_json,
        extract_path=extract_path,
        coverage_ledger_path=coverage_ledger_path,
        text_dir=text_dir,
        num_segments=num_segments,
        skill_path=skill_path,
    )
    options = ClaudeAgentOptions(
        cwd=repo_root,
        model=config.LLM_MODEL_STEP1,
        tools=STEP1_AGENT_TOOLS,
        allowed_tools=STEP1_AGENT_TOOLS,
        skills=[STEP1_AGENT_SKILL],
        permission_mode="acceptEdits",
        max_turns=200,
        add_dirs=_step1_agent_add_dirs(input_file),
        env=build_step1_agent_env(),
    )
    session_log = AgentSessionLog(session_log_path)
    session_log.append(
        "session_start",
        {
            "step": "step_1",
            "input_file": input_file,
            "output_json": output_json,
            "extract_path": extract_path,
            "coverage_ledger_path": coverage_ledger_path,
            "text_dir": text_dir,
            "num_segments": num_segments,
            "skill_path": skill_path,
            "repo_root": repo_root,
            "add_dirs": _step1_agent_add_dirs(input_file),
            "model": config.LLM_MODEL_STEP1,
            "tools": STEP1_AGENT_TOOLS,
            "skill": STEP1_AGENT_SKILL,
            "prompt": prompt,
        },
    )

    result_message: ResultMessage | None = None
    try:
        async for message in query(prompt=prompt, options=options):
            session_log.append("message", {"message": _serialize_sdk_message(message)})
            if isinstance(message, ResultMessage):
                result_message = message
                if message.is_error:
                    raise RuntimeError(message.result or "Claude Agent Step 1 failed")
    except Exception as exc:
        session_log.append(
            "session_error",
            {"error_type": type(exc).__name__, "error": str(exc)},
        )
        raise
    finally:
        if result_message is not None:
            session_log.append(
                "session_end",
                {
                    "success": not result_message.is_error,
                    "result": _serialize_sdk_message(result_message),
                },
            )
        else:
            session_log.append(
                "session_end",
                {"success": False, "result": None, "note": "no ResultMessage received"},
            )

    if not Path(output_json).exists():
        raise FileNotFoundError(f"Claude Agent未生成raw.json: {output_json}")


def run_step1_agent(
    *,
    input_file: str,
    output_json: str,
    extract_path: str,
    coverage_ledger_path: str,
    session_log_path: str,
    text_dir: str,
    num_segments: int,
    skill_path: str,
    repo_root: str,
) -> None:
    runner = partial(
        _run_step1_agent_async,
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
    anyio.run(runner)
