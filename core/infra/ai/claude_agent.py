from __future__ import annotations

import json
import re
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
STEP1_AGENT_SKILL = config.STEP1_AGENT_SKILL

STEP1_EXTRACT_NAME = "_extract.txt"
STEP1_COVERAGE_LEDGER_NAME = "_coverage_ledger.json"
STEP1_SESSION_LOG_NAME = "_agent_session.jsonl"

_MAX_LOG_FIELD_CHARS = 12_000
_OMITTED_BASH_READ_CONTENT = "[omitted: Bash text-window output from _extract.txt]"
_OMITTED_BASH_READ_COMMAND = "[omitted: Bash text-window read command from _extract.txt]"
_OMITTED_SKILL_REFERENCE_CONTENT = "[omitted: skill/reference file content]"
_OMITTED_PERSISTED_FILE_CONTENT = "[omitted: file content already persisted]"
_OMITTED_PERSISTED_READ_CONTENT = "[omitted: persisted draft/raw file read]"
_OMITTED_LEDGER_WRITE_COMMAND = "[omitted: Bash write command for _coverage_ledger.json]"
_BASH_READ_WINDOW_RE = re.compile(r"\b(sed\s+-n|head|tail)\b")


def _step1_agent_add_dirs(input_file: str) -> list[str]:
    input_path = Path(input_file)
    if input_path.is_dir():
        return [str(input_path)]
    return [str(input_path.parent)]


