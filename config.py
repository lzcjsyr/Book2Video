# ████████████████████████████████████████████████████████████████████████████████
# ██                  用户配置参数区域(参数按7步工作流程组织，清晰对应各步骤)           ██
# ████████████████████████████████████████████████████████████████████████████████

# ════════════════════════════════════════════════════════════════════════════════
# ⚙️  全局配置
# ════════════════════════════════════════════════════════════════════════════════
OPENING_QUOTE = True                                   # 是否启用开场金句（影响步骤3、4、5）

# ════════════════════════════════════════════════════════════════════════════════
# 📝 步骤1：智能总结 - 文档压缩
# ════════════════════════════════════════════════════════════════════════════════
LLM_MODEL_STEP1 = "moonshotai/Kimi-K2-Instruct-0905"    # 步骤1 LLM模型（智能总结）
TARGET_LENGTH = 2000                                    # 目标字数 (500-5000)
LLM_TEMPERATURE_SCRIPT = 0.7                            # 生成随机性 (0-1，越大越随机)
# 步骤1 LLM模型荐模型: google/gemini-2.5-pro, moonshotai/Kimi-K2-Instruct-0905

# ════════════════════════════════════════════════════════════════════════════════
# ✂️  步骤1.5：脚本分段 - 段落切分
# ════════════════════════════════════════════════════════════════════════════════
NUM_SEGMENTS = 15                                       # 视频分段数量 (5-50)

# ════════════════════════════════════════════════════════════════════════════════
# 🔍 步骤2：要点提取 - 视觉关键词
# ════════════════════════════════════════════════════════════════════════════════
LLM_MODEL_STEP2 = "moonshotai/Kimi-K2-Instruct-0905"   # 步骤2 LLM模型（要点提取）
IMAGES_METHOD = "description"                          # 配图生成方式: keywords / description
LLM_TEMPERATURE_KEYWORDS = 0.5                          # 提取随机性 (0-1，越大越随机)
# keywords模式: 为每段提取视觉关键词和氛围词
# description模式: 生成内容整体描述，适合连贯性更强的配图
# 步骤1 LLM模型荐模型: moonshotai/Kimi-K2-Instruct-0905

# ════════════════════════════════════════════════════════════════════════════════
# 🎨 步骤3：图像生成 - AI配图
# ════════════════════════════════════════════════════════════════════════════════
IMAGE_SIZE = "2560x1440"                               # 图像尺寸 (16:9 横屏)
IMAGE_MODEL = "doubao-seedream-4-0-250828"             # 图像生成模型
IMAGE_STYLE_PRESET = "style06"                         # 段落图像风格预设 (详见 prompts.py)
OPENING_IMAGE_STYLE = "des01"                          # 开场图像风格 (详见 prompts.py)
MAX_CONCURRENT_IMAGE_GENERATION = 5                    # 图像生成最大并发数

# 图像模型尺寸规则：
# - doubao-seedream-4-0-250828: 支持 [1280x720, 4096x4096] 范围内任意尺寸
# - doubao-seedream-3-0-t2i-250415: 支持 [512x512, 2048x2048] 范围内任意尺寸
# - Qwen/Qwen-Image: 仅支持固定尺寸 (如 1664x928, 1328x1328, 928x1664, 1472x1140, 1140x1472 等)

# ════════════════════════════════════════════════════════════════════════════════
# 🎙️  步骤4：语音合成 - TTS配音
# ════════════════════════════════════════════════════════════════════════════════
VOICE = "S_MfnRsKLH1"                                  # 语音音色
RESOURCE_ID = "seed-icl-2.0"                           # TTS资源ID: seed-tts-1.0, seed-tts-2.0, seed-icl-1.0, seed-icl-2.0

# 音频参数配置
TTS_EMOTION = "neutral"                                # 情感: neutral(中性), happy(高兴), sad(悲伤)等
TTS_EMOTION_SCALE = 4                                  # 情感强度 (1-5, 默认4)
TTS_SPEECH_RATE = 20                                   # 语速 (-50到100, 0=正常, 100=2倍速, -50=0.5倍速, 默认0)
TTS_LOUDNESS_RATE = 0                                  # 音量 (-50到100, 0=正常, 100=2倍音量, -50=0.5倍音量, 默认0)

