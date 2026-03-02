"""CLI-owned input/output directory scanning and selection helpers."""

import datetime
import os
from pathlib import Path
from typing import Any, Dict, List

from core.shared import FileProcessingError, get_file_info, logger


def _resolve_cli_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    project_root = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(project_root, path)


def scan_input_files(input_dir: str = "input") -> List[Dict[str, Any]]:
    """Scan CLI input directory for supported document files."""
    input_dir = _resolve_cli_path(input_dir)
    if not os.path.exists(input_dir):
        logger.warning(f"输入目录不存在: {input_dir}")
        return []

    supported_extensions = [".pdf", ".epub", ".mobi", ".azw3"]
    files: List[Dict[str, Any]] = []
    logger.info(f"CLI 正在扫描输入目录: {input_dir}")

    try:
        for file_name in os.listdir(input_dir):
            file_path = os.path.join(input_dir, file_name)
            if os.path.isdir(file_path):
                continue
            extension = Path(file_path).suffix.lower()
            if extension in supported_extensions:
                files.append(get_file_info(file_path))
    except Exception as exc:
        logger.error(f"扫描输入目录失败: {exc}")
        raise FileProcessingError(f"扫描输入目录失败: {exc}")

    files.sort(key=lambda item: item["modified_time"], reverse=True)
    return files


def scan_output_projects(output_dir: str = "output") -> List[Dict[str, Any]]:
    """Scan CLI output directory for existing projects."""
    output_dir = _resolve_cli_path(output_dir)
    projects: List[Dict[str, Any]] = []

    if not os.path.exists(output_dir):
        return projects

    try:
        for entry in os.listdir(output_dir):
            path = os.path.join(output_dir, entry)
            if not os.path.isdir(path):
                continue
            text_dir = os.path.join(path, "text")
            if os.path.isdir(text_dir):
                stat = os.stat(path)
                projects.append(
                    {
                        "path": path,
                        "name": entry,
                        "modified_time": datetime.datetime.fromtimestamp(stat.st_mtime),
                    }
                )
    except Exception as exc:
        logger.warning(f"扫描输出目录失败: {exc}")
        return []

    projects.sort(key=lambda item: item["modified_time"], reverse=True)
    return projects


__all__ = ["scan_input_files", "scan_output_projects"]
