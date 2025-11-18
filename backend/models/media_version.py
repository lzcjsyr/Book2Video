"""
媒体资源版本管理模型

支持图片和音频的多版本管理，每个资源可以有多个版本，
用户可以选择活跃版本用于最终合成。
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum, Text, ForeignKey
from sqlalchemy.sql import func
from datetime import datetime
import enum

from backend.database import Base


class MediaType(str, enum.Enum):
    """媒体类型枚举"""
    IMAGE = "image"
    AUDIO = "audio"


class GenerationMethod(str, enum.Enum):
    """生成方式枚举"""
    AI_GENERATED = "ai_generated"       # AI生成
    UPLOADED = "uploaded"               # 用户上传
    EDITED = "edited"                   # 编辑后保存


class MediaVersion(Base):
    """媒体资源版本模型"""
    __tablename__ = "media_versions"

    id = Column(Integer, primary_key=True, index=True)

    # 关联项目
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)

    # 媒体信息
    media_type = Column(Enum(MediaType), nullable=False, index=True)  # 媒体类型
    filename = Column(String(500), nullable=False, index=True)         # 文件名（如 opening.png, voice_1.wav）
    segment_index = Column(Integer, nullable=True)                     # 段落索引（如果适用）

    # 版本信息
    version = Column(Integer, nullable=False)                          # 版本号（从1开始）
    is_active = Column(Integer, default=0, index=True)                 # 是否为活跃版本（用于合成）

    # 存储信息
    local_path = Column(String(1000), nullable=True)                   # 本地路径
    cloud_url = Column(String(2000), nullable=True)                    # 云存储URL

    # 生成信息
    generation_method = Column(Enum(GenerationMethod), nullable=False)
    generation_params = Column(JSON, nullable=True)                    # 生成参数
    # 示例: {
    #   "prompt": "温馨的家庭场景",
    #   "model": "seedream-4.0",
    #   "voice": "zh_male_yuanboxiaoshu",
    #   "original_filename": "my_image.png"
    # }

    # 元数据
    file_size_bytes = Column(Integer, default=0)                       # 文件大小
    duration_seconds = Column(Integer, nullable=True)                  # 音频时长（仅音频）
    width = Column(Integer, nullable=True)                             # 图片宽度（仅图片）
    height = Column(Integer, nullable=True)                            # 图片高度（仅图片）

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100), nullable=True)                    # 创建者（用户ID或"system"）

    # 备注
    note = Column(Text, nullable=True)                                 # 用户备注

    def __repr__(self):
        return f"<MediaVersion(id={self.id}, project_id={self.project_id}, filename='{self.filename}', version={self.version}, active={bool(self.is_active)})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "media_type": self.media_type.value if self.media_type else None,
            "filename": self.filename,
            "segment_index": self.segment_index,
            "version": self.version,
            "is_active": bool(self.is_active),
            "local_path": self.local_path,
            "cloud_url": self.cloud_url,
            "generation_method": self.generation_method.value if self.generation_method else None,
            "generation_params": self.generation_params,
            "file_size_bytes": self.file_size_bytes,
            "duration_seconds": self.duration_seconds,
            "width": self.width,
            "height": self.height,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "note": self.note,
        }