MUTE_CUT_THRESHOLD = 500                               # 静音判定阈值 (建议200-800, 0=禁用)
MUTE_CUT_MIN_SILENCE_MS = 200                          # 最小静音长度 (毫秒, 只切除长于此值的静音, 建议100-500)
MUTE_CUT_REMAIN_MS = 1                               # 静音切除后保留时长 (毫秒, 建议50-150)

MAX_CONCURRENT_VOICE_SYNTHESIS = 5                     # 语音合成最大并发数

# seed-tts-1.0: zh_male_yuanboxiaoshu_moon_bigtts(男-书香), zh_female_wenrouxiaoya_moon_bigtts(女-文雅)
# seed-tts-2.0：zh_male_ruyayichen_saturn_bigtts, zh_female_santongyongns_saturn_bigtts
# seed-icl-2.0：S_MfnRsKLH1

# ════════════════════════════════════════════════════════════════════════════════
# 🎬 步骤5：视频合成 - 最终导出
# ════════════════════════════════════════════════════════════════════════════════

# --- 基础设置 ---
VIDEO_SIZE = "1280x720"                                # 视频导出尺寸 (可与 IMAGE_SIZE 不同)
ENABLE_SUBTITLES = True                                # 是否启用字幕
BGM_FILENAME = "Light of the Seven.mp3"                          # 背景音乐 (music/ 下，None=无音乐)

# --- 音频控制 ---
BGM_DEFAULT_VOLUME = 0.25                              # 背景音乐音量 (0=静音, 1=原音, >1放大, 推荐0.03-0.20)
NARRATION_DEFAULT_VOLUME = 2.0                         # 口播音量 (0.5-3.0, 推荐0.8-1.5, >2.0有削波风险)
NARRATION_SPEED_FACTOR = 1.1                          # 口播变速系数 (1.0=原速)

# 音频闪避（口播时自动降低BGM音量）
AUDIO_DUCKING_ENABLED = True                          # 是否启用音频闪避
AUDIO_DUCKING_STRENGTH = 0.3                           # BGM压低强度 (0-1)
AUDIO_DUCKING_SMOOTH_SECONDS = 0.12                    # 音量过渡平滑时间 (秒)

# --- 视觉效果时间控制 ---
OPENING_FADEIN_SECONDS = 2.0                           # 开场渐显时长 (秒)
OPENING_HOLD_AFTER_NARRATION_SECONDS = 0.3             # 开场口播后停留时长 (秒)
ENDING_FADE_SECONDS = 2.0                              # 片尾淡出时长 (秒)

# --- 字幕样式配置 ---
# 字体路径建议：
# macOS 苹方字体: /System/Library/Fonts/PingFang.ttc
# macOS 宋体: /System/Library/Fonts/Supplemental/Songti.ttc
# Windows 微软雅黑: C:/Windows/Fonts/msyh.ttc
SUBTITLE_FONT_SIZE = 38                                # 字幕字体大小
SUBTITLE_FONT_FAMILY = "/System/Library/Fonts/STHeiti Light.ttc"  # 字幕字体路径
SUBTITLE_COLOR = "white"                               # 字幕文字颜色
SUBTITLE_STROKE_COLOR = "black"                        # 字幕描边颜色
SUBTITLE_STROKE_WIDTH = 2                              # 字幕描边粗细
SUBTITLE_POSITION = ("center", "bottom")               # 字幕位置 (水平, 垂直)
SUBTITLE_MARGIN_BOTTOM = 50                            # 字幕距底部距离 (像素)
SUBTITLE_MAX_CHARS_PER_LINE = 25                       # 字幕每行最大字符数
SUBTITLE_MAX_LINES = 1                                 # 字幕最大行数
SUBTITLE_LINE_SPACING = 15                             # 字幕行间距 (像素)
SUBTITLE_BACKGROUND_COLOR = (0, 0, 0)                  # 字幕背景色 (RGB, None=透明)
SUBTITLE_BACKGROUND_OPACITY = 0.8                      # 字幕背景不透明度 (0-1)
SUBTITLE_BACKGROUND_H_PADDING = 20                     # 字幕背景水平内边距 (像素)
SUBTITLE_BACKGROUND_V_PADDING = 10                     # 字幕背景垂直内边距 (像素)
SUBTITLE_SHADOW_ENABLED = False                        # 是否启用字幕阴影
SUBTITLE_SHADOW_COLOR = "black"                        # 字幕阴影颜色
SUBTITLE_SHADOW_OFFSET = (2, 2)                        # 字幕阴影偏移 (x, y)