def build_step1_agent_env() -> dict[str, str]:
    server = (config.LLM_SERVER_STEP1 or "").strip().lower()
    if not server:
        raise RuntimeError("步骤1需要配置 LLM_SERVER_STEP1（mimo/siliconflow/openrouter/volcengine/deepseek）")

    if server == "mimo":
        base_url = "https://token-plan-sgp.xiaomimimo.com/anthropic"
        api_key = (config.MIMO_API_KEY or "").strip()
        key_name = "MIMO_API_KEY"
    elif server == "deepseek":
        base_url = "https://api.deepseek.com/anthropic"
        api_key = (config.DEEPSEEK_API_KEY or "").strip()
        key_name = "DEEPSEEK_API_KEY"
    elif server == "siliconflow":
        base_url = "https://api.siliconflow.cn/"
        api_key = (config.SILICONFLOW_KEY or "").strip()
        key_name = "SILICONFLOW_KEY"
    elif server == "openrouter":
        base_url = "https://openrouter.ai/api"
        api_key = (config.OPENROUTER_API_KEY or "").strip()
        key_name = "OPENROUTER_API_KEY"
    elif server == "volcengine":
        base_url = "https://ark.cn-beijing.volces.com/api/v3"
        api_key = (config.VOLCENGINE_API_KEY or "").strip()
        key_name = "VOLCENGINE_API_KEY"
    else:
        raise ValueError(f"不支持的步骤1 LLM服务商: {server}，支持的服务商: mimo, deepseek, siliconflow, openrouter, volcengine")

    if not api_key:
        raise RuntimeError(f"步骤1需要 {key_name}（.env），用于驱动 Claude Agent SDK")

    return {
        "ANTHROPIC_BASE_URL": base_url,
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
        self._omitted_bash_read_tool_ids: set[str] = set()
        self._omitted_persisted_read_tool_ids: set[str] = set()

    @staticmethod
    def _is_extract_window_read_command(command: str) -> bool:
        return "_extract.txt" in command and bool(_BASH_READ_WINDOW_RE.search(command))

    @staticmethod
    def _is_skill_reference_path(path: str) -> bool:
        return "/core/skills/" in path and (
            path.endswith("/SKILL.md") or "/references/" in path
        )

    @staticmethod
    def _is_large_persisted_file_write(item: dict[str, Any]) -> bool:
        if item.get("name") != "Write":
            return False
        input_payload = item.get("input")
        if not isinstance(input_payload, dict):
            return False
        content = input_payload.get("content")
        return isinstance(content, str) and len(content) > 1000

    @staticmethod
    def _is_coverage_ledger_write_command(command: str) -> bool:
        return "_coverage_ledger.json" in command and "cat >" in command

    @staticmethod
    def _is_persisted_read_path(path: str) -> bool:
        return Path(path).name in {
            "_draft_v1.txt",
            "_draft_v2_structure.txt",
            "_draft_final.txt",
            "_revision_audit.json",
            "raw.json",
        }

    def _compact_message_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        message = payload.get("message")
        if not isinstance(message, dict):
            return payload

        content = message.get("content")
        if not isinstance(content, list):
            return payload

        changed = False
        omitted_tool_result_ids: set[str] = set()
        omit_skill_reference_result = False
        tool_use_result = message.get("tool_use_result")
        if isinstance(tool_use_result, dict):
            file_result = tool_use_result.get("file")
            if isinstance(file_result, dict):
                file_path = file_result.get("filePath")
                omit_skill_reference_result = isinstance(file_path, str) and self._is_skill_reference_path(file_path)

        compacted_content: list[Any] = []
        for item in content:
            if not isinstance(item, dict):
                compacted_content.append(item)
                continue

            if self._is_large_persisted_file_write(item):
                compacted_item = dict(item)
                compacted_input = dict(item.get("input") or {})
                content_value = compacted_input.get("content")
                compacted_input["content"] = _OMITTED_PERSISTED_FILE_CONTENT
                compacted_input["content_length"] = len(content_value) if isinstance(content_value, str) else None
                compacted_input["log_omitted"] = "persisted_file_content"
                compacted_item["input"] = compacted_input
                compacted_content.append(compacted_item)
                changed = True
                continue

            if item.get("name") == "Read":
                input_payload = item.get("input")
                file_path = input_payload.get("file_path") if isinstance(input_payload, dict) else None
                if isinstance(file_path, str) and self._is_persisted_read_path(file_path):
                    tool_id = item.get("id")
                    if isinstance(tool_id, str):
                        self._omitted_persisted_read_tool_ids.add(tool_id)
                    compacted_item = dict(item)
                    compacted_item["log_omitted"] = "persisted_file_read"
                    compacted_content.append(compacted_item)
                    changed = True
                    continue

            if item.get("name") == "Bash":
                input_payload = item.get("input")
                command = input_payload.get("command") if isinstance(input_payload, dict) else None
                if isinstance(command, str) and self._is_extract_window_read_command(command):
                    tool_id = item.get("id")
                    if isinstance(tool_id, str):
                        self._omitted_bash_read_tool_ids.add(tool_id)
                    compacted_item = dict(item)
                    compacted_input = dict(input_payload or {})
                    compacted_input["command"] = _OMITTED_BASH_READ_COMMAND
                    compacted_item["input"] = compacted_input
                    compacted_item["log_omitted"] = "bash_extract_window_read"
                    compacted_content.append(compacted_item)
                    changed = True
                    continue
                if isinstance(command, str) and self._is_coverage_ledger_write_command(command):
                    compacted_item = dict(item)
                    compacted_input = dict(input_payload or {})
                    compacted_input["command"] = _OMITTED_LEDGER_WRITE_COMMAND
                    compacted_input["command_length"] = len(command)
                    compacted_item["input"] = compacted_input
                    compacted_item["log_omitted"] = "coverage_ledger_write"
                    compacted_content.append(compacted_item)
                    changed = True
                    continue

            tool_use_id = item.get("tool_use_id")
            is_error = item.get("is_error") is True
            if isinstance(tool_use_id, str) and tool_use_id in self._omitted_bash_read_tool_ids and not is_error:
                content_value = item.get("content")
                compacted_item = dict(item)
                compacted_item["content"] = _OMITTED_BASH_READ_CONTENT
                compacted_item["content_length"] = len(content_value) if isinstance(content_value, str) else None
                compacted_item["log_omitted"] = "bash_extract_window_output"
                omitted_tool_result_ids.add(tool_use_id)
                compacted_content.append(compacted_item)
                changed = True
                continue

            if isinstance(tool_use_id, str) and tool_use_id in self._omitted_persisted_read_tool_ids and not is_error:
                content_value = item.get("content")
                compacted_item = dict(item)
                compacted_item["content"] = _OMITTED_PERSISTED_READ_CONTENT
                compacted_item["content_length"] = len(content_value) if isinstance(content_value, str) else None
                compacted_item["log_omitted"] = "persisted_file_read"
                compacted_content.append(compacted_item)
                changed = True
                continue

            if omit_skill_reference_result and not is_error:
                content_value = item.get("content")
                compacted_item = dict(item)
                compacted_item["content"] = _OMITTED_SKILL_REFERENCE_CONTENT
                compacted_item["content_length"] = len(content_value) if isinstance(content_value, str) else None
                compacted_item["log_omitted"] = "skill_reference_read"
                compacted_content.append(compacted_item)
                changed = True
                continue

            compacted_content.append(item)

        if not changed:
            return payload

        compacted_message = dict(message)
        compacted_message["content"] = compacted_content
        tool_use_result = compacted_message.get("tool_use_result")
        if isinstance(tool_use_result, dict):
            file_result = tool_use_result.get("file")
            if omit_skill_reference_result and isinstance(file_result, dict):
                compacted_file = dict(file_result)
                file_content = compacted_file.get("content")
                if isinstance(file_content, str):
                    compacted_file["content"] = _OMITTED_SKILL_REFERENCE_CONTENT
                    compacted_file["content_length"] = len(file_content)
                    compacted_file["log_omitted"] = "skill_reference_read"
                    compacted_result = dict(tool_use_result)
                    compacted_result["file"] = compacted_file
                    compacted_message["tool_use_result"] = compacted_result
                    tool_use_result = compacted_result
            if isinstance(file_result, dict):
                file_path = file_result.get("filePath")
                if isinstance(file_path, str) and self._is_persisted_read_path(file_path):
                    compacted_file = dict(file_result)
                    file_content = compacted_file.get("content")
                    if isinstance(file_content, str):
                        compacted_file["content"] = _OMITTED_PERSISTED_READ_CONTENT
                        compacted_file["content_length"] = len(file_content)
                        compacted_file["log_omitted"] = "persisted_file_read"
                        compacted_result = dict(tool_use_result)
                        compacted_result["file"] = compacted_file
                        compacted_message["tool_use_result"] = compacted_result
                        tool_use_result = compacted_result
            tool_use_id = tool_use_result.get("tool_use_id")
            is_error = tool_use_result.get("is_error") is True
            should_omit_result = (
                isinstance(tool_use_id, str) and tool_use_id in self._omitted_bash_read_tool_ids
            ) or (not isinstance(tool_use_id, str) and bool(omitted_tool_result_ids))
            if should_omit_result and not is_error:
                compacted_result = dict(tool_use_result)
                stdout = compacted_result.get("stdout")
                if isinstance(stdout, str):
                    compacted_result["stdout"] = _OMITTED_BASH_READ_CONTENT
                    compacted_result["stdout_length"] = len(stdout)
                    compacted_result["log_omitted"] = "bash_extract_window_output"
                    compacted_message["tool_use_result"] = compacted_result
        return {**payload, "message": compacted_message}

    def append(self, event: str, payload: dict[str, Any]) -> None:
        self._seq += 1
        if event == "message":
            payload = self._compact_message_payload(payload)
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
    extra_requirements: str = "",
) -> None:
    prompt = build_step1_agent_prompt(
        input_file=input_file,
        output_json=output_json,
        text_dir=text_dir,
        skill_path=skill_path,
        extra_requirements=extra_requirements,
    )
    options = ClaudeAgentOptions(
        cwd=repo_root,
        model=config.LLM_MODEL_STEP1,
        tools=STEP1_AGENT_TOOLS,
        allowed_tools=STEP1_AGENT_TOOLS,
        skills=[STEP1_AGENT_SKILL],
        permission_mode="acceptEdits",
        max_turns=300,
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
            "extra_requirements": extra_requirements,
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
    extra_requirements: str = "",
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
        extra_requirements=extra_requirements,
    )
    anyio.run(runner)
