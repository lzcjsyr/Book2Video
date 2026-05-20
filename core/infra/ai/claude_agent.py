from __future__ import annotations

from functools import partial
from pathlib import Path

import anyio
from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from core.prompts import build_step1_agent_prompt


STEP1_AGENT_TOOLS = ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Skill"]
STEP1_AGENT_SKILL = "video-book-direct-read"


async def _run_step1_agent_async(
    *,
    input_file: str,
    output_json: str,
    extract_path: str,
    num_segments: int,
    skill_path: str,
    repo_root: str,
) -> None:
    prompt = build_step1_agent_prompt(
        input_file=input_file,
        output_json=output_json,
        extract_path=extract_path,
        num_segments=num_segments,
        skill_path=skill_path,
    )
    options = ClaudeAgentOptions(
        cwd=repo_root,
        tools=STEP1_AGENT_TOOLS,
        allowed_tools=STEP1_AGENT_TOOLS,
        skills=[STEP1_AGENT_SKILL],
        permission_mode="acceptEdits",
        max_turns=80,
        setting_sources=["user", "project", "local"],
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
    num_segments: int,
    skill_path: str,
    repo_root: str,
) -> None:
    runner = partial(
        _run_step1_agent_async,
        input_file=input_file,
        output_json=output_json,
        extract_path=extract_path,
        num_segments=num_segments,
        skill_path=skill_path,
        repo_root=repo_root,
    )
    anyio.run(runner)