# --- 开场金句样式配置 ---
OPENING_QUOTE_FONT_FAMILY = "/System/Library/Fonts/STHeiti Light.ttc"  # 开场金句字体路径
OPENING_QUOTE_FONT_SIZE = 50                       # 开场金句字体大小
OPENING_QUOTE_FONT_SCALE = 1.3                     # 开场金句相对字幕字体的缩放倍数
OPENING_QUOTE_COLOR = "white"                      # 开场金句文字颜色
OPENING_QUOTE_STROKE_COLOR = "black"               # 开场金句描边颜色
OPENING_QUOTE_STROKE_WIDTH = 3                     # 开场金句描边粗细
OPENING_QUOTE_POSITION = ("center", "center")      # 开场金句位置 (居中显示)
OPENING_QUOTE_MAX_LINES = 6                        # 开场金句最大行数
OPENING_QUOTE_MAX_CHARS_PER_LINE = 20              # 开场金句每行最大字符数
OPENING_QUOTE_LINE_SPACING = 25                    # 开场金句行间距 (像素)
OPENING_QUOTE_LETTER_SPACING = 0                   # 开场金句字间距 (0=正常)

# --- 素材处理配置 ---
IMAGE_MATERIAL_TARGET_FPS = 15                         # 纯图片素材时的帧率
VIDEO_MATERIAL_TARGET_FPS = 30                         # 有视频素材时的目标帧率
VIDEO_MATERIAL_REMOVE_AUDIO = True                     # 是否移除原视频素材中的音频
VIDEO_MATERIAL_DURATION_ADJUST = "stretch"             # 视频时长调整方式: stretch/crop
VIDEO_MATERIAL_RESIZE_METHOD = "crop"                  # 视频尺寸调整方式: crop/stretch

# ════════════════════════════════════════════════════════════════════════════════
# 🖼️  步骤6：封面生成 - 宣传素材
# ════════════════════════════════════════════════════════════════════════════════
COVER_IMAGE_SIZE = "2250x3000"                         # 封面图像尺寸 (竖版 3:4)
COVER_IMAGE_MODEL = "doubao-seedream-4-0-250828"       # 封面图像生成模型
COVER_IMAGE_STYLE = "cover09"                          # 封面风格预设 (详见 prompts.py)
COVER_IMAGE_COUNT = 1                                  # 封面生成数量


# ████████████████████████████████████████████████████████████████████████████████
# ██                          系统内部配置（勿动）                                ██
# ████████████████████████████████████████████████████████████████████████████████

import os
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def get_generation_params() -> Dict[str, object]:
    """返回生成参数字典（供CLI使用）"""
    return {
        "target_length": TARGET_LENGTH,
        "num_segments": NUM_SEGMENTS,
        "image_size": IMAGE_SIZE,
        "video_size": VIDEO_SIZE,
        "llm_model_step1": LLM_MODEL_STEP1,
        "llm_model_step2": LLM_MODEL_STEP2,
        "image_model": IMAGE_MODEL,
        "voice": VOICE,
        "resource_id": RESOURCE_ID,
        "tts_emotion": TTS_EMOTION,
        "tts_emotion_scale": TTS_EMOTION_SCALE,
        "tts_speech_rate": TTS_SPEECH_RATE,
        "tts_loudness_rate": TTS_LOUDNESS_RATE,
        "mute_cut_threshold": MUTE_CUT_THRESHOLD,
        "mute_cut_min_silence_ms": MUTE_CUT_MIN_SILENCE_MS,
        "mute_cut_remain_ms": MUTE_CUT_REMAIN_MS,
        "output_dir": "output",
        "image_style_preset": IMAGE_STYLE_PRESET,
        "opening_image_style": OPENING_IMAGE_STYLE,
        "images_method": IMAGES_METHOD,
        "enable_subtitles": ENABLE_SUBTITLES,
        "bgm_filename": BGM_FILENAME,
        "opening_quote": OPENING_QUOTE,

        "cover_image_size": COVER_IMAGE_SIZE,
        "cover_image_model": COVER_IMAGE_MODEL,
        "cover_image_style": COVER_IMAGE_STYLE,
        "cover_image_count": COVER_IMAGE_COUNT,
    }
    
