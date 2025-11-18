"""
媒体版本管理服务

自动为生成的图片和音频创建版本记录
"""
import os
from datetime import datetime
from typing import Optional, Dict
from sqlalchemy.orm import Session

from backend.models import MediaVersion, MediaType, GenerationMethod


def create_media_version(
    db: Session,
    project_id: int,
    media_type: MediaType,
    filename: str,
    local_path: str,
    cloud_url: Optional[str] = None,
    generation_method: GenerationMethod = GenerationMethod.AI_GENERATED,
    generation_params: Optional[Dict] = None,
    segment_index: Optional[int] = None,
    set_as_active: bool = True,
    created_by: str = "system"
) -> MediaVersion:
    """
    创建新的媒体版本记录

    Args:
        db: 数据库会话
        project_id: 项目ID
        media_type: 媒体类型
        filename: 文件名
        local_path: 本地路径
        cloud_url: 云存储URL（可选）
        generation_method: 生成方式
        generation_params: 生成参数
        segment_index: 段落索引（可选）
        set_as_active: 是否设为活跃版本
        created_by: 创建者

    Returns:
        创建的MediaVersion对象
    """
    # 获取下一个版本号
    max_version = db.query(MediaVersion).filter(
        MediaVersion.project_id == project_id,
        MediaVersion.media_type == media_type,
        MediaVersion.filename == filename
    ).count()
    next_version = max_version + 1

    # 获取文件信息
    file_size = os.path.getsize(local_path) if os.path.exists(local_path) else 0

    # 获取媒体特定信息
    width, height, duration = None, None, None

    if media_type == MediaType.IMAGE:
        try:
            from PIL import Image
            with Image.open(local_path) as img:
                width, height = img.size
        except Exception as e:
            print(f"获取图片尺寸失败: {str(e)}")

    elif media_type == MediaType.AUDIO:
        try:
            from moviepy.editor import AudioFileClip
            audio = AudioFileClip(local_path)
            duration = int(audio.duration)
            audio.close()
        except Exception as e:
            print(f"获取音频时长失败: {str(e)}")

    # 如果设为活跃，取消其他版本的活跃状态
    if set_as_active:
        db.query(MediaVersion).filter(
            MediaVersion.project_id == project_id,
            MediaVersion.media_type == media_type,
            MediaVersion.filename == filename,
            MediaVersion.is_active == 1
        ).update({"is_active": 0})

    # 创建新版本记录
    new_version = MediaVersion(
        project_id=project_id,
        media_type=media_type,
        filename=filename,
        segment_index=segment_index,
        version=next_version,
        is_active=1 if set_as_active else 0,
        local_path=local_path,
        cloud_url=cloud_url,
        generation_method=generation_method,
        generation_params=generation_params or {},
        file_size_bytes=file_size,
        duration_seconds=duration,
        width=width,
        height=height,
        created_by=created_by
    )

    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    return new_version


def batch_create_image_versions(
    db: Session,
    project_id: int,
    images_dir: str,
    images_urls: Dict[str, str] = None,
    generation_params: Optional[Dict] = None
) -> int:
    """
    批量创建图片版本记录

    Args:
        db: 数据库会话
        project_id: 项目ID
        images_dir: 图片目录
        images_urls: 图片URL映射（文件名 -> 云存储URL）
        generation_params: 生成参数

    Returns:
        创建的版本数量
    """
    if not os.path.exists(images_dir):
        return 0

    images_urls = images_urls or {}
    count = 0

    for filename in os.listdir(images_dir):
        if not filename.endswith(('.png', '.jpg', '.jpeg')):
            continue

        local_path = os.path.join(images_dir, filename)
        cloud_url = images_urls.get(filename)

        # 提取段落索引
        segment_index = None
        if filename.startswith('segment_'):
            try:
                segment_index = int(filename.split('_')[1].split('.')[0])
            except:
                pass

        create_media_version(
            db=db,
            project_id=project_id,
            media_type=MediaType.IMAGE,
            filename=filename,
            local_path=local_path,
            cloud_url=cloud_url,
            generation_method=GenerationMethod.AI_GENERATED,
            generation_params=generation_params,
            segment_index=segment_index,
            set_as_active=True,
            created_by="system"
        )
        count += 1

    return count


def batch_create_audio_versions(
    db: Session,
    project_id: int,
    audio_dir: str,
    audio_urls: Dict[str, str] = None,
    generation_params: Optional[Dict] = None
) -> int:
    """
    批量创建音频版本记录

    Args:
        db: 数据库会话
        project_id: 项目ID
        audio_dir: 音频目录
        audio_urls: 音频URL映射（文件名 -> 云存储URL）
        generation_params: 生成参数

    Returns:
        创建的版本数量
    """
    if not os.path.exists(audio_dir):
        return 0

    audio_urls = audio_urls or {}
    count = 0

    for filename in os.listdir(audio_dir):
        if not filename.endswith(('.mp3', '.wav', '.m4a')):
            continue

        local_path = os.path.join(audio_dir, filename)
        cloud_url = audio_urls.get(filename)

        # 提取段落索引
        segment_index = None
        if filename.startswith('voice_'):
            try:
                segment_index = int(filename.split('_')[1].split('.')[0])
            except:
                pass

        create_media_version(
            db=db,
            project_id=project_id,
            media_type=MediaType.AUDIO,
            filename=filename,
            local_path=local_path,
            cloud_url=cloud_url,
            generation_method=GenerationMethod.AI_GENERATED,
            generation_params=generation_params,
            segment_index=segment_index,
            set_as_active=True,
            created_by="system"
        )
        count += 1

    return count


def get_active_media_urls(db: Session, project_id: int) -> Dict[str, Dict]:
    """
    获取项目的所有活跃媒体资源URL

    Args:
        db: 数据库会话
        project_id: 项目ID

    Returns:
        包含images和audio的字典
    """
    active_versions = db.query(MediaVersion).filter(
        MediaVersion.project_id == project_id,
        MediaVersion.is_active == 1
    ).all()

    images = {}
    audio = {}

    for v in active_versions:
        url = v.cloud_url or v.local_path
        if v.media_type == MediaType.IMAGE:
            images[v.filename] = url
        elif v.media_type == MediaType.AUDIO:
            audio[v.filename] = url

    return {"images": images, "audio": audio}
