from __future__ import annotations

from functools import partial
from pathlib import Path

import anyio
from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from core.config import config
from core.prompts import build_step1_agent_prompt


STEP1_AGENT_TOOLS = ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Skill"]
STEP1_AGENT_SKILL = "video-book-direct-read"


def build_step1_agent_env() -> dict[str, str]:
    api_key = (config.MIMO_API_KEY or "").strip()
    if not api_key:
        raise RuntimeError("步骤1需要 MIMO_API_KEY（.env），用于驱动 Claude Agent SDK")
    return {
        "ANTHROPIC_BASE_URL": config.LLM_BASE_URL_STEP1,
        "ANTHROPIC_API_KEY": api_key,
        "ANTHROPIC_MODEL": config.LLM_MODEL_STEP1,
    }


async def _run_step1_agent_async(
    *,
    input_file: str,
    output_json: str,
    extract_path: str,
    coverage_ledger_path: str,
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
        max_turns=80,
        env=build_step1_agent_env(),
    )

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage):
            if message.is_error:
                raise RuntimeError(message.result or "Claude Agent Step 1 failed")
            break

    if not Path(output_json).exists():
        raise FileNotFoundError(f"Claude Agent未生成raw.json: {output_json}")


def run_step1_agent(
    *,
    input_file: str,
    output_json: str,
    extract_path: str,
    coverage_ledger_path: str,
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
        text_dir=text_dir,
        num_segments=num_segments,
        skill_path=skill_path,
        repo_root=repo_root,
    )
    anyio.run(runner)
