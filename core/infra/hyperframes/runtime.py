"""Shared HyperFrames runtime configuration."""

import os
from pathlib import Path

HYPERFRAMES_VERSION = "hyperframes@0.7.10"


def parse_size(size: str) -> tuple[int, int]:
    raw = (
        (size or "1280x720")
        .lower()
        .replace(" ", "")
        .replace("×", "x")
        .replace("*", "x")
    )
    width, height = raw.split("x", 1)
    return int(width), int(height)


def subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    path_parts = [
        "/opt/homebrew/bin",
        "/usr/local/bin",
        str(Path.home() / ".nvm/versions/node/v22.22.3/bin"),
        str(Path.home() / ".nvm/versions/node/v22.22.2/bin"),
    ]
    current_path = env.get("PATH", "")
    env["PATH"] = os.pathsep.join(
        [*path_parts, current_path] if current_path else path_parts
    )
    return env
