"""
独立字数与Token估算脚本

功能：
- 读取 EPUB / PDF / TXT 文本
- 统计总字符数、中文字符数、英文字符数（含字母/数字/ASCII标点/空白）等
- 估算Token数量（按中英文分别估算）：
  - 中文：约 1 字符 ≈ 1 token
  - 英文：约 4 字符 ≈ 1 token（字母/数字/ASCII标点/空白累计）
- 可选：若已安装 tiktoken，可启用精确token计数（参考OpenAI编码器）

使用示例：
  # 交互式从 input/ 选择文件
  python check_text_stats.py --interactive

  # 直接指定文件
  python check_text_stats.py --input "/absolute/path/to/file.epub"
  python check_text_stats.py --input "/absolute/path/to/file.pdf" --use-tiktoken
  python check_text_stats.py --input "/absolute/path/to/file.txt" --encoding utf-8
"""

import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
import re
import math
import argparse
from typing import Tuple, Dict, Any


def _read_txt(file_path: str, encoding: str = "utf-8") -> Tuple[str, int]:
    with open(file_path, "r", encoding=encoding, errors="ignore") as f:
        text = f.read()
    return text, len(text)


def _read_document_any(file_path: str, encoding: str = "utf-8") -> Tuple[str, int]:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        return _read_txt(file_path, encoding=encoding)
    # 使用统一的文档读取器
    try:
        from core.domain.reader import DocumentReader
        reader = DocumentReader()
        return reader.read(file_path)
    except Exception as e:
        raise RuntimeError(f"读取文件失败: {e}")


def _count_categories(text: str) -> Dict[str, int]:
    # 基本分类统计
    zh_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    en_letters = len(re.findall(r"[A-Za-z]", text))
    digits = len(re.findall(r"\d", text))
    spaces = len(re.findall(r"\s", text))

    # ASCII 标点（string.punctuation 等价范围）
    ascii_punct = len(re.findall(r"[!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~]", text))

    total = len(text)
    other = total - zh_chars - en_letters - digits - spaces - ascii_punct

    return {
        "total": total,
        "zh_chars": zh_chars,
        "en_letters": en_letters,
        "digits": digits,
        "spaces": spaces,
        "ascii_punct": ascii_punct,
        "other": other if other >= 0 else 0,
    }


def _estimate_tokens(stats: Dict[str, int]) -> Dict[str, int]:
    # 中文：1 字符 ≈ 1 token
    zh_tokens = stats["zh_chars"]

    # 英文：约 4 字符 ≈ 1 token（将字母/数字/ASCII标点/空白都计入英文估算）
    en_chars_for_token = stats["en_letters"] + stats["digits"] + stats["ascii_punct"] + stats["spaces"]
    en_tokens = int(math.ceil(en_chars_for_token / 4.0))

    return {
        "tokens_zh_est": zh_tokens,
        "tokens_en_est": en_tokens,
        "tokens_total_est": zh_tokens + en_tokens,
    }


def _tiktoken_count(text: str, model: str = "cl100k_base") -> int:
    try:
        import tiktoken
    except Exception as e:
        raise RuntimeError(f"未安装 tiktoken：{e}")
    try:
        enc = tiktoken.get_encoding(model)
    except Exception:
        try:
            enc = tiktoken.get_encoding("cl100k_base")
        except Exception as ie:
            raise RuntimeError(f"tiktoken 编码器加载失败：{ie}")
    return len(enc.encode(text))


def analyze_file(file_path: str, encoding: str = "utf-8", use_tiktoken: bool = False, tiktoken_model: str = "cl100k_base") -> Dict[str, Any]:
    text, total_len = _read_document_any(file_path, encoding=encoding)
    stats = _count_categories(text)
    token_est = _estimate_tokens(stats)

    result: Dict[str, Any] = {
        "file": file_path,
        "total_chars": stats["total"],
        "zh_chars": stats["zh_chars"],
        "en_letters": stats["en_letters"],
        "digits": stats["digits"],
        "spaces": stats["spaces"],
        "ascii_punct": stats["ascii_punct"],
        "other_chars": stats["other"],
        **token_est,
    }

    if use_tiktoken:
        try:
            result["tokens_tiktoken"] = _tiktoken_count(text, model=tiktoken_model)
            result["tiktoken_model"] = tiktoken_model
        except Exception as e:
            result["tokens_tiktoken_error"] = str(e)

    return result


def _format_int(n: int) -> str:
    return f"{n:,}"


def main():
    parser = argparse.ArgumentParser(description="检查文档字数与Token估算（中英文区分）")
    parser.add_argument("--input", required=False, help="要分析的文件（支持 .epub / .pdf / .txt）")
    parser.add_argument("--interactive", action="store_true", help="从项目 input/ 目录交互式选择文件")
    parser.add_argument("--encoding", default="utf-8", help="TXT文件读取编码，默认 utf-8")
    parser.add_argument("--use-tiktoken", action="store_true", help="若已安装 tiktoken，则计算精确 token 数")
    parser.add_argument("--tiktoken-model", default="cl100k_base", help="tiktoken 编码器，默认 cl100k_base")
    args = parser.parse_args()

    file_path = args.input
    if args.interactive or not file_path:
        # 复用主项目交互式文件选择器
        try:
            from cli.ui_helpers import interactive_file_selector
            # tools/ 下脚本运行时，项目根目录为上一级
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            file_path = interactive_file_selector(input_dir=os.path.join(project_root, "input"))
        except Exception as e:
            print(f"❌ 交互式选择失败: {e}")
            raise SystemExit(1)
        if not file_path:
            print("👋 已取消")
            raise SystemExit(0)
    if not os.path.isabs(file_path):
        file_path = os.path.abspath(file_path)
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        raise SystemExit(1)

    try:
        res = analyze_file(
            file_path=file_path,
            encoding=args.encoding,
            use_tiktoken=args.use_tiktoken,
            tiktoken_model=args.tiktoken_model,
        )
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        raise SystemExit(2)

    print("\n" + "=" * 60)
    print("📊 文档字数与Token估算")
    print("=" * 60)
    print(f"文件: {res['file']}")
    print(f"总字符: {_format_int(res['total_chars'])}")
    print(f"中文字符: {_format_int(res['zh_chars'])}")
    print(f"英文字母: {_format_int(res['en_letters'])}")
    print(f"数字: {_format_int(res['digits'])}")
    print(f"ASCII标点: {_format_int(res['ascii_punct'])}")
    print(f"空白字符: {_format_int(res['spaces'])}")
    print(f"其他字符: {_format_int(res['other_chars'])}")
    print("-" * 60)
    print(f"估算Token（中文）: {_format_int(res['tokens_zh_est'])}")
    print(f"估算Token（英文）: {_format_int(res['tokens_en_est'])}")
    print(f"估算Token（合计）: {_format_int(res['tokens_total_est'])}")
    if 'tokens_tiktoken' in res:
        model = res.get('tiktoken_model', 'cl100k_base')
        print(f"tiktoken计数（{model}）: {_format_int(res['tokens_tiktoken'])}")
    elif 'tokens_tiktoken_error' in res:
        print(f"tiktoken计数失败: {res['tokens_tiktoken_error']}")
    print("=" * 60)


if __name__ == "__main__":
    main()


