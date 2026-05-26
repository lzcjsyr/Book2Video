# ████████████████████████████████████████████████████████████████████████████████
# ██                  用户配置参数区域(参数按7步工作流程组织，清晰对应各步骤)            ██
# ████████████████████████████████████████████████████████████████████████████████

# ════════════════════════════════════════════════════════════════════════════════
# ⚙️  全局配置
# ════════════════════════════════════════════════════════════════════════════════
OPENING_QUOTE = True                                 # 是否启用开场金句（影响步骤3、4、5）

# ════════════════════════════════════════════════════════════════════════════════
# 📝 步骤1：Claude Agent SDK - 原始文稿写作（小米 MiMo Anthropic 兼容端点）
# ════════════════════════════════════════════════════════════════════════════════
LLM_BASE_URL_STEP1 = "https://token-plan-sgp.xiaomimimo.com/anthropic"
LLM_MODEL_STEP1 = "mimo-v2.5-pro"                        # 填写完整模型名称，按网关要求原样传递
STEP1_AGENT_SKILL = "video-book-direct-read"             # 步骤1使用的 Claude Code skill
# 密钥：.env 中的 MIMO_API_KEY（由 Claude Code 读取为 ANTHROPIC_API_KEY）

# ════════════════════════════════════════════════════════════════════════════════
# ✂️  步骤1.5：脚本分段 - 段落切分
# ════════════════════════════════════════════════════════════════════════════════
NUM_SEGMENTS = 75                                       # 视频分段数量 (5-100)

# ════════════════════════════════════════════════════════════════════════════════
# 🔍 步骤2：要点提取 - 视觉关键词
# ════════════════════════════════════════════════════════════════════════════════
LLM_SERVER_STEP2 = "siliconflow"                        # 步骤2 LLM供应商
LLM_BASE_URL_STEP2 = "https://api.siliconflow.cn/v1"    # 步骤2 LLM base URL
LLM_MODEL_STEP2 = "Pro/moonshotai/Kimi-K2.6"            # 步骤2模型（要点提取）
IMAGES_METHOD = "description"                          # 配图生成方式: keywords / description
LLM_TEMPERATURE_KEYWORDS = 0.5                          # 提取随机性 (0-1，越大越随机)
# keywords模式: 为每段提取视觉关键词和氛围词
# description模式: 生成内容整体描述，适合连贯性更强的配图

# ════════════════════════════════════════════════════════════════════════════════
# 🎨 步骤3：视觉素材生成 - Remotion开场视频 + AI配图
# ════════════════════════════════════════════════════════════════════════════════
IMAGE_SERVER = "google"                                # 供应商: doubao / siliconflow / google / google_adc
IMAGE_SIZE = "2560x1440"                               # 图像尺寸 (16:9 横屏)
IMAGE_MODEL = "gemini-3.1-flash-image-preview"         # 模型：gemini-3.1-flash-image-preview,doubao-seedream-5-0-260128
IMAGE_STYLE_PRESET = "style02"                         # 段落图像风格预设 (详见 prompts.py)

LLM_SERVER_STEP3 = "siliconflow"                        # 步骤3提示词脱敏 LLM供应商
LLM_BASE_URL_STEP3 = "https://api.siliconflow.cn/v1"    # 步骤3提示词脱敏 LLM base URL
LLM_MODEL_STEP3 = "Pro/moonshotai/Kimi-K2.6"            # 步骤3提示词脱敏模型

MAX_CONCURRENT_IMAGE_GENERATION = 1                    # 图像生成最大并发数

