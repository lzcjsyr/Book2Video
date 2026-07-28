#!/usr/bin/env python3
"""Validate the exact Step 1 raw.json contract for Book2Video."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


REQUIRED_FIELDS = {
    "source_name",
    "video_titles",
    "cover_titles",
    "cover_subtitles",
    "golden_quotes",
    "content",
    "total_length",
}
THREE_ITEM_FIELDS = {
    "video_titles",
    "cover_titles",
    "cover_subtitles",
    "golden_quotes",
}


def validate(raw_path: Path, draft_path: Path | None = None) -> dict:
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("raw JSON 顶层必须是对象")
    if set(data) != REQUIRED_FIELDS:
        missing = sorted(REQUIRED_FIELDS - set(data))
        extra = sorted(set(data) - REQUIRED_FIELDS)
        raise ValueError(f"字段集合错误；缺少={missing}，多余={extra}")

    source_name = data["source_name"]
    if (
        not isinstance(source_name, str)
        or not source_name.startswith("《")
        or not source_name.endswith("》")
        or not source_name[1:-1].strip()
    ):
        raise ValueError("source_name 必须是带书名号的非空字符串")
    if re.search(r"\.(pdf|epub|docx?|txt|mobi|azw3)》$", source_name, re.IGNORECASE):
        raise ValueError("source_name 不得包含文件扩展名")

    for field in THREE_ITEM_FIELDS:
        values = data[field]
        if not isinstance(values, list) or len(values) != 3:
            raise ValueError(f"{field} 必须是正好包含3项的数组")
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError(f"{field} 的每一项都必须是非空字符串")
        if len(set(values)) != 3:
            raise ValueError(f"{field} 的3项不得重复")

    content = data["content"]
    if not isinstance(content, str) or not content.strip():
        raise ValueError("content 必须是非空字符串")
    if not 950 <= len(content) <= 1150:
        raise ValueError("content 长度必须在950到1150字符之间")
    if not isinstance(data["total_length"], int) or isinstance(data["total_length"], bool):
        raise ValueError("total_length 必须是整数")
    if data["total_length"] != len(content):
        raise ValueError("total_length 必须等于 Python len(content)")
    if any(len(value) > 10 for value in data["cover_titles"]):
        raise ValueError("cover_titles 每项不得超过10字符")
    if any(len(value) > 15 for value in data["cover_subtitles"]):
        raise ValueError("cover_subtitles 每项不得超过15字符")

    if draft_path is not None:
        draft = draft_path.read_text(encoding="utf-8").strip()
        if content != draft:
            raise ValueError("content 必须与 _draft_final.txt 完全一致")
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_json", type=Path)
    parser.add_argument("--draft", type=Path)
    args = parser.parse_args()
    validate(args.raw_json, args.draft)
    print("raw.json contract valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
