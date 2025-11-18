"""
项目数据模型 V2 - 支持云存储
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum, Text, Boolean
from sqlalchemy.sql import func
from datetime import datetime
import enum

from backend.database import Base


class ProjectStatus(str, enum.Enum):
    """项目状态枚举"""
    CREATED = "created"
    PROCESSING = "processing"
    STEP1_COMPLETED = "step1_completed"
    STEP1_5_COMPLETED = "step1_5_completed"
    STEP2_COMPLETED = "step2_completed"
    STEP3_COMPLETED = "step3_completed"
    STEP4_COMPLETED = "step4_completed"
    STEP5_COMPLETED = "step5_completed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Project(Base):
    """项目模型 - 支持云存储"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.CREATED, index=True)

    # 输入文件信息
    input_filename = Column(String(500), nullable=True)
    input_file_path = Column(String(1000), nullable=True)  # 本地路径（兼容）
    input_file_url = Column(String(2000), nullable=True)   # 云存储URL ✨

    # 项目路径
    project_dir = Column(String(1000), nullable=False)  # 本地工作目录

    # 配置参数（JSON格式）
    config = Column(JSON, nullable=False)

    # 步骤完成状态
    step1_completed = Column(Integer, default=0)
    step1_5_completed = Column(Integer, default=0)
    step2_completed = Column(Integer, default=0)
    step3_completed = Column(Integer, default=0)
    step4_completed = Column(Integer, default=0)
    step5_completed = Column(Integer, default=0)
    step6_completed = Column(Integer, default=0)

    # 当前执行状态
    current_step = Column(Integer, default=0)
    current_step_progress = Column(Integer, default=0)

    # 错误信息
    error_message = Column(Text, nullable=True)

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # ==================== 核心数据（JSON字段 - 已持久化） ✅ ====================
    raw_data = Column(JSON, nullable=True)           # raw.json完整内容
    script_data = Column(JSON, nullable=True)        # script.json完整内容
    keywords_data = Column(JSON, nullable=True)      # keywords.json完整内容

    # ==================== 文件存储（云存储URL） ✨ ====================

    # 云存储标志
    use_cloud_storage = Column(Boolean, default=True)  # 是否使用云存储

    # 图片云存储URL（JSON数组）
    images_urls = Column(JSON, nullable=True)
    # 格式: {
    #   "opening": "https://cdn.example.com/projects/1/images/opening.png",
    #   "segment_1": "https://cdn.example.com/projects/1/images/segment_1.png",
    #   "segment_2": "https://cdn.example.com/projects/1/images/segment_2.png",
    #   ...
    # }

    # 音频云存储URL（JSON数组）
    audio_urls = Column(JSON, nullable=True)
    # 格式: {
    #   "opening": "https://cdn.example.com/projects/1/voice/opening.mp3",
    #   "segment_1": "https://cdn.example.com/projects/1/voice/voice_1.wav",
    #   ...
    # }

    # 最终视频云存储URL
    final_video_url = Column(String(2000), nullable=True)

    # 封面图片云存储URL（JSON数组）
    cover_image_urls = Column(JSON, nullable=True)
    # 格式: ["https://...", "https://...", ...]

    # SRT字幕云存储URL
    srt_url = Column(String(2000), nullable=True)

    # ==================== 本地路径（兼容旧版本，用于备份） ====================
    final_video_path = Column(String(1000), nullable=True)  # 本地备份路径
    cover_image_paths = Column(JSON, nullable=True)         # 本地备份路径

    # ==================== 云存储元数据 ====================
    storage_provider = Column(String(50), nullable=True)  # 存储提供商
    storage_bucket = Column(String(200), nullable=True)   # Bucket名称
    storage_size_bytes = Column(Integer, default=0)       # 总存储大小（字节）
    cloud_uploaded_at = Column(DateTime(timezone=True), nullable=True)  # 上传时间

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value if self.status else None,
            "input_filename": self.input_filename,
            "input_file_url": self.input_file_url,  # 优先使用云存储URL
            "project_dir": self.project_dir,
            "config": self.config,
            "step1_completed": bool(self.step1_completed),
            "step1_5_completed": bool(self.step1_5_completed),
            "step2_completed": bool(self.step2_completed),
            "step3_completed": bool(self.step3_completed),
            "step4_completed": bool(self.step4_completed),
            "step5_completed": bool(self.step5_completed),
            "step6_completed": bool(self.step6_completed),
            "current_step": self.current_step,
            "current_step_progress": self.current_step_progress,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,

            # 核心数据
            "raw_data": self.raw_data,
            "script_data": self.script_data,
            "keywords_data": self.keywords_data,

            # 云存储URL
            "use_cloud_storage": self.use_cloud_storage,
            "images_urls": self.images_urls,
            "audio_urls": self.audio_urls,
            "final_video_url": self.final_video_url,
            "cover_image_urls": self.cover_image_urls,
            "srt_url": self.srt_url,

            # 云存储元数据
            "storage_provider": self.storage_provider,
            "storage_size_bytes": self.storage_size_bytes,
            "cloud_uploaded_at": self.cloud_uploaded_at.isoformat() if self.cloud_uploaded_at else None,
        }
