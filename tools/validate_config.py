#!/usr/bin/env python3
"""
配置验证工具 - 检查系统配置的完整性和有效性
使用方法: python tools/validate_config.py
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import config, Config
from typing import List, Dict, Any


def check_api_keys() -> List[str]:
    """检查API密钥配置"""
    issues = []
    
    # 检查LLM服务密钥
    llm_keys = {
        "OpenRouter": config.OPENROUTER_API_KEY,
        "SiliconFlow": config.SILICONFLOW_KEY,
    }
    
    has_llm = any(llm_keys.values())
    if not has_llm:
        issues.append("⚠️  警告: 未配置任何LLM服务API密钥（至少需要一个）")
    else:
        for name, key in llm_keys.items():
            if key:
                print(f"✅ {name} API密钥: 已配置")
            else:
                print(f"ℹ️  {name} API密钥: 未配置（可选）")
    
    # 检查图像生成服务密钥
    if not config.SEEDREAM_API_KEY:
        issues.append("❌ 错误: SEEDREAM_API_KEY未配置（图像生成必需）")
    else:
        print("✅ Seedream API密钥: 已配置")
    
    # 检查TTS服务密钥
    if config.BYTEDANCE_TTS_API_KEY:
        print("✅ 豆包语音 API Key: 已配置")
    else:
        issues.append("❌ 错误: 豆包语音配置不完整（请配置 BYTEDANCE_TTS_API_KEY）")
    
    return issues


def check_directories() -> List[str]:
    """检查必要的目录"""
    issues = []
    required_dirs = {
        "input": "输入文档目录",
        "output": "输出目录",
        "music": "背景音乐目录",
        "core": "核心模块目录",
        "cli": "CLI模块目录",
    }
    
    print("\n📁 检查目录结构:")
    for dir_name, description in required_dirs.items():
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name}/ - {description}: 存在")
        else:
            if dir_name in ["input", "music"]:
                issues.append(f"⚠️  警告: {dir_name}/ 目录不存在，建议创建")
            else:
                issues.append(f"❌ 错误: {dir_name}/ 目录不存在（系统必需）")
    
    return issues


def check_config_params() -> List[str]:
    """检查配置参数有效性"""
    issues = []
    from core.config import (TARGET_LENGTH, NUM_SEGMENTS, IMAGE_SIZE, IMAGE_MODEL,
                       TTS_SPEECH_RATE, TTS_LOUDNESS_RATE, TTS_EMOTION, TTS_EMOTION_SCALE, TTS_MODEL)
    
    print("\n⚙️  检查配置参数:")
    
    # 检查字数范围
    if not (Config.MIN_TARGET_LENGTH <= TARGET_LENGTH <= Config.MAX_TARGET_LENGTH):
        issues.append(
            f"❌ TARGET_LENGTH={TARGET_LENGTH} 超出范围 "
            f"[{Config.MIN_TARGET_LENGTH}, {Config.MAX_TARGET_LENGTH}]"
        )
    else:
        print(f"✅ 目标字数: {TARGET_LENGTH} (有效)")
    
    # 检查分段数
    if not (Config.MIN_NUM_SEGMENTS <= NUM_SEGMENTS <= Config.MAX_NUM_SEGMENTS):
        issues.append(
            f"❌ NUM_SEGMENTS={NUM_SEGMENTS} 超出范围 "
            f"[{Config.MIN_NUM_SEGMENTS}, {Config.MAX_NUM_SEGMENTS}]"
        )
    else:
        print(f"✅ 分段数量: {NUM_SEGMENTS} (有效)")
    
    # 检查图像尺寸
    try:
        w, h = IMAGE_SIZE.split("x")
        width, height = int(w), int(h)
        
        # 检查Seedream V4尺寸范围
        if "seedream-4" in IMAGE_MODEL.lower():
            min_w, min_h = Config.SEEDREAM_V4_MIN_SIZE
            max_w, max_h = Config.SEEDREAM_V4_MAX_SIZE
            if not (min_w <= width <= max_w and min_h <= height <= max_h):
                issues.append(
                    f"❌ 图像尺寸 {IMAGE_SIZE} 超出Seedream V4范围 "
                    f"[{min_w}x{min_h}, {max_w}x{max_h}]"
                )
            else:
                print(f"✅ 图像尺寸: {IMAGE_SIZE} (有效)")
        else:
            print(f"✅ 图像尺寸: {IMAGE_SIZE}")
    except Exception as e:
        issues.append(f"❌ 图像尺寸格式错误: {IMAGE_SIZE}")
    
    # 检查TTS参数
    if not (-50 <= TTS_SPEECH_RATE <= 100):
        issues.append(f"⚠️  TTS语速 {TTS_SPEECH_RATE} 超出范围 [-50, 100]")
    else:
        print(f"✅ TTS语速: {TTS_SPEECH_RATE}")

    if not (-50 <= TTS_LOUDNESS_RATE <= 100):
        issues.append(f"⚠️  TTS音量 {TTS_LOUDNESS_RATE} 超出范围 [-50, 100]")
    else:
        print(f"✅ TTS音量: {TTS_LOUDNESS_RATE}")

    if not (1 <= TTS_EMOTION_SCALE <= 5):
        issues.append(f"⚠️  TTS情感强度 {TTS_EMOTION_SCALE} 超出范围 [1, 5]")
    else:
        print(f"✅ TTS情感: {TTS_EMOTION}({TTS_EMOTION_SCALE})")

    voice_id = getattr(config, "BYTEDANCE_TTS_VOICE_ID", "") or getattr(config, "DEFAULT_VOICE", "")
    if not voice_id:
        issues.append("❌ 错误: 未配置声音ID（请在 .env 中设置 BYTEDANCE_TTS_VOICE_ID）")
    else:
        print(f"✅ TTS音色ID: {voice_id}")

    valid_tts_models = {"seed-tts-2.0-expressive", "seed-tts-2.0-standard"}
    if TTS_MODEL not in valid_tts_models:
        issues.append(f"⚠️  TTS模型 {TTS_MODEL} 不在推荐范围 {sorted(valid_tts_models)}")
    else:
        print(f"✅ TTS模型: {TTS_MODEL}")

    return issues


def check_dependencies() -> List[str]:
    """检查Python依赖包"""
    issues = []
    required_packages = [
        ("openai", "OpenAI API客户端"),
        ("requests", "HTTP请求库"),
        ("PIL", "图像处理库"),
        ("docx", "Word文档处理"),
        ("moviepy", "视频处理"),
        ("websockets", "WebSocket客户端"),
    ]
    
    print("\n📦 检查依赖包:")
    for package_name, description in required_packages:
        try:
            __import__(package_name)
            print(f"✅ {package_name}: 已安装")
        except ImportError:
            issues.append(f"❌ 错误: {package_name} ({description}) 未安装")
    
    return issues


def check_font_files() -> List[str]:
    """检查字体文件"""
    issues = []
    from core.domain.composer import VideoComposer
    
    print("\n🔤 检查字体文件:")
    composer = VideoComposer()
    
    # 检查字幕字体
    subtitle_font = config.SUBTITLE_FONT_FAMILY
    resolved = composer.resolve_font_path(subtitle_font)
    if resolved:
        print(f"✅ 字幕字体: {resolved}")
    else:
        issues.append(f"⚠️  警告: 未找到字幕字体 {subtitle_font}，将使用系统默认")
    
    # 检查开场金句字体
    quote_font = config.OPENING_QUOTE_FONT_FAMILY
    if quote_font:
        resolved = composer.resolve_font_path(quote_font)
        if resolved:
            print(f"✅ 开场字体: {resolved}")
        else:
            issues.append(f"⚠️  警告: 未找到开场字体 {quote_font}，将使用系统默认")
    
    return issues


def check_bgm_files() -> List[str]:
    """检查背景音乐文件"""
    issues = []
    from core.config import BGM_FILENAME
    
    print("\n🎵 检查背景音乐:")
    if not BGM_FILENAME:
        print("ℹ️  未配置背景音乐（可选）")
        return issues
    
    music_dir = project_root / "music"
    bgm_path = music_dir / BGM_FILENAME
    
    if bgm_path.exists():
        size_mb = bgm_path.stat().st_size / (1024 * 1024)
        print(f"✅ 背景音乐: {BGM_FILENAME} ({size_mb:.1f}MB)")
    else:
        issues.append(f"⚠️  警告: 背景音乐文件不存在: {BGM_FILENAME}")
    
    return issues


def main():
    """主函数"""
    print("=" * 70)
    print("🔍 AIGC视频制作系统 - 配置验证工具")
    print("=" * 70)
    
    all_issues = []
    
    # 运行各项检查
    print("\n🔑 检查API密钥:")
    all_issues.extend(check_api_keys())
    
    all_issues.extend(check_directories())
    all_issues.extend(check_config_params())
    all_issues.extend(check_dependencies())
    all_issues.extend(check_font_files())
    all_issues.extend(check_bgm_files())
    
    # 输出总结
    print("\n" + "=" * 70)
    print("📋 检查总结:")
    print("=" * 70)
    
    if not all_issues:
        print("✨ 恭喜！所有检查通过，系统配置正常。")
        return 0
    
    # 分类显示问题
    errors = [i for i in all_issues if i.startswith("❌")]
    warnings = [i for i in all_issues if i.startswith("⚠️")]
    
    if errors:
        print(f"\n❌ 发现 {len(errors)} 个错误（必须修复）:")
        for issue in errors:
            print(f"  {issue}")
    
    if warnings:
        print(f"\n⚠️  发现 {len(warnings)} 个警告（建议处理）:")
        for issue in warnings:
            print(f"  {issue}")
    
    print("\n💡 提示:")
    print("  - 请在 .env 文件中配置缺失的API密钥")
    print("  - 运行 'pip install -r requirements.txt' 安装缺失的依赖")
    print("  - 查看 core/config.py 调整配置参数")
    
    return 1 if errors else 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 验证过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