# --- Remotion 开场视频配置（以下参数会直接影响 opening.mp4 的真实效果） ---
OPENING_REMOTION_IP_NAME = "Cody叩底"                   # 左上刊头文案
OPENING_REMOTION_DURATION_SECONDS = 5.0                # 开场视频时长（秒）
OPENING_REMOTION_FPS = 30                              # 开场视频帧率（fps）
OPENING_REMOTION_FIRST_LINE_SECONDS = 0.2              # 第一行金句出现时间（秒）
OPENING_REMOTION_LAST_LINE_SECONDS = 1.0               # 最后一行金句出现时间（秒）
OPENING_REMOTION_MAX_LINES = 4                         # 金句最大行数（也会影响断句）
OPENING_REMOTION_MAX_CHARS_PER_LINE = 20               # 每行最大字符数（也会影响断句）

# 图像模型尺寸规则：
# - doubao-seedream-4-0-250828: 支持 [1280x720, 4096x4096] 范围内任意尺寸
# - Qwen/Qwen-Image: 仅支持固定尺寸 (如 1664x928, 1328x1328, 928x1664, 1472x1140, 1140x1472 等)
# - gemini-3.1-flash-image-preview: 由Google模型自动决定输出尺寸（保留 IMAGE_SIZE 作为流程参数）

# ════════════════════════════════════════════════════════════════════════════════
# 🎙️  步骤4：语音合成 - TTS配音
# ════════════════════════════════════════════════════════════════════════════════
VOICE = ""                                             # 语音音色（建议通过 .env 的 BYTEDANCE_TTS_VOICE_ID 配置）
RESOURCE_ID = "seed-icl-2.0"                           # TTS资源ID: seed-tts-1.0, seed-tts-2.0, seed-icl-1.0, seed-icl-2.0
TTS_MODEL = "seed-tts-2.0-standard"                  # 声音复刻2.0模型效果: seed-tts-2.0-expressive / seed-tts-2.0-standard

# 音频参数配置
TTS_EMOTION = "neutral"                                # 情感: neutral(中性), happy(高兴), sad(悲伤)等
TTS_EMOTION_SCALE = 4                                  # 情感强度 (1-5, 默认4)
TTS_SPEECH_RATE = 20                                   # 语速 (-50到100, 0=正常, 100=2倍速, -50=0.5倍速, 默认0)
TTS_LOUDNESS_RATE = 0                                  # 音量 (-50到100, 0=正常, 100=2倍音量, -50=0.5倍音量, 默认0)

MUTE_CUT_THRESHOLD = 400                               # 静音判定阈值 (建议200-800, 0=禁用)
MUTE_CUT_MIN_SILENCE_MS = 300                          # 最小静音长度 (毫秒, 只切除长于此值的静音, 建议100-500)
MUTE_CUT_REMAIN_MS = 200                               # 静音切除后保留时长 (毫秒, 建议50-150)

MAX_CONCURRENT_VOICE_SYNTHESIS = 5                     # 语音合成最大并发数

# seed-tts-1.0: zh_male_yuanboxiaoshu_moon_bigtts(男-书香), zh_female_wenrouxiaoya_moon_bigtts(女-文雅)
# seed-tts-2.0：zh_male_ruyayichen_saturn_bigtts, zh_female_santongyongns_saturn_bigtts
# seed-icl-2.0：S_QKj17k802

# ════════════════════════════════════════════════════════════════════════════════
# 🎬 步骤5：视频合成 - 最终导出
# ════════════════════════════════════════════════════════════════════════════════

# --- 基础设置 ---
VIDEO_SIZE = "1280x720"                                # 视频导出尺寸 (可与 IMAGE_SIZE 不同)
VIDEO_OUTPUT_FPS = 30                                  # 视频导出帧率（步骤5最终成片）
VIDEO_CODEC = "hevc"                                   # 视频编码: h264(兼容性好), hevc(H.265, M1效率高, 体积小)
VIDEO_BITRATE_MODE = "quality"                         # 码率模式: auto(固定码率), quality(质量优先VBR)
VIDEO_QUALITY_LEVEL = 70                               # 质量系数 (0-100, 仅quality模式有效, 推荐60-75)
ENABLE_SUBTITLES = True                                # 是否启用字幕
DEFAULT_BGM_FILENAME = "The Sound of Slience.mp3"      # 默认背景音乐（music/ 下，None=无音乐）

