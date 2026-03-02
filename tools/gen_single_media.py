import os
import sys
import datetime
import requests
from urllib.parse import urlparse
from io import BytesIO
from PIL import Image, UnidentifiedImageError

# Ensure project root is on sys.path when running from tools/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.infra.ai import text_to_image_doubao, text_to_image_siliconflow, text_to_audio_bytedance


def ensure_temp_dir(project_root: str) -> str:
    temp_dir = os.path.join(project_root, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def sanitize_filename(name: str) -> str:
    # 保留常见安全字符；其余替换为下划线
    safe_chars = "-_().（）[]【】{}，。、“”‘’ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(ch if (ch.isalnum() or ch in safe_chars) else "_" for ch in name)


def is_valid_http_url(url: str) -> bool:
    """Basic validation to ensure we got a usable http(s) URL."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def first_n_chars(text: str, n: int) -> str:
    text = text.strip()
    return text[:n] if len(text) > n else text


def build_filename(prompt: str, ext: str) -> str:
    prefix_raw = first_n_chars(prompt, 6)
    prefix = sanitize_filename(prefix_raw).strip(" _") or "untitled"
    # 使用 月日_时分，与现有项目时间后缀风格保持一致
    # 扩展到包含秒，降低同一分钟内的重名概率
    time_suffix = datetime.datetime.now().strftime("%m%d_%H%M%S")
    return f"{prefix}_{time_suffix}{ext}"


def read_document(file_path: str) -> str:
    """
    读取文档内容，使用统一的DocumentReader
    """
    from core.domain.reader import DocumentReader
    reader = DocumentReader()
    content, _ = reader.read(file_path)
    return content


def get_text_input() -> str:
    print("\n请选择文字输入方式：")
    print("  1) 直接输入")
    print("  2) 从文档读取")
    
    while True:
        choice = input("请输入选项 (1/2): ").strip()
        if choice in ("1", "2"):
            break
        print("无效输入，请输入 1 或 2。")
    
    if choice == "1":
        text = input("\n请输入文字内容：").strip()
        if not text:
            raise ValueError("文字内容不能为空")
        return text
    else:
        while True:
            file_path = input("\n请输入文档路径：").strip()
            
            # 处理空路径或引号包围的路径
            if not file_path:
                print("❌ 文档路径不能为空。")
                continue
                
            # 移除可能的引号
            if (file_path.startswith('"') and file_path.endswith('"')) or \
               (file_path.startswith("'") and file_path.endswith("'")):
                file_path = file_path[1:-1].strip()
                
            # 再次检查去除引号后是否为空
            if not file_path:
                print("❌ 文档路径不能为空。")
                continue
            
            try:
                text = read_document(file_path)  # 使用本地定义的函数
                print(f"✅ 成功读取文档，文字长度：{len(text)} 字符")
                preview = first_n_chars(text, 100)
                print(f"内容预览：{preview}{'...' if len(text) > 100 else ''}")
                return text
            except (ValueError, FileNotFoundError) as e:
                print(f"❌ 文件路径问题：{e}")
                retry = input("是否重新输入文档路径？(y/n): ").strip().lower()
                if retry != 'y':
                    raise RuntimeError("用户取消文档读取")
            except Exception as e:
                print(f"❌ 读取文档失败：{e}")
                retry = input("是否重新输入文档路径？(y/n): ").strip().lower()
                if retry != 'y':
                    raise RuntimeError("用户取消文档读取")


def get_multiline_prompt(prompt_text: str = "请输入图片提示词") -> str:
    """
    支持多行输入的提示词获取函数

    用户可以选择逐行输入或粘贴模式

    逐行输入模式：
    1. 输入空行结束
    2. 输入 END 结束
    3. 按 Ctrl+D (macOS/Linux) 或 Ctrl+Z (Windows) 结束

    粘贴模式：
    1. 直接粘贴多行文本
    2. 输入 END（单独一行）结束
    3. 按 Ctrl+D (macOS/Linux) 或 Ctrl+Z (Windows) 结束

    Args:
        prompt_text: 提示文本

    Returns:
        str: 完整的多行文本
    """
    print(f"\n{'='*60}")
    print(f"📝 {prompt_text}")
    print(f"{'='*60}")
    print("请选择输入模式：")
    print("  1) 逐行输入模式（每输入一行按回车，空行结束）")
    print("  2) 粘贴模式（粘贴多行文本，输入END或Ctrl+D结束）")
    print(f"{'='*60}\n")

    while True:
        mode = input("请选择模式 (1/2): ").strip()
        if mode in ("1", "2"):
            break
        print("无效输入，请输入 1 或 2")

    print()

    if mode == "1":
        return _get_input_line_by_line()
    else:
        return _get_input_paste_mode(prompt_text)


def _get_input_line_by_line() -> str:
    """逐行输入模式"""
    print("💡 逐行输入模式：")
    print("  • 每输入一行按回车继续")
    print("  • 输入空行或 'END' 结束")
    print("  • 输入 'CANCEL' 取消操作")
    print()

    lines = []
    line_number = 1

    try:
        while True:
            try:
                line = input(f"[第{line_number}行] ")

                # 检查取消命令
                if line.strip().upper() == "CANCEL":
                    print("\n❌ 已取消输入")
                    raise KeyboardInterrupt

                # 检查结束命令
                if line.strip().upper() == "END":
                    break

                # 空行结束
                if not line.strip() and lines:
                    break

                # 如果是第一行且为空，提示重新输入
                if not line.strip() and not lines:
                    print("⚠️  第一行不能为空，请输入内容")
                    continue

                lines.append(line)
                line_number += 1

            except EOFError:
                break

    except KeyboardInterrupt:
        raise RuntimeError("用户取消输入")

    result = "\n".join(lines).strip()

    if not result:
        raise ValueError("提示词不能为空")

    _show_input_preview(result, len(lines))
    return result


def _get_input_paste_mode(prompt_text: str) -> str:
    """粘贴模式：一次性粘贴多行文本"""
    print("💡 粘贴模式：")
    print("  • 直接粘贴多行文本（可以包含任意多行）")
    print("  • 粘贴完成后，在新的一行输入 'END' 结束")
    print("  • 或按 Ctrl+D (macOS/Linux) / Ctrl+Z (Windows) 结束")
    print("  • 输入 'CANCEL' 取消操作")
    print()
    print("请粘贴内容（结束后输入END）：")

    lines = []

    try:
        while True:
            try:
                line = input()

                # 检查结束命令
                if line.strip().upper() == "END":
                    break

                # 检查取消命令
                if line.strip().upper() == "CANCEL":
                    print("\n❌ 已取消输入")
                    raise KeyboardInterrupt

                lines.append(line)

            except EOFError:
                break

    except KeyboardInterrupt:
        raise RuntimeError("用户取消输入")

    result = "\n".join(lines).strip()

    if not result:
        raise ValueError("提示词不能为空")

    _show_input_preview(result, len(lines))
    return result


def _show_input_preview(result: str, line_count: int):
    """显示输入内容预览"""
    print(f"\n{'='*60}")
    print(f"✅ 已输入 {line_count} 行，共 {len(result)} 字符")
    print(f"{'='*60}")
    print("内容预览：")
    preview_lines = result.split('\n')[:5]
    for i, line in enumerate(preview_lines, 1):
        print(f"  {i}. {line[:80]}{'...' if len(line) > 80 else ''}")
    if len(result.split('\n')) > 5:
        print(f"  ... (还有 {len(result.split('\n')) - 5} 行)")
    print(f"{'='*60}\n")


def generate_image(prompt: str, save_dir: str, size: str = "1024x1024", model: str = "doubao-seedream-3-0-t2i-250415") -> str:
    os.makedirs(save_dir, exist_ok=True)

    model_lower = (model or "").lower()
    if model_lower.startswith("qwen/") or "qwen-image" in model_lower:
        image_result = text_to_image_siliconflow(prompt=prompt, size=size, model=model)
        if not image_result:
            raise RuntimeError("图像生成失败：未返回内容")
        data_type = image_result.get("type")
        data_value = image_result.get("data")
        if data_type == "url":
            image_url = data_value
            if not is_valid_http_url(image_url):
                raise RuntimeError(f"图像生成失败：URL无效或不受支持 -> {image_url}")
            content_bytes = requests.get(image_url, timeout=60).content
        elif data_type == "b64":
            import base64
            content_bytes = base64.b64decode(data_value)
        else:
            raise RuntimeError("图像生成失败：返回类型不支持")
    else:
        image_url = text_to_image_doubao(prompt=prompt, size=size, model=model)
        if not image_url or not isinstance(image_url, str):
            raise RuntimeError("图像生成失败：未返回URL")
        if not is_valid_http_url(image_url):
            raise RuntimeError(f"图像生成失败：URL无效或不受支持 -> {image_url}")
        content_bytes = requests.get(image_url, timeout=60).content

    # 强制保存为 PNG（无论返回URL的原始扩展名）
    filename = build_filename(prompt, ".png")
    output_path = os.path.join(save_dir, filename)

    try:
        with Image.open(BytesIO(content_bytes)) as img_loaded:
            # 强制解码，尽早暴露错误
            img_loaded.load()
            # 统一转换到适合PNG的模式（保持透明度）
            if img_loaded.mode in ("RGBA", "LA") or (img_loaded.mode == "P" and "transparency" in img_loaded.info):
                img_converted = img_loaded.convert("RGBA")
            else:
                img_converted = img_loaded.convert("RGB")

        temp_path = f"{output_path}.part"
        img_converted.save(temp_path, format="PNG")
        os.replace(temp_path, output_path)
    except UnidentifiedImageError as e:
        raise RuntimeError(f"下载的内容不是有效图片：{e}")
    except Exception as e:
        raise RuntimeError(f"下载或转换PNG失败：{e}")

    return output_path


def generate_audio(
    prompt: str,
    save_dir: str,
    voice: str = "zh_male_yuanboxiaoshu_moon_bigtts",
    encoding: str = "wav",
    speech_rate: int = 0,
    loudness_rate: int = 0,
    emotion: str = "neutral",
    emotion_scale: int = 4,
    mute_cut_threshold: int = 400,
    mute_cut_min_silence_ms: int = 200,
    mute_cut_remain_ms: int = 100,
) -> str:
    os.makedirs(save_dir, exist_ok=True)

    enc_norm = encoding.lower().lstrip(".")
    allowed = {"wav", "mp3"}
    if enc_norm not in allowed:
        raise ValueError(f"不支持的音频编码：{encoding}，仅支持：{', '.join(sorted(allowed))}")

    ext = f".{enc_norm}"
    filename = build_filename(prompt, ext)
    output_path = os.path.join(save_dir, filename)
    ok = text_to_audio_bytedance(
        text=prompt,
        output_filename=output_path,
        voice=voice,
        encoding=enc_norm,
        speech_rate=speech_rate,
        loudness_rate=loudness_rate,
        emotion=emotion,
        emotion_scale=emotion_scale,
        mute_cut_threshold=mute_cut_threshold,
        mute_cut_min_silence_ms=mute_cut_min_silence_ms,
        mute_cut_remain_ms=mute_cut_remain_ms,
    )
    if not ok or not os.path.exists(output_path):
        raise RuntimeError("语音合成失败")
    return output_path


def main(
    image_size: str = "1024x1024",
    image_model: str = "doubao-seedream-3-0-t2i-250415",
    tts_voice: str = "zh_male_yuanboxiaoshu_moon_bigtts",
    audio_encoding: str = "wav",
) -> int:
    project_root = os.path.dirname(__file__)
    temp_dir = ensure_temp_dir(project_root)

    print("\n======================")
    print("独立生成：图片 或 音频")
    print("======================\n")
    print(f"当前参数：图片尺寸={image_size} | 图片模型={image_model}")
    print(f"当前参数：语音音色={tts_voice} | 音频编码={audio_encoding}")
    print("请选择要生成的类型：")
    print("  1) 图片")
    print("  2) 音频")
    print("  q) 退出")

    while True:
        choice = input("请输入选项 (1/2/q): ").strip().lower()
        if choice in ("1", "2", "q"):
            break
        print("无效输入，请输入 1、2 或 q。")

    if choice == "q":
        print("已退出。")
        return 0

    try:
        if choice == "1":
            # 生成图片
            try:
                prompt = get_multiline_prompt("请输入图片提示词")
            except (ValueError, RuntimeError) as e:
                print(f"❌ {e}")
                return 1
            print("\n正在生成图片…")
            out_path = generate_image(prompt, temp_dir, size=image_size, model=image_model)
            print(f"完成！图片已保存：{out_path}")
        else:
            # 生成音频
            text_content = get_text_input()
            print("\n正在合成音频…")
            out_path = generate_audio(text_content, temp_dir, voice=tts_voice, encoding=audio_encoding)
            print(f"完成！音频已保存：{out_path}")
        return 0
    except KeyboardInterrupt:
        print("\n已取消。")
        return 1
    except Exception as e:
        print(f"\n❌ 失败：{e}")
        return 1


if __name__ == "__main__":
    # ================= 可在下方调整主要参数（便于修改） =================
    # 可选尺寸：1024x1024 | 864x1152 | 1152x864 | 1280x720 | 720x1280 | 832x1248 | 1248x832 | 1512x648
    IMAGE_SIZE = "2560x1440"
    # 可选图片模型：
    # - doubao-seedream-3-0-t2i-250415 (V3模型，支持guidance_scale参数)
    # - doubao-seedream-4-0-250828 (V4模型，新版API，不支持guidance_scale)
    IMAGE_MODEL = "doubao-seedream-4-0-250828"
    TTS_VOICE = "zh_male_yuanboxiaoshu_moon_bigtts"  # 可在豆包/字节控制台选择其他音色
    AUDIO_ENCODING = "wav"  # 可选：wav | mp3

    sys.exit(main(
        image_size=IMAGE_SIZE,
        image_model=IMAGE_MODEL,
        tts_voice=TTS_VOICE,
        audio_encoding=AUDIO_ENCODING,
    ))
