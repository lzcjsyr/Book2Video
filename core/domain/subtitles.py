"""Pure subtitle text and timing logic."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import re
import unicodedata
from typing import Callable, List

try:
    import jieba

    jieba.setLogLevel(40)
except ImportError:  # 兼容尚未更新依赖的旧安装环境。
    jieba = None


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


_DISPLAY_PAIR_MARKS = set('"“”《》〈〉')


def format_subtitle_display_text(text: str) -> str:
    """仅保留双引号和书名号，其余标点统一替换为单个空格。"""
    value = unicodedata.normalize("NFC", str(text or ""))
    _, roles = _find_pair_ranges_and_roles(value)
    result: list[str] = []
    pending_space = False

    for index, char in enumerate(value):
        if char in _DISPLAY_PAIR_MARKS:
            role = roles.get(index)
            if role == "close":
                while result and result[-1] == " ":
                    result.pop()
                result.append(char)
                pending_space = False
                continue
            if pending_space and result and result[-1] != " ":
                result.append(" ")
            result.append(char)
            pending_space = False
            continue

        category = unicodedata.category(char)
        if char.isspace() or category.startswith("P"):
            pending_space = True
            continue

        if pending_space and result and result[-1] not in {'"', "“", "《", "〈", " "}:
            result.append(" ")
        result.append(char)
        pending_space = False

    return "".join(result).strip()


_ASYMMETRIC_PAIRS = {
    "《": "》",
    "〈": "〉",
    "“": "”",
    "‘": "’",
    "「": "」",
    "『": "』",
    "（": "）",
    "(": ")",
    "【": "】",
    "[": "]",
    "{": "}",
}
_SYMMETRIC_QUOTES = {'"', "'"}
_STRONG_END = set("。！？!?…")
_MEDIUM_END = set("，,；;：:")
_TRAILING_PUNCTUATION = set("。！？!?…，,；;：:、—-）)]}》〉」』”’")


@dataclass(frozen=True)
class _Token:
    text: str
    role: str = "text"  # text / open / close / protected / space

    @property
    def width(self) -> int:
        return len(self.text)


def split_text_for_subtitle(
    text: str,
    max_chars_per_line: int = 20,
    max_lines: int = 2,
    display_formatter: Callable[[str], str] | None = None,
) -> List[str]:
    """按中文阅读节奏切分字幕，并尽可能让成对符号留在同一条字幕中。

    ``max_lines`` 仅为兼容旧接口保留；步骤 5 一次只显示一条字幕。短书名、
    引语和括注会作为不可拆 token，长到无法安全放进画面的成对内容则在内部按
    标点切分，同时保证开符号不悬在行尾、闭符号不孤立在下一行。
    """
    del max_lines

    normalized = _normalize_subtitle_text(text)
    if not normalized:
        return []

    limit = max(1, int(max_chars_per_line or 1))

    @lru_cache(maxsize=None)
    def display_width(value: str) -> int:
        rendered = display_formatter(value) if display_formatter else value
        return len(rendered)

    if display_width(normalized) <= limit:
        return [normalized]
    if re.fullmatch(r"[A-Za-z0-9]+", normalized):
        return _split_text_evenly(normalized, limit)

    pairs, roles = _find_pair_ranges_and_roles(normalized)
    # 允许短成对内容比普通行略宽 10%，但最多只溢出 2 个字符。这样可避免
    # 《书名》或一句短引语被生硬拆开，同时仍给放大后的字幕保留画面安全边距。
    protected_limit = limit + min(2, max(1, round(limit * 0.10)))
    eligible_pairs = [
        (start, end)
        for start, end in pairs
        if display_width(normalized[start : end + 1]) <= protected_limit
    ]
    protected_by_start = dict(_select_outermost_ranges(eligible_pairs))
    tokens = _tokenize(normalized, protected_by_start, roles, limit)
    lines = _wrap_tokens(tokens, limit, protected_limit, display_width)
    return [line.strip() for line in lines if line.strip()]


def _normalize_subtitle_text(text: str) -> str:
    value = unicodedata.normalize("NFC", str(text or ""))
    value = re.sub(r"[\t\r\n\u3000 ]+", " ", value)
    # 中文标点前不保留空格；中文字符之间的误插空格也移除。
    value = re.sub(r"\s+([，。！？；：、…》〉」』”’）】\]])", r"\1", value)
    value = re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", value)
    return value.strip()


def _find_pair_ranges_and_roles(text: str) -> tuple[list[tuple[int, int]], dict[int, str]]:
    pairs: list[tuple[int, int]] = []
    roles: dict[int, str] = {}
    stack: list[tuple[str, str, int]] = []

    for index, char in enumerate(text):
        if char in _SYMMETRIC_QUOTES:
            # 英文单词中的 apostrophe（don't / user's）不是引号。
            if (
                char == "'"
                and index > 0
                and index + 1 < len(text)
                and text[index - 1].isalnum()
                and text[index + 1].isalnum()
            ):
                continue
            if stack and stack[-1][0] == char and stack[-1][1] == char:
                _, _, start = stack.pop()
                pairs.append((start, index))
                roles[start] = "open"
                roles[index] = "close"
            else:
                stack.append((char, char, index))
                roles[index] = "open"
            continue

        if char in _ASYMMETRIC_PAIRS:
            stack.append((char, _ASYMMETRIC_PAIRS[char], index))
            roles[index] = "open"
            continue

        matching_stack_index = next(
            (i for i in range(len(stack) - 1, -1, -1) if stack[i][1] == char),
            None,
        )
        if matching_stack_index is None:
            continue
        _, _, start = stack.pop(matching_stack_index)
        pairs.append((start, index))
        roles[start] = "open"
        roles[index] = "close"

    return sorted(pairs), roles


def _select_outermost_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    selected: list[tuple[int, int]] = []
    for start, end in sorted(ranges, key=lambda item: (item[0], -item[1])):
        if any(parent_start <= start and end <= parent_end for parent_start, parent_end in selected):
            continue
        selected.append((start, end))
    return selected


def _tokenize(
    text: str,
    protected_by_start: dict[int, int],
    roles: dict[int, str],
    limit: int,
) -> list[_Token]:
    tokens: list[_Token] = []
    index = 0
    while index < len(text):
        protected_end = protected_by_start.get(index)
        if protected_end is not None:
            tokens.append(_Token(text[index : protected_end + 1], "protected"))
            index = protected_end + 1
            continue

        char = text[index]
        if char.isspace():
            if tokens and tokens[-1].role != "space":
                tokens.append(_Token(" ", "space"))
            index += 1
            continue

        if _is_cjk(char):
            match = re.match(r"[\u3400-\u9fff]+", text[index:])
            if match:
                cjk_run = match.group(0)
                words = list(jieba.cut(cjk_run, cut_all=False, HMM=True)) if jieba else list(cjk_run)
                for word in words:
                    if len(word) <= limit:
                        tokens.append(_Token(word))
                    else:
                        tokens.extend(_Token(piece) for piece in word)
                index += len(cjk_run)
                continue

        # 完整英文/数字词优先不拆；超长词再按字符降级，避免单个 token 溢出。
        if char.isascii() and char.isalnum():
            match = re.match(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*", text[index:])
            if match:
                word = match.group(0)
                if len(word) <= limit:
                    tokens.append(_Token(word))
                else:
                    tokens.extend(_Token(piece) for piece in word)
                index += len(word)
                continue

        tokens.append(_Token(char, roles.get(index, "text")))
        index += 1
    return tokens


_BAD_LINE_START_WORDS = {"的", "地", "得", "了", "着", "过", "吗", "呢", "吧", "啊", "呀", "嘛", "之", "是", "和", "与", "及", "或"}
_BAD_LINE_END = set("的地得把被给让向从在对将和与及或但而却")
_BAD_LINE_END_WORDS = {
    "是", "有", "在", "从", "对", "向", "把", "被", "给", "让", "将", "为",
    "和", "与", "及", "或", "但", "而", "却", "都", "也", "又", "更", "最",
    "很", "能", "会", "要", "因", "由", "像",
}
_MEASURE_WORDS = set(
    "个位名条件本部章节句字种次年月天秒元块倍成分点项份家所座台辆张页篇门届期场轮颗枚只头匹艘架层套组批排行列封首"
)
_CHINESE_NUMERALS = set("零〇一二两三四五六七八九十百千万亿几多半")


def _wrap_tokens(
    tokens: list[_Token],
    limit: int,
    protected_limit: int,
    display_width: Callable[[str], int],
) -> list[str]:
    """用全局动态规划选择断点，避免局部贪心制造短尾或拆散中文短语。"""
    hard_boundaries = [0]
    clause_threshold = max(6, round(limit * 0.33))
    for boundary in range(1, len(tokens)):
        if not _is_legal_boundary(tokens, boundary):
            continue
        if _ends_strong_sentence(tokens, boundary):
            hard_boundaries.append(boundary)
            continue
        if _ends_medium_clause(tokens, boundary):
            current_clause = "".join(token.text for token in tokens[hard_boundaries[-1] : boundary])
            next_clause = _next_clause_text(tokens, boundary)
            if (
                display_width(current_clause) >= clause_threshold
                and display_width(next_clause) >= clause_threshold
            ):
                hard_boundaries.append(boundary)
    hard_boundaries.append(len(tokens))

    lines: list[str] = []
    for start, end in zip(hard_boundaries, hard_boundaries[1:]):
        lines.extend(_wrap_token_group(tokens[start:end], limit, protected_limit, display_width))
    return lines


def _wrap_token_group(
    tokens: list[_Token],
    limit: int,
    protected_limit: int,
    display_width: Callable[[str], int],
) -> list[str]:
    """在一个完整句子内用全局动态规划选择最自然的断点。"""
    token_count = len(tokens)
    raw_ranges: dict[tuple[int, int], str] = {}

    def raw_text(start: int, end: int) -> str:
        key = (start, end)
        if key not in raw_ranges:
            raw_ranges[key] = "".join(token.text for token in tokens[start:end]).strip()
        return raw_ranges[key]

    # 每个状态保存：(行数, 总惩罚, 断点列表)。先保证行数最少，再比较阅读质量。
    best: list[tuple[int, float, list[int]] | None] = [None] * (token_count + 1)
    best[0] = (0, 0.0, [])

    for start in range(token_count):
        state = best[start]
        if state is None:
            continue
        if tokens[start].role == "space":
            candidate = (state[0], state[1], state[2] + [start + 1])
            if best[start + 1] is None or candidate[:2] < best[start + 1][:2]:
                best[start + 1] = candidate
            continue

        for end in range(start + 1, token_count + 1):
            segment = raw_text(start, end)
            width = display_width(segment)
            protected_positions = [
                index for index in range(start, end) if tokens[index].role == "protected"
            ]
            last_token = tokens[end - 1]
            leading_protected = bool(protected_positions) and all(
                token.role in {"open", "space"}
                for token in tokens[start : protected_positions[0]]
            )
            allowance = protected_limit if leading_protected else limit
            if leading_protected and (
                last_token.role == "close" or last_token.text[-1:] in _TRAILING_PUNCTUATION
            ):
                allowance += 1
            if width > allowance:
                # display_width 对尾部标点可能不单调，继续看完紧邻的标点 token。
                if last_token.text[-1:] not in _TRAILING_PUNCTUATION:
                    break
                continue
            if end < token_count and not _is_legal_boundary(tokens, end):
                continue

            line_count = state[0] + 1
            penalty = state[1] + _line_penalty(tokens, start, end, width, limit, end == token_count)
            candidate = (line_count, penalty, state[2] + [end])
            current = best[end]
            if current is None or candidate[:2] < current[:2]:
                best[end] = candidate

    final = best[token_count]
    if final is None:
        # 极端输入（如单个超长保护 token）仍保证不丢字。
        return [raw_text(index, index + 1) for index in range(token_count) if raw_text(index, index + 1)]

    lines: list[str] = []
    start = 0
    for end in final[2]:
        value = raw_text(start, end)
        if value:
            lines.append(value)
        start = end
    return lines


def _ends_strong_sentence(tokens: list[_Token], boundary: int) -> bool:
    tail = "".join(token.text for token in tokens[max(0, boundary - 4) : boundary]).rstrip()
    tail = tail.rstrip("》〉”’」』）)】]}")
    return tail[-1:] in _STRONG_END


def _ends_medium_clause(tokens: list[_Token], boundary: int) -> bool:
    tail = "".join(token.text for token in tokens[max(0, boundary - 2) : boundary]).rstrip()
    return tail[-1:] in "，,；;"


def _next_clause_text(tokens: list[_Token], boundary: int) -> str:
    end = boundary
    while end < len(tokens):
        end += 1
        if _ends_strong_sentence(tokens, end) or _ends_medium_clause(tokens, end):
            break
    return "".join(token.text for token in tokens[boundary:end])


def _is_legal_boundary(tokens: list[_Token], boundary: int) -> bool:
    left = tokens[boundary - 1]
    right = tokens[boundary]
    if left.role == "open" or right.role == "close":
        return False
    if right.text[:1] in _TRAILING_PUNCTUATION:
        return False
    return True


def _line_penalty(
    tokens: list[_Token],
    start: int,
    end: int,
    width: int,
    limit: int,
    is_final: bool,
) -> float:
    """越低越好：优先语义标点，其次行宽均衡，并惩罚中文禁忌断点。"""
    fill = min(width, limit) / max(1, limit)
    penalty = (1.0 - fill) ** 2 * (18 if is_final else 34)
    if width <= max(2, round(limit * 0.25)):
        penalty += 55
    elif width < round(limit * 0.45):
        penalty += 18

    if end >= len(tokens):
        return penalty

    left_text = tokens[end - 1].text.rstrip()
    right_text = tokens[end].text.lstrip()
    left_char = left_text[-1:] if left_text else ""
    right_char = right_text[:1] if right_text else ""

    if left_char in _STRONG_END:
        penalty -= 50
    elif left_char in _MEDIUM_END:
        penalty -= 34
    elif left_char in "—-、" or tokens[end - 1].role == "space":
        penalty -= 24
    elif tokens[end].role == "protected":
        penalty -= 10

    if left_char in _BAD_LINE_END or left_text in _BAD_LINE_END_WORDS:
        penalty += 70
    if right_text in _BAD_LINE_START_WORDS:
        penalty += 70
    if _splits_number_measure_phrase(tokens, end):
        penalty += 120
    return penalty


def _splits_number_measure_phrase(tokens: list[_Token], boundary: int) -> bool:
    """识别“三｜个字”和“三个｜字”一类中文数量短语断裂。"""
    left = "".join(token.text for token in tokens[max(0, boundary - 4) : boundary])
    right = "".join(token.text for token in tokens[boundary : min(len(tokens), boundary + 3)])
    if not left or not right:
        return False
    if left[-1] in _CHINESE_NUMERALS or left[-1].isdigit():
        return right[0] in _MEASURE_WORDS
    if left[-1] in _MEASURE_WORDS:
        prefix = left[:-1]
        return bool(prefix) and (prefix[-1] in _CHINESE_NUMERALS or prefix[-1].isdigit()) and _is_cjk(right[0])
    return False


def _is_cjk(char: str) -> bool:
    return bool(char) and "\u3400" <= char <= "\u9fff"


def _find_protected_pair_ranges(text: str, pair_markers: dict, max_chars: int) -> List[tuple]:
    """兼容旧的私有辅助函数，并修复直引号无法闭合的问题。"""
    pairs, _ = _find_pair_ranges_and_roles(text)
    return [
        (start, end)
        for start, end in pairs
        if text[start] in pair_markers
        and pair_markers[text[start]] == text[end]
        and end - start + 1 <= max_chars
    ]


def _split_text_evenly(text: str, max_chars_per_line: int) -> List[str]:
    """兼容旧调用：均衡切分，避免最后只剩一两个字符。"""
    if len(text) <= max_chars_per_line:
        return [text]
    segment_count = (len(text) + max_chars_per_line - 1) // max_chars_per_line
    base_length, remainder = divmod(len(text), segment_count)
    result = []
    start = 0
    for index in range(segment_count):
        length = base_length + (1 if index < remainder else 0)
        result.append(text[start : start + length])
        start += length
    return result