# --- 音频控制 ---
BGM_DEFAULT_VOLUME = 0.1                               # 背景音乐音量 (0=静音, 1=原音, >1放大, 推荐0.03-0.20)
NARRATION_DEFAULT_VOLUME = 2.0                         # 口播音量 (0.5-3.0, 推荐0.8-1.5, >2.0有削波风险)
NARRATION_SPEED_FACTOR = 1.05                           # 口播变速系数 (1.0=原速)

# BGM响度标准化（解决音量起伏过大问题）
BGM_NORMALIZE_LOUDNESS = True                          # 是否启用BGM响度标准化（推荐开启）
BGM_TARGET_LOUDNESS = 15.0                             # 目标响度（均值）：数值越小越响，建议范围 16-23
BGM_LOUDNESS_RANGE = 6.5                               # 响度范围（标准差）：数值越小越平，建议范围 5-10

# 音频闪避（口播时自动降低BGM音量）
AUDIO_DUCKING_ENABLED = False                          # 是否启用音频闪避
AUDIO_DUCKING_STRENGTH = 0.5                           # BGM压低强度 (0-1)
AUDIO_DUCKING_SMOOTH_SECONDS = 0.12                    # 音量过渡平滑时间 (秒)

# --- 视觉效果时间控制 ---
OPENING_FADEIN_SECONDS = 1.0                           # 开场渐显时长 (秒)
ENDING_FADE_SECONDS = 2.0                              # 片尾淡出时长 (秒)

# --- 视频过渡效果 ---
ENABLE_TRANSITIONS = False                              # 是否启用视频过渡效果（默认关闭，确保向后兼容）
TRANSITION_DURATION = 0.8                               # 过渡时长 (秒, 建议0.3-1.5)
TRANSITION_STYLE = "slide_right"                        
# 过渡样式: crossfade(交叉淡化), fade_white(白场), fade_black(黑场), wipe_left(左擦除), wipe_right(右擦除),
# slide_left(左滑动), slide_right(右滑动), zoom_in(放大), zoom_out(缩小)

# --- 字幕样式配置 ---
# 字体路径建议：
# macOS 苹方字体: /System/Library/Fonts/PingFang.ttc
# macOS 宋体: /System/Library/Fonts/Supplemental/Songti.ttc
# Windows 微软雅黑: C:/Windows/Fonts/msyh.ttc
SUBTITLE_FONT_SIZE = 48                                # 字幕字体大小
SUBTITLE_FONT_FAMILY = "/System/Library/AssetsV2/com_apple_MobileAsset_Font8/86ba2c91f017a3749571a82f2c6d890ac7ffb2fb.asset/AssetData/PingFang.ttc"  # 字幕字体路径 (PingFang SC)
SUBTITLE_FONT_TTC_INDEX = 11                           # TTC字体索引 (11=PingFang SC Semibold)
SUBTITLE_COLOR = "white"                               # 字幕文字颜色
SUBTITLE_STROKE_COLOR = "black"                        # 字幕描边颜色
SUBTITLE_STROKE_WIDTH = 6                              # 字幕描边粗细
SUBTITLE_POSITION = ("center", "bottom")               # 字幕位置 (水平, 垂直)
SUBTITLE_MARGIN_BOTTOM = 60                            # 字幕距底部距离 (像素)
SUBTITLE_MAX_CHARS_PER_LINE = 20                       # 字幕每行最大字符数
SUBTITLE_MAX_LINES = 1                                 # 字幕最大行数
SUBTITLE_LINE_SPACING = 15                             # 字幕行间距 (像素)
SUBTITLE_LETTER_SPACING = 2                            # 字幕字间距 (像素, 0=正常)
SUBTITLE_BACKGROUND_COLOR = (0, 0, 0)                  # 字幕背景色 (RGB, None=透明)
SUBTITLE_BACKGROUND_OPACITY = 0.0                      # 字幕背景不透明度 (0-1)
SUBTITLE_BACKGROUND_H_PADDING = 20                     # 字幕背景水平内边距 (像素)
SUBTITLE_BACKGROUND_V_PADDING = 10                     # 字幕背景垂直内边距 (像素)
SUBTITLE_SHADOW_ENABLED = True                         # 是否启用字幕阴影
SUBTITLE_SHADOW_COLOR = "black"                        # 字幕阴影颜色
SUBTITLE_SHADOW_OFFSET = (0, 0)                        # 字幕阴影偏移 (x, y)