class Config:
    """系统配置类，统一管理所有配置项"""
    pass


# 批量将模块级配置变量同步到Config类（避免重复赋值代码）
_USER_CONFIG_ATTRS = [
    # 音视频参数
    'LLM_TEMPERATURE_SCRIPT', 'LLM_TEMPERATURE_KEYWORDS',
    'BGM_DEFAULT_VOLUME', 'NARRATION_DEFAULT_VOLUME',
    'AUDIO_DUCKING_ENABLED', 'AUDIO_DUCKING_STRENGTH', 'AUDIO_DUCKING_SMOOTH_SECONDS',
    'OPENING_FADEIN_SECONDS', 'OPENING_HOLD_AFTER_NARRATION_SECONDS', 'ENDING_FADE_SECONDS',
    'NARRATION_SPEED_FACTOR',
    # 字幕配置
    'SUBTITLE_FONT_SIZE', 'SUBTITLE_FONT_FAMILY', 'SUBTITLE_COLOR',
    'SUBTITLE_STROKE_COLOR', 'SUBTITLE_STROKE_WIDTH', 'SUBTITLE_POSITION',
    'SUBTITLE_MARGIN_BOTTOM', 'SUBTITLE_MAX_CHARS_PER_LINE', 'SUBTITLE_MAX_LINES',
    'SUBTITLE_LINE_SPACING', 'SUBTITLE_BACKGROUND_COLOR', 'SUBTITLE_BACKGROUND_OPACITY',
    'SUBTITLE_BACKGROUND_H_PADDING', 'SUBTITLE_BACKGROUND_V_PADDING',
    'SUBTITLE_SHADOW_ENABLED', 'SUBTITLE_SHADOW_COLOR', 'SUBTITLE_SHADOW_OFFSET',
    # 开场金句配置
    'OPENING_QUOTE_FONT_FAMILY', 'OPENING_QUOTE_FONT_SIZE', 'OPENING_QUOTE_FONT_SCALE',
    'OPENING_QUOTE_COLOR', 'OPENING_QUOTE_STROKE_COLOR', 'OPENING_QUOTE_STROKE_WIDTH',
    'OPENING_QUOTE_POSITION', 'OPENING_QUOTE_MAX_LINES', 'OPENING_QUOTE_MAX_CHARS_PER_LINE',
    'OPENING_QUOTE_LINE_SPACING', 'OPENING_QUOTE_LETTER_SPACING',
    # 素材处理配置
    'VIDEO_MATERIAL_TARGET_FPS', 'VIDEO_MATERIAL_REMOVE_AUDIO',
    'VIDEO_MATERIAL_DURATION_ADJUST', 'VIDEO_MATERIAL_RESIZE_METHOD',
    'IMAGE_MATERIAL_TARGET_FPS',
    # 并发控制
    'MAX_CONCURRENT_IMAGE_GENERATION', 'MAX_CONCURRENT_VOICE_SYNTHESIS',
    # TTS配置
    'RESOURCE_ID', 'TTS_EMOTION', 'TTS_EMOTION_SCALE',
    'TTS_SPEECH_RATE', 'TTS_LOUDNESS_RATE', 'MUTE_CUT_THRESHOLD', 'MUTE_CUT_MIN_SILENCE_MS', 'MUTE_CUT_REMAIN_MS',
]

for _attr in _USER_CONFIG_ATTRS:
    setattr(Config, _attr, globals()[_attr])


# 继续设置Config类的系统配置（非用户可配置项）
Config.OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
Config.SEEDREAM_API_KEY = os.getenv('SEEDREAM_API_KEY')
Config.SILICONFLOW_KEY = os.getenv('SILICONFLOW_KEY')

Config.BYTEDANCE_TTS_APPID = os.getenv('BYTEDANCE_TTS_APPID')
Config.BYTEDANCE_TTS_ACCESS_TOKEN = os.getenv('BYTEDANCE_TTS_ACCESS_TOKEN')
Config.BYTEDANCE_TTS_SECRET_KEY = os.getenv('BYTEDANCE_TTS_SECRET_KEY')
Config.BYTEDANCE_TTS_VERIFY_SSL = os.getenv('BYTEDANCE_TTS_VERIFY_SSL', 'true').lower() == 'true'

