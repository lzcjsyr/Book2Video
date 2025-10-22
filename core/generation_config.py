"""
视频生成配置数据类
集中管理视频生成流程的所有参数，避免函数参数过多
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VideoGenerationConfig:
    """视频生成配置类，封装所有生成参数"""
    
    # ==================== 输入输出配置 ====================
    input_file: str
    output_dir: str
    
    # ==================== 内容生成参数 ====================
    target_length: int = 800
    num_segments: int = 6
    
    # ==================== LLM 配置 ====================
    llm_server_step1: str = "openrouter"
    llm_model_step1: str = "moonshotai/Kimi-K2-Instruct-0905"
    llm_server_step2: str = "openrouter"
    llm_model_step2: str = "moonshotai/Kimi-K2-Instruct-0905"
    
    # ==================== 图像生成配置 ====================
    image_server: str = "doubao"
    image_model: str = "doubao-seedream-4-0-250828"
    image_size: str = "1664x928"
    image_style_preset: str = "style01"
    opening_image_style: str = "des01"
    images_method: str = "keywords"  # keywords / description
    
    # ==================== 语音合成配置 ====================
    tts_server: str = "bytedance"
    voice: str = "zh_male_yuanboxiaoshu_moon_bigtts"
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


@dataclass
class StepExecutionConfig:
    """单步执行配置（用于分步模式）"""
    
    project_output_dir: str
    
    # 可选参数（不同步骤需要不同参数）
    llm_server: Optional[str] = None
    llm_model: Optional[str] = None
    image_server: Optional[str] = None
    image_model: Optional[str] = None
    image_size: Optional[str] = None
    image_style_preset: Optional[str] = None
    opening_image_style: Optional[str] = None
    images_method: Optional[str] = None
    tts_server: Optional[str] = None
    voice: Optional[str] = None
    speech_rate: int = 0
    loudness_rate: int = 0
    emotion: str = "neutral"
    emotion_scale: int = 4
    mute_cut_remain_ms: int = 100
    mute_cut_threshold: int = 400
    enable_subtitles: bool = True
    bgm_filename: Optional[str] = None
    opening_quote: bool = True
    target_segments: Optional[list] = None
    regenerate_opening: bool = True
    
    @classmethod
    def from_generation_config(
        cls, 
        gen_config: VideoGenerationConfig,
        project_output_dir: str,
        step_number: int = 2
    ) -> "StepExecutionConfig":
        """
        从 VideoGenerationConfig 创建步骤执行配置
        
        Args:
            gen_config: 视频生成配置
            project_output_dir: 项目输出目录
            step_number: 步骤号（1或2），用于选择对应的LLM配置
            
        Returns:
            StepExecutionConfig: 步骤执行配置
        """
        # 根据步骤号选择LLM配置
        if step_number == 1:
            llm_server = gen_config.llm_server_step1
            llm_model = gen_config.llm_model_step1
        else:  # step 2 或其他
            llm_server = gen_config.llm_server_step2
            llm_model = gen_config.llm_model_step2
            
        return cls(
            project_output_dir=project_output_dir,
            llm_server=llm_server,
            llm_model=llm_model,
            image_server=gen_config.image_server,
            image_model=gen_config.image_model,
            image_size=gen_config.image_size,
            image_style_preset=gen_config.image_style_preset,
            opening_image_style=gen_config.opening_image_style,
            images_method=gen_config.images_method,
            tts_server=gen_config.tts_server,
            voice=gen_config.voice,
            speech_rate=gen_config.speech_rate,
            loudness_rate=gen_config.loudness_rate,
            emotion=gen_config.emotion,
            emotion_scale=gen_config.emotion_scale,
            mute_cut_remain_ms=gen_config.mute_cut_remain_ms,
            mute_cut_threshold=gen_config.mute_cut_threshold,
            enable_subtitles=gen_config.enable_subtitles,
            bgm_filename=gen_config.bgm_filename,
            opening_quote=gen_config.opening_quote,
        )


__all__ = ['VideoGenerationConfig', 'StepExecutionConfig']