# --- 素材处理配置 ---
IMAGE_MATERIAL_TARGET_FPS = 15                         # 纯图片素材时的帧率
VIDEO_MATERIAL_REMOVE_AUDIO = True                     # 是否移除原视频素材中的音频
VIDEO_MATERIAL_LONGER_THAN_AUDIO_MODE = "crop"         # 长视频对齐方式: crop(截取前段)/compress(均匀压缩到音频时长)
VIDEO_MATERIAL_DURATION_ADJUST = "stretch"             # 兼容旧版配置：stretch≈compress, crop=裁剪（推荐改用 VIDEO_MATERIAL_LONGER_THAN_AUDIO_MODE）
VIDEO_MATERIAL_RESIZE_METHOD = "crop"                  # 视频尺寸调整方式: crop/stretch

# ════════════════════════════════════════════════════════════════════════════════
# 🖼️  步骤6：封面生成 - 宣传素材
# ════════════════════════════════════════════════════════════════════════════════

# 封面尺寸预设（运行步骤6时可选择）
COVER_IMAGE_SIZE_PRESETS = {
    "16:9": "3200x1800",   # 横屏
    "9:16": "1800x3200",   # 竖屏
    "4:3": "3000x2250",    # 传统横屏
    "3:4": "2250x3000",    # 传统竖屏
    "1:1": "2500x2500",    # 方形
}
DEFAULT_COVER_IMAGE_SIZE_KEY = "1:1"                   # 默认封面尺寸比例

COVER_IMAGE_MODEL = "gemini-3.1-flash-image-preview"   # 封面图像生成模型
COVER_IMAGE_SERVER = "google_adc"                       # 封面图像生成供应商: google_adc=本机ADC/Vertex AI，google=GOOGLE_CLOUD_API_KEY
COVER_IMAGE_STYLE = "cover06"                          # 封面风格预设 (详见 prompts.py)
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

# 允许通过 .env 覆盖声音复刻音色ID，避免遗漏在代码配置中
VOICE = os.getenv("BYTEDANCE_TTS_VOICE_ID", VOICE).strip() or VOICE


def get_generation_params() -> Dict[str, object]:
    """返回生成参数字典（供 CLI 使用）。"""
    return {
        "num_segments": NUM_SEGMENTS,
        "image_size": IMAGE_SIZE,
        "video_size": VIDEO_SIZE,
        "llm_model_step2": LLM_MODEL_STEP2,
        "llm_server_step2": LLM_SERVER_STEP2,
        "llm_base_url_step2": LLM_BASE_URL_STEP2,
        "image_server": IMAGE_SERVER,
        "image_model": IMAGE_MODEL,
        "llm_server_step3": LLM_SERVER_STEP3,
        "llm_base_url_step3": LLM_BASE_URL_STEP3,
        "llm_model_step3": LLM_MODEL_STEP3,
        "voice": VOICE,
        "resource_id": RESOURCE_ID,
        "tts_model": TTS_MODEL,
        "tts_emotion": TTS_EMOTION,
        "tts_emotion_scale": TTS_EMOTION_SCALE,
        "tts_speech_rate": TTS_SPEECH_RATE,
        "tts_loudness_rate": TTS_LOUDNESS_RATE,
        "mute_cut_threshold": MUTE_CUT_THRESHOLD,
        "mute_cut_min_silence_ms": MUTE_CUT_MIN_SILENCE_MS,
        "mute_cut_remain_ms": MUTE_CUT_REMAIN_MS,
        "output_dir": "output",
        "image_style_preset": IMAGE_STYLE_PRESET,
        "images_method": IMAGES_METHOD,
        "enable_subtitles": ENABLE_SUBTITLES,
        "bgm_filename": DEFAULT_BGM_FILENAME,
        "opening_quote": OPENING_QUOTE,
        "cover_image_model": COVER_IMAGE_MODEL,
        "cover_image_server": COVER_IMAGE_SERVER,
        "cover_image_style": COVER_IMAGE_STYLE,
        "cover_image_count": COVER_IMAGE_COUNT,
    }