Config.OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
Config.SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
Config.SILICONFLOW_IMAGE_BASE_URL = "https://api.siliconflow.cn/v1/images/generations"
Config.ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

Config.DEFAULT_IMAGE_SIZE = "1664x928"
Config.DEFAULT_VOICE = "zh_male_yuanboxiaoshu_moon_bigtts"
Config.DEFAULT_OUTPUT_DIR = "output"

Config.SUPPORTED_LLM_SERVERS = ["openrouter", "siliconflow"]
Config.SUPPORTED_IMAGE_SERVERS = ["doubao", "siliconflow"]
Config.SUPPORTED_TTS_SERVERS = ["bytedance"]
Config.SUPPORTED_IMAGE_METHODS = ["keywords", "description"]

Config.RECOMMENDED_MODELS = {
    "llm": {
        "openrouter": ["google/gemini-2.5-pro", "anthropic/claude-sonnet-4", "openai/gpt-5"],
        "siliconflow": ["Qwen/Qwen2.5-72B-Instruct", "deepseek-ai/DeepSeek-V3"]
    },
    "image": {
        "doubao": ["doubao-seedream-4-0-250828", "doubao-seedream-3-0-t2i-250415"],
        "siliconflow": ["stabilityai/stable-diffusion-3-5-large", "black-forest-labs/FLUX.1-schnell"]
    },
    "voice": ["zh_male_yuanboxiaoshu_moon_bigtts", "zh_male_haoyuxiaoge_moon_bigtts", 
             "zh_female_wenrouxiaoya_moon_bigtts", "zh_female_daimengchuanmei_moon_bigtts"]
}

Config.SUPPORTED_VIDEO_SIZES = {
    "横屏16:9": ["1280x720", "1664x928", "1920x1080", "2560x1440"],
    "竖屏9:16": ["720x1280", "1080x1920"],
    "方形1:1": ["1024x1024", "1664x1664"],
    "竖屏3:4": ["864x1152", "1536x2048", "2250x3000"]
}

Config.SUPPORTED_QWEN_IMAGE_SIZES = [
    "1328x1328", "1664x928", "928x1664", "1472x1140", 
    "1140x1472", "1584x1056", "1056x1584"
]

Config.SEEDREAM_V4_MIN_SIZE = (1280, 720)
Config.SEEDREAM_V4_MAX_SIZE = (4096, 4096)
Config.SEEDREAM_V3_MIN_SIZE = (512, 512)
Config.SEEDREAM_V3_MAX_SIZE = (2048, 2048)

Config.SERVER_TYPE_MAP = {
    "llm_server": "llm",
    "image_server": "image", 
    "tts_server": "voice",
    "text": "text"
}

Config.MIN_TARGET_LENGTH = 500
Config.MAX_TARGET_LENGTH = 5000
Config.MIN_NUM_SEGMENTS = 5
Config.MAX_NUM_SEGMENTS = 50
Config.SPEECH_SPEED_WPM = 250


# ================================================================================
#                           动态添加Config类方法
# ================================================================================

def _validate_api_keys_impl(cls) -> Dict[str, bool]:
    """验证API密钥配置"""
    return {
        "openrouter": bool(cls.OPENROUTER_API_KEY),
        "siliconflow": bool(cls.SILICONFLOW_KEY),
        "seedream": bool(cls.SEEDREAM_API_KEY),
        "bytedance_tts": bool(cls.BYTEDANCE_TTS_APPID and cls.BYTEDANCE_TTS_ACCESS_TOKEN)
    }

def _get_missing_keys_impl(cls) -> List[str]:
    """获取缺失的必需API密钥"""
    missing = []
    key_status = cls.validate_api_keys()
    
    if not (key_status["openrouter"] or key_status["siliconflow"]):
        missing.append("OPENROUTER_API_KEY 或 SILICONFLOW_KEY (至少一个)")
    if not key_status["seedream"]:
        missing.append("SEEDREAM_API_KEY")
    if not key_status["bytedance_tts"]:
        missing.append("BYTEDANCE_TTS_APPID 和 BYTEDANCE_TTS_ACCESS_TOKEN")
    
    return missing

