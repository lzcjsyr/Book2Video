"""Pure subtitle text and timing logic."""

import re
import unicodedata
from typing import List


def calculate_mixed_length(text: str) -> float:
    """计算混合中英文本的等效长度。"""
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    english_words = len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*", text))
    numbers = len(re.findall(r"\d", text))

    ascii_alpha = re.compile(r"[A-Za-z]")
    cjk_pattern = re.compile(r"[\u4e00-\u9fff]")
    other_letters = 0
    for ch in text:
        if cjk_pattern.match(ch):
            continue
        if ascii_alpha.match(ch):
            continue
        if unicodedata.category(ch).startswith("L"):
            other_letters += 1

    return chinese_chars * 1.0 + english_words * 1.5 + numbers * 1.0 + other_letters * 1.0


def calculate_subtitle_durations(subtitle_texts: List[str], total_duration: float) -> List[float]:
    """按字幕文本等效长度分配显示时长。"""
    if len(subtitle_texts) == 0:
        return [total_duration]

    lengths = [max(1.0, calculate_mixed_length(t)) for t in subtitle_texts]
    total_len = sum(lengths)
    line_durations = []
    acc = 0.0

    for idx, length in enumerate(lengths):
        if idx < len(lengths) - 1:
            duration = total_duration * (length / total_len)
            line_durations.append(duration)
            acc += duration
        else:
            line_durations.append(max(0.0, total_duration - acc))

    return line_durations


def split_text_for_subtitle(text: str, max_chars_per_line: int = 20, max_lines: int = 2) -> List[str]:
    """将长文本分割为适合字幕显示的短句，同时保护成对符号。"""
    del max_lines  # 保持旧接口；当前逻辑返回完整行序列。

    if len(text) <= max_chars_per_line:
        return [text]

    pair_markers = {
        "《": "》",
        '"': '"',
    }

    protected_ranges = _find_protected_pair_ranges(text, pair_markers, max_chars_per_line)

    def is_protected(pos: int) -> bool:
        for start, end in protected_ranges:
            if start < pos <= end:
                return True
        return False

    heavy_punctuation = ["。", "！", "？", "!", "?", "，", ",", "；", ";", ":", "：", "——", " "]
    segments = []
    current_segment = ""

    for i, char in enumerate(text):
        current_segment += char
        if char in heavy_punctuation and not is_protected(i):
            if current_segment.strip():
                segments.append(current_segment.strip())
            current_segment = ""

    if current_segment.strip():
        segments.append(current_segment.strip())

    final_parts = []
    for segment in segments:
        if len(segment) <= max_chars_per_line:
            final_parts.append(segment)
        else:
            seg_protected = _find_protected_pair_ranges(segment, pair_markers, max_chars_per_line)
            final_parts.extend(_split_with_protection(segment, seg_protected, max_chars_per_line))

    return final_parts


def _split_with_protection(text: str, protected_ranges: List[tuple], max_chars: int) -> List[str]:
    if len(text) <= max_chars:
        return [text]

    if not protected_ranges:
        return _split_without_protection(text, max_chars)

    sorted_ranges = sorted(protected_ranges, key=lambda x: x[0])
    parts = []
    last_end = 0

    for start, end in sorted_ranges:
        if start > last_end:
            before_text = text[last_end:start]
            if before_text.strip():
                parts.append(("unprotected", before_text))

        protected_text = text[start:end + 1]
        parts.append(("protected", protected_text))
        last_end = end + 1

    if last_end < len(text):
        after_text = text[last_end:]
        if after_text.strip():
            parts.append(("unprotected", after_text))

    result = []
    current_line = ""

    for part_type, part_text in parts:
        if part_type == "protected":
            if len(current_line) + len(part_text) <= max_chars:
                current_line += part_text
            else:
                if current_line.strip():
                    result.extend(_split_without_protection(current_line, max_chars))
                current_line = part_text
        else:
            combined = current_line + part_text
            if len(combined) <= max_chars:
                current_line = combined
            else:
                if current_line.strip():
                    split_result = _split_at_punctuation(current_line + part_text, max_chars)
                    result.extend(split_result[:-1])
                    current_line = split_result[-1] if split_result else ""
                else:
                    split_result = _split_at_punctuation(part_text, max_chars)
                    result.extend(split_result[:-1])
                    current_line = split_result[-1] if split_result else ""

    if current_line.strip():
        if len(current_line) <= max_chars:
            result.append(current_line)
        else:
            result.extend(_split_without_protection(current_line, max_chars))

    return [r for r in result if r.strip()]


def _split_at_punctuation(text: str, max_chars: int) -> List[str]:
    if len(text) <= max_chars:
        return [text]

    light_punctuation = ["、", ";", "；", "，", ",", "。", "！", "？", "!", "?", "：", ":"]
    result = []
    current = ""

    for char in text:
        current += char
        if char in light_punctuation and len(current) >= max_chars * 0.5:
            result.append(current)
            current = ""

    if current:
        result.append(current)

    final_result = []
    for part in result:
        if len(part) <= max_chars:
            final_result.append(part)
        else:
            final_result.extend(_split_text_evenly(part, max_chars))

    return final_result


def _split_without_protection(text: str, max_chars: int) -> List[str]:
    if len(text) <= max_chars:
        return [text]

    result = _split_at_punctuation(text, max_chars)
    if all(len(r) <= max_chars for r in result):
        return result

    return _split_text_evenly(text, max_chars)


def _find_protected_pair_ranges(text: str, pair_markers: dict, max_chars: int) -> List[tuple]:
    protected_ranges = []
    stack = []

    for i, char in enumerate(text):
        if char in pair_markers:
            stack.append((char, i))
        elif stack:
            open_char, open_pos = stack[-1]
            if char == pair_markers[open_char]:
                stack.pop()
                pair_len = i - open_pos + 1
                if pair_len <= max_chars:
                    protected_ranges.append((open_pos, i))

    return protected_ranges


def _split_text_evenly(text: str, max_chars_per_line: int) -> List[str]:
    if len(text) <= max_chars_per_line:
        return [text]

    total_chars = len(text)
    num_segments = (total_chars + max_chars_per_line - 1) // max_chars_per_line

    base_length = total_chars // num_segments
    remainder = total_chars % num_segments

    result = []
    start = 0

    for i in range(num_segments):
        length = base_length + (1 if i < remainder else 0)
        end = start + length
        result.append(text[start:end])
        start = end

    return result