class Config:
    """系统配置类：用户参数由模块常量注入，密钥与校验逻辑定义在类上。"""

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    MIMO_API_KEY = os.getenv("MIMO_API_KEY")
    SEEDREAM_API_KEY = os.getenv("SEEDREAM_API_KEY")
    SILICONFLOW_KEY = os.getenv("SILICONFLOW_KEY")
    GOOGLE_CLOUD_API_KEY = os.getenv("GOOGLE_CLOUD_API_KEY")
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GOOGLE_PROJECT_ID")
    GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    BYTEDANCE_TTS_API_KEY = os.getenv("BYTEDANCE_TTS_API_KEY")
    BYTEDANCE_TTS_VERIFY_SSL = os.getenv("BYTEDANCE_TTS_VERIFY_SSL", "true").lower() == "true"

    SILICONFLOW_IMAGE_BASE_URL = "https://api.siliconflow.cn/v1/images/generations"
    ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
    DEFAULT_IMAGE_SIZE = "1664x928"
    DEFAULT_VOICE = VOICE
    DEFAULT_OUTPUT_DIR = "output"

    SUPPORTED_LLM_SERVERS = ["openrouter", "siliconflow"]
    SUPPORTED_IMAGE_SERVERS = ["doubao", "siliconflow", "google", "google_adc"]
    SUPPORTED_TTS_SERVERS = ["bytedance"]
    SUPPORTED_IMAGE_METHODS = ["keywords", "description"]
    RECOMMENDED_MODELS = {
        "llm": {
            "openrouter": [LLM_MODEL_STEP2],
            "siliconflow": [LLM_MODEL_STEP2],
        },
        "image": {
            "doubao": [
                "doubao-seedream-5-0-260128",
                "doubao-seedream-4-0-250828",
                "doubao-seedream-3-0-t2i-250415",
            ],
            "siliconflow": ["stabilityai/stable-diffusion-3-5-large", "black-forest-labs/FLUX.1-schnell"],
            "google": ["gemini-3.1-flash-image-preview"],
            "google_adc": ["gemini-3.1-flash-image-preview"],
        },
        "voice": [
            "zh_male_yuanboxiaoshu_moon_bigtts",
            "zh_male_haoyuxiaoge_moon_bigtts",
            "zh_female_wenrouxiaoya_moon_bigtts",
            "zh_female_daimengchuanmei_moon_bigtts",
        ],
    }
    SUPPORTED_VIDEO_SIZES = {
        "横屏16:9": ["1280x720", "1664x928", "1920x1080", "2560x1440"],
        "竖屏9:16": ["720x1280", "1080x1920"],
        "方形1:1": ["1024x1024", "1664x1664"],
        "竖屏3:4": ["864x1152", "1536x2048", "2250x3000"],
    }
    SUPPORTED_QWEN_IMAGE_SIZES = [
        "1328x1328", "1664x928", "928x1664", "1472x1140",
        "1140x1472", "1584x1056", "1056x1584",
    ]
    SEEDREAM_V4_MIN_SIZE = (1280, 720)
    SEEDREAM_V4_MAX_SIZE = (4096, 4096)
    SEEDREAM_V5_MIN_PIXELS = 3686400
    SEEDREAM_V5_MAX_SIZE = (4096, 4096)
    SEEDREAM_V3_MIN_SIZE = (512, 512)
    SEEDREAM_V3_MAX_SIZE = (2048, 2048)
    SERVER_TYPE_MAP = {"image_server": "image", "tts_server": "voice", "text": "text"}
    MIN_NUM_SEGMENTS = 5
    MAX_NUM_SEGMENTS = 100
    SPEECH_SPEED_WPM = 250

    @classmethod
    def validate_api_keys(cls) -> Dict[str, bool]:
        """验证API密钥配置"""
        return {
            "openrouter": bool(cls.OPENROUTER_API_KEY),
            "mimo": bool(cls.MIMO_API_KEY),
            "siliconflow": bool(cls.SILICONFLOW_KEY),
            "seedream": bool(cls.SEEDREAM_API_KEY),
            "google": bool(cls.GOOGLE_CLOUD_API_KEY or cls.GOOGLE_CLOUD_PROJECT),
            "bytedance_tts": bool(cls.BYTEDANCE_TTS_API_KEY),
        }

    @classmethod
    def get_missing_keys(cls) -> List[str]:
        """获取缺失的必需API密钥"""
        missing = []
        key_status = cls.validate_api_keys()
        llm_servers = {cls.LLM_SERVER_STEP2, cls.LLM_SERVER_STEP3}
        if "siliconflow" in llm_servers and not key_status["siliconflow"]:
            missing.append("SILICONFLOW_KEY")
        if "openrouter" in llm_servers and not key_status["openrouter"]:
            missing.append("OPENROUTER_API_KEY")
        if not (key_status["seedream"] or key_status["siliconflow"] or key_status["google"]):
            missing.append("SEEDREAM_API_KEY 或 SILICONFLOW_KEY 或 GOOGLE_CLOUD_API_KEY")
        if not key_status["bytedance_tts"]:
            missing.append("BYTEDANCE_TTS_API_KEY")
        return missing

    @classmethod
    def get_required_keys_for_config(cls, image_server: str, tts_server: str, *llm_key_names: str) -> List[str]:
        """根据服务配置返回所需的API密钥列表"""
        required_keys = []
        for key_name in llm_key_names:
            if key_name and key_name not in required_keys:
                required_keys.append(key_name)

        if image_server == "doubao":
            required_keys.append("SEEDREAM_API_KEY")
        elif image_server == "siliconflow" and "SILICONFLOW_KEY" not in required_keys:
            required_keys.append("SILICONFLOW_KEY")
        elif image_server == "google":
            required_keys.append("GOOGLE_CLOUD_API_KEY")

        if tts_server == "bytedance":
            required_keys.append("BYTEDANCE_TTS_API_KEY")
        return required_keys

    @classmethod
    def validate_image_size(cls, size: str, model: str) -> bool:
        """验证图像尺寸是否符合模型要求"""
        if not size:
            return False
        size = size.lower().replace("×", "x").replace("*", "x")
        if "x" not in size:
            return False
        try:
            width, height = map(int, size.split("x"))
        except ValueError:
            return False
        if "qwen" in model.lower():
            return size in cls.SUPPORTED_QWEN_IMAGE_SIZES
        if "doubao" in model.lower():
            if "seedream-5" in model.lower():
                return width * height >= cls.SEEDREAM_V5_MIN_PIXELS and width <= 4096 and height <= 4096
            if "seedream-4" in model.lower():
                return 1280 <= width <= 4096 and 720 <= height <= 4096
            if "seedream-3" in model.lower():
                return 512 <= width <= 2048 and 512 <= height <= 2048
        return True

    @classmethod
    def validate_model_provider_pair(cls, model_type: str, server: str, model: str) -> None:
        """严格校验模型与供应商组合，不允许自动推断。"""
        server = (server or "").strip().lower()
        model = (model or "").strip()
        lower_model = model.lower()

        if not server:
            raise ValueError(f"{model_type} 的供应商不能为空")
        if not model:
            raise ValueError(f"{model_type} 的模型不能为空")

        if model_type == "image":
            if server == "doubao":
                if "doubao" not in lower_model and "seedream" not in lower_model:
                    raise ValueError(f"图像模型 {model} 与供应商 {server} 不匹配")
                return
            if server == "siliconflow":
                if "doubao" in lower_model or "seedream" in lower_model:
                    raise ValueError(f"图像模型 {model} 与供应商 {server} 不匹配")
                return
            if server in {"google", "google_adc"}:
                if "gemini" not in lower_model and "imagen" not in lower_model:
                    raise ValueError(f"图像模型 {model} 与供应商 {server} 不匹配")
                return
            raise ValueError(f"不支持的图像服务商: {server}，支持的服务商: {cls.SUPPORTED_IMAGE_SERVERS}")

        if model_type == "voice":
            if server not in cls.SUPPORTED_TTS_SERVERS:
                raise ValueError(f"不支持的TTS服务商: {server}，支持的服务商: {cls.SUPPORTED_TTS_SERVERS}")
            return

        raise ValueError(f"不支持的模型类型: {model_type}")

    @classmethod
    def validate_parameters(
        cls,
        num_segments: int,
        llm_server: str,
        image_server: str,
        tts_server: str,
        image_model: str,
        image_size: str,
        *,
        images_method: str = None,
        llm_model: str = None,
    ) -> None:
        """验证所有参数的有效性"""
        if not cls.MIN_NUM_SEGMENTS <= num_segments <= cls.MAX_NUM_SEGMENTS:
            raise ValueError(f"num_segments必须在{cls.MIN_NUM_SEGMENTS}-{cls.MAX_NUM_SEGMENTS}之间")
        if llm_server not in cls.SUPPORTED_LLM_SERVERS:
            raise ValueError(f"不支持的LLM服务商: {llm_server}，支持的服务商: {cls.SUPPORTED_LLM_SERVERS}")
        if llm_model is not None and not str(llm_model).strip():
            raise ValueError("LLM模型不能为空")
        if image_server not in cls.SUPPORTED_IMAGE_SERVERS:
            raise ValueError(f"不支持的图像服务商: {image_server}，支持的服务商: {cls.SUPPORTED_IMAGE_SERVERS}")
        if tts_server not in cls.SUPPORTED_TTS_SERVERS:
            raise ValueError(f"不支持的TTS服务商: {tts_server}，支持的服务商: {cls.SUPPORTED_TTS_SERVERS}")
        cls.validate_model_provider_pair("image", image_server, image_model)
        if images_method and images_method not in cls.SUPPORTED_IMAGE_METHODS:
            raise ValueError(f"不支持的图像生成方法: {images_method}，支持的方法: {cls.SUPPORTED_IMAGE_METHODS}")
        if not cls.validate_image_size(image_size, image_model):
            raise ValueError(
                f"图像尺寸 {image_size} 不符合模型 {image_model} 的要求。\n"
                f"Qwen模型支持的固定尺寸: {cls.SUPPORTED_QWEN_IMAGE_SIZES}\n"
                f"Doubao-5模型支持: 总像素不少于 {cls.SEEDREAM_V5_MIN_PIXELS}，宽高不超过 4096\n"
                f"Doubao-4模型支持: 1280x720 到 4096x4096 之间的任意尺寸\n"
                f"Doubao-3模型支持: 512x512 到 2048x2048 之间的任意尺寸\n"
                f"腾讯混元图像支持: 宽高范围 512-2048，面积不超过 1024x1024"
            )


# 将用户配置区的模块常量挂到 Config，避免在类体内逐字段复制
for _name, _value in list(globals().items()):
    if _name.isupper() and not hasattr(Config, _name) and not isinstance(_value, type):
        setattr(Config, _name, _value)

config = Config()
