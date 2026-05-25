"""
视频生成配置数据类
集中管理视频生成流程的所有参数，避免函数参数过多
"""

from dataclasses import dataclass
from typing import Optional


def _infer_image_server_from_model(model: str) -> str:
    """根据图像模型名推断供应商（用于兼容旧参数缺省场景）。"""
    lower_model = (model or "").strip().lower()
    if "doubao" in lower_model or "seedream" in lower_model:
        return "doubao"
    if "gemini" in lower_model or "imagen" in lower_model:
        return "google"
    if lower_model:
        return "siliconflow"
    return ""


def _resolve_cover_image_server(image_server: str, cover_model: str) -> str:
    inferred = _infer_image_server_from_model(cover_model)
    if inferred == "google" and image_server == "google_adc":
        return "google_adc"
    return inferred or image_server


# get_generation_params() 键名 -> VideoGenerationConfig 字段名
_CLI_PARAM_ALIASES = (
    ("tts_emotion", "emotion"),
    ("tts_emotion_scale", "emotion_scale"),
    ("tts_speech_rate", "speech_rate"),
    ("tts_loudness_rate", "loudness_rate"),
)


@dataclass
class VideoGenerationConfig:
    """视频生成配置类，封装所有生成参数"""
    
    # ==================== 输入输出配置 ====================
    input_file: str
    output_dir: str
    
    # ==================== 内容生成参数 ====================
    num_segments: int = 6
    
    # ==================== LLM 配置 ====================
    llm_server_step2: str = ""
    llm_base_url_step2: str = ""
    llm_model_step2: str = "Pro/moonshotai/Kimi-K2.6"
    llm_server_step3: str = ""
    llm_base_url_step3: str = ""
    llm_model_step3: str = "Pro/moonshotai/Kimi-K2.6"
    
    # ==================== 图像生成配置 ====================
    image_server: str = ""
    image_model: str = "doubao-seedream-4-0-250828"
    image_size: str = "1664x928"
    image_style_preset: str = "style01"
    images_method: str = "keywords"  # keywords / description
    
    # ==================== 语音合成配置 ====================
    tts_server: str = "bytedance"
    voice: str = "zh_male_yuanboxiaoshu_moon_bigtts"
    tts_model: str = "seed-tts-2.0-expressive"
    speech_rate: int = 0
    loudness_rate: int = 0
    emotion: str = "neutral"
    emotion_scale: int = 4
    mute_cut_remain_ms: int = 100
    mute_cut_threshold: int = 400

    # ==================== 视频合成配置 ====================
    video_size: Optional[str] = None  # None 则使用 image_size
    enable_subtitles: bool = True
    opening_quote: bool = True
    bgm_filename: Optional[str] = None
    
    # ==================== 封面图配置 ====================
    cover_image_size: Optional[str] = None  # None 则使用 image_size
    cover_image_model: Optional[str] = None  # None 则使用 image_model
    cover_image_server: str = ""
    cover_image_style: str = "cover01"
    cover_image_count: int = 1
    
    def __post_init__(self):
        """初始化后的验证和默认值设置"""
        # 设置默认值
        if self.video_size is None:
            self.video_size = self.image_size
        if self.cover_image_size is None:
            self.cover_image_size = self.image_size
        if self.cover_image_model is None:
            self.cover_image_model = self.image_model
        if not self.cover_image_server:
            self.cover_image_server = _resolve_cover_image_server(self.image_server, self.cover_image_model)
    
    @classmethod
    def from_cli_params(
        cls,
        params: dict,
        *,
        input_file: str,
        output_dir: str,
        **overrides,
    ) -> "VideoGenerationConfig":
        """从 get_generation_params() 风格字典创建配置（含 CLI 字段别名）。"""
        data = dict(params)
        for src, dst in _CLI_PARAM_ALIASES:
            if src in data:
                data[dst] = data.pop(src)
        data.update(input_file=input_file, output_dir=output_dir, **overrides)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, params: dict) -> "VideoGenerationConfig":
        """
        从字典创建配置对象
        
        Args:
            params: 参数字典
            
        Returns:
            VideoGenerationConfig: 配置对象
        """
        # 过滤掉不在 dataclass 字段中的键
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_params = {k: v for k, v in params.items() if k in valid_fields}
        return cls(**filtered_params)
    
    def to_dict(self) -> dict:
        """
        转换为字典
        
        Returns:
            dict: 参数字典
        """
        from dataclasses import asdict
        return asdict(self)
    
    def get_effective_video_size(self) -> str:
        """获取实际使用的视频尺寸"""
        return self.video_size or self.image_size
    
    def get_effective_cover_size(self) -> str:
        """获取实际使用的封面尺寸"""
        return self.cover_image_size or self.image_size
    
    def get_effective_cover_model(self) -> str:
        """获取实际使用的封面模型"""
        return self.cover_image_model or self.image_model

    def get_effective_cover_server(self) -> str:
        """获取实际使用的封面供应商"""
        return self.cover_image_server or _resolve_cover_image_server(
            self.image_server,
            self.cover_image_model or "",
        )


__all__ = ["VideoGenerationConfig"]