def _get_required_keys_for_config_impl(cls, llm_server: str, image_server: str, tts_server: str) -> List[str]:
    """根据服务配置返回所需的API密钥列表"""
    required_keys = []
    
    if llm_server == "openrouter":
        required_keys.append("OPENROUTER_API_KEY")
    elif llm_server == "siliconflow":
        required_keys.append("SILICONFLOW_KEY")
    
    if image_server == "doubao":
        required_keys.append("SEEDREAM_API_KEY")
    elif image_server == "siliconflow":
        if "SILICONFLOW_KEY" not in required_keys:
            required_keys.append("SILICONFLOW_KEY")
    
    if tts_server == "bytedance":
        required_keys.append("BYTEDANCE_TTS_APPID")
        required_keys.append("BYTEDANCE_TTS_ACCESS_TOKEN")
    
    return required_keys

def _validate_image_size_impl(cls, size: str, model: str) -> bool:
    """验证图像尺寸是否符合模型要求"""
    if not size or 'x' not in size:
        return False
    
    try:
        width, height = map(int, size.split('x'))
    except ValueError:
        return False
    
    if "Qwen" in model or "qwen" in model:
        return size in cls.SUPPORTED_QWEN_IMAGE_SIZES
    
    if "doubao" in model.lower():
        if "seedream-4" in model.lower():
            return 1280 <= width <= 4096 and 720 <= height <= 4096
        elif "seedream-3" in model.lower():
            return 512 <= width <= 2048 and 512 <= height <= 2048
    
    return True

def _validate_parameters_impl(
    cls,
    target_length: int,
    num_segments: int,
    llm_server: str,
    image_server: str,
    tts_server: str,
    image_model: str,
    image_size: str,
    images_method: str = None,
) -> None:
    """验证所有参数的有效性"""
    
    if not cls.MIN_TARGET_LENGTH <= target_length <= cls.MAX_TARGET_LENGTH:
        raise ValueError(f"target_length必须在{cls.MIN_TARGET_LENGTH}-{cls.MAX_TARGET_LENGTH}之间")
    
    if not cls.MIN_NUM_SEGMENTS <= num_segments <= cls.MAX_NUM_SEGMENTS:
        raise ValueError(f"num_segments必须在{cls.MIN_NUM_SEGMENTS}-{cls.MAX_NUM_SEGMENTS}之间")
    
    if llm_server not in cls.SUPPORTED_LLM_SERVERS:
        raise ValueError(f"不支持的LLM服务商: {llm_server}，支持的服务商: {cls.SUPPORTED_LLM_SERVERS}")
    
    if image_server not in cls.SUPPORTED_IMAGE_SERVERS:
        raise ValueError(f"不支持的图像服务商: {image_server}，支持的服务商: {cls.SUPPORTED_IMAGE_SERVERS}")
    
    if tts_server not in cls.SUPPORTED_TTS_SERVERS:
        raise ValueError(f"不支持的TTS服务商: {tts_server}，支持的服务商: {cls.SUPPORTED_TTS_SERVERS}")
    
    if images_method and images_method not in cls.SUPPORTED_IMAGE_METHODS:
        raise ValueError(f"不支持的图像生成方法: {images_method}，支持的方法: {cls.SUPPORTED_IMAGE_METHODS}")
    
    if not cls.validate_image_size(image_size, image_model):
        raise ValueError(
            f"图像尺寸 {image_size} 不符合模型 {image_model} 的要求。\n"
            f"Qwen模型支持的固定尺寸: {cls.SUPPORTED_QWEN_IMAGE_SIZES}\n"
            f"Doubao-4模型支持: 1280x720 到 4096x4096 之间的任意尺寸\n"
            f"Doubao-3模型支持: 512x512 到 2048x2048 之间的任意尺寸"
        )

# 将方法绑定到Config类
Config.validate_api_keys = classmethod(_validate_api_keys_impl)
Config.get_missing_keys = classmethod(_get_missing_keys_impl)
Config.get_required_keys_for_config = classmethod(_get_required_keys_for_config_impl)
Config.validate_image_size = classmethod(_validate_image_size_impl)
Config.validate_parameters = classmethod(_validate_parameters_impl)


# 创建全局配置实例
config = Config()
