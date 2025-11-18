"""
媒体版本管理API

提供图片和音频的多版本管理功能：
- 查看所有版本
- 设置活跃版本
- 生成新版本
- 上传新版本
- 删除版本
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import json

from backend.database import get_db
from backend.models import Project, MediaVersion, MediaType, GenerationMethod
from backend.services.cloud_storage import get_storage_provider, upload_project_file
from backend.tasks.video_generation import regenerate_images

router = APIRouter(prefix="/media-versions", tags=["media-versions"])


# ==================== 查询版本 ====================

@router.get("/projects/{project_id}/images/{filename}/versions")
async def get_image_versions(
    project_id: int,
    filename: str,
    db: Session = Depends(get_db)
):
    """获取指定图片的所有版本"""
    versions = db.query(MediaVersion).filter(
        MediaVersion.project_id == project_id,
        MediaVersion.media_type == MediaType.IMAGE,
        MediaVersion.filename == filename
    ).order_by(MediaVersion.version.desc()).all()

    return {
        "filename": filename,
        "versions": [v.to_dict() for v in versions],
        "active_version": next((v.version for v in versions if v.is_active), None)
    }


@router.get("/projects/{project_id}/audio/{filename}/versions")
async def get_audio_versions(
    project_id: int,
    filename: str,
    db: Session = Depends(get_db)
):
    """获取指定音频的所有版本"""
    versions = db.query(MediaVersion).filter(
        MediaVersion.project_id == project_id,
        MediaVersion.media_type == MediaType.AUDIO,
        MediaVersion.filename == filename
    ).order_by(MediaVersion.version.desc()).all()

    return {
        "filename": filename,
        "versions": [v.to_dict() for v in versions],
        "active_version": next((v.version for v in versions if v.is_active), None)
    }


@router.get("/projects/{project_id}/all-versions")
async def get_all_media_versions(
    project_id: int,
    media_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取项目的所有媒体资源版本"""
    query = db.query(MediaVersion).filter(MediaVersion.project_id == project_id)

    if media_type:
        query = query.filter(MediaVersion.media_type == MediaType(media_type))

    versions = query.order_by(
        MediaVersion.filename,
        MediaVersion.version.desc()
    ).all()

    # 按文件名分组
    grouped = {}
    for v in versions:
        if v.filename not in grouped:
            grouped[v.filename] = {
                "filename": v.filename,
                "media_type": v.media_type.value,
                "segment_index": v.segment_index,
                "versions": [],
                "active_version": None
            }
        grouped[v.filename]["versions"].append(v.to_dict())
        if v.is_active:
            grouped[v.filename]["active_version"] = v.version

    return {
        "project_id": project_id,
        "media": list(grouped.values())
    }


# ==================== 设置活跃版本 ====================

@router.post("/projects/{project_id}/images/{filename}/set-active")
async def set_active_image_version(
    project_id: int,
    filename: str,
    version: int,
    db: Session = Depends(get_db)
):
    """设置指定图片版本为活跃版本"""
    # 取消当前活跃版本
    db.query(MediaVersion).filter(
        MediaVersion.project_id == project_id,
        MediaVersion.media_type == MediaType.IMAGE,
        MediaVersion.filename == filename,
        MediaVersion.is_active == 1
    ).update({"is_active": 0})

    # 设置新的活跃版本
    target_version = db.query(MediaVersion).filter(
        MediaVersion.project_id == project_id,
        MediaVersion.media_type == MediaType.IMAGE,
        MediaVersion.filename == filename,
        MediaVersion.version == version
    ).first()

    if not target_version:
        raise HTTPException(status_code=404, detail=f"Version {version} not found")

    target_version.is_active = 1
    db.commit()

    return {
        "success": True,
        "message": f"Version {version} is now active",
        "version": target_version.to_dict()
    }


@router.post("/projects/{project_id}/audio/{filename}/set-active")
async def set_active_audio_version(
    project_id: int,
    filename: str,
    version: int,
    db: Session = Depends(get_db)
):
    """设置指定音频版本为活跃版本"""
    # 取消当前活跃版本
    db.query(MediaVersion).filter(
        MediaVersion.project_id == project_id,
        MediaVersion.media_type == MediaType.AUDIO,
        MediaVersion.filename == filename,
        MediaVersion.is_active == 1
    ).update({"is_active": 0})

    # 设置新的活跃版本
    target_version = db.query(MediaVersion).filter(
        MediaVersion.project_id == project_id,
        MediaVersion.media_type == MediaType.AUDIO,
        MediaVersion.filename == filename,
        MediaVersion.version == version
    ).first()

    if not target_version:
        raise HTTPException(status_code=404, detail=f"Version {version} not found")

    target_version.is_active = 1
    db.commit()

    return {
        "success": True,
        "message": f"Version {version} is now active",
        "version": target_version.to_dict()
    }


# ==================== 创建新版本 ====================

@router.post("/projects/{project_id}/images/{filename}/upload")
async def upload_new_image_version(
    project_id: int,
    filename: str,
    file: UploadFile = File(...),
    note: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """上传新的图片版本"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 获取下一个版本号
    max_version = db.query(MediaVersion).filter(
        MediaVersion.project_id == project_id,
        MediaVersion.media_type == MediaType.IMAGE,
        MediaVersion.filename == filename
    ).count()
    next_version = max_version + 1

    # 保存文件到本地
    local_dir = os.path.join(project.project_dir, "images", "versions")
    os.makedirs(local_dir, exist_ok=True)

    version_filename = f"{os.path.splitext(filename)[0]}_v{next_version}{os.path.splitext(filename)[1]}"
    local_path = os.path.join(local_dir, version_filename)

    with open(local_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 上传到云存储
    cloud_url = None
    if project.use_cloud_storage:
        try:
            cloud_path = f"projects/{project_id}/images/versions/{version_filename}"
            storage = get_storage_provider()
            cloud_url = storage.upload_file(local_path, cloud_path)
        except Exception as e:
            print(f"云存储上传失败: {str(e)}")

    # 获取文件信息
    file_size = os.path.getsize(local_path)
    try:
        from PIL import Image
        with Image.open(local_path) as img:
            width, height = img.size
    except:
        width, height = None, None

    # 创建版本记录
    new_version = MediaVersion(
        project_id=project_id,
        media_type=MediaType.IMAGE,
        filename=filename,
        version=next_version,
        is_active=1,  # 新上传的版本默认设为活跃
        local_path=local_path,
        cloud_url=cloud_url,
        generation_method=GenerationMethod.UPLOADED,
        generation_params={
            "original_filename": file.filename,
            "content_type": file.content_type
        },
        file_size_bytes=file_size,
        width=width,
        height=height,
        created_by="user",
        note=note
    )

    # 取消其他活跃版本
    db.query(MediaVersion).filter(
        MediaVersion.project_id == project_id,
        MediaVersion.media_type == MediaType.IMAGE,
        MediaVersion.filename == filename,
        MediaVersion.is_active == 1
    ).update({"is_active": 0})

    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    return {
        "success": True,
        "message": "Image version uploaded successfully",
        "version": new_version.to_dict()
    }


@router.post("/projects/{project_id}/audio/{filename}/upload")
async def upload_new_audio_version(
    project_id: int,
    filename: str,
    file: UploadFile = File(...),
    note: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """上传新的音频版本"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 获取下一个版本号
    max_version = db.query(MediaVersion).filter(
        MediaVersion.project_id == project_id,
        MediaVersion.media_type == MediaType.AUDIO,
        MediaVersion.filename == filename
    ).count()
    next_version = max_version + 1

    # 保存文件到本地
    local_dir = os.path.join(project.project_dir, "voice", "versions")
    os.makedirs(local_dir, exist_ok=True)

    version_filename = f"{os.path.splitext(filename)[0]}_v{next_version}{os.path.splitext(filename)[1]}"
    local_path = os.path.join(local_dir, version_filename)

    with open(local_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 上传到云存储
    cloud_url = None
    if project.use_cloud_storage:
        try:
            cloud_path = f"projects/{project_id}/voice/versions/{version_filename}"
            storage = get_storage_provider()
            cloud_url = storage.upload_file(local_path, cloud_path)
        except Exception as e:
            print(f"云存储上传失败: {str(e)}")

    # 获取文件信息
    file_size = os.path.getsize(local_path)

    # 尝试获取音频时长
    duration = None
    try:
        from moviepy.editor import AudioFileClip
        audio = AudioFileClip(local_path)
        duration = int(audio.duration)
        audio.close()
    except:
        pass

    # 创建版本记录
    new_version = MediaVersion(
        project_id=project_id,
        media_type=MediaType.AUDIO,
        filename=filename,
        version=next_version,
        is_active=1,  # 新上传的版本默认设为活跃
        local_path=local_path,
        cloud_url=cloud_url,
        generation_method=GenerationMethod.UPLOADED,
        generation_params={
            "original_filename": file.filename,
            "content_type": file.content_type
        },
        file_size_bytes=file_size,
        duration_seconds=duration,
        created_by="user",
        note=note
    )

    # 取消其他活跃版本
    db.query(MediaVersion).filter(
        MediaVersion.project_id == project_id,
        MediaVersion.media_type == MediaType.AUDIO,
        MediaVersion.filename == filename,
        MediaVersion.is_active == 1
    ).update({"is_active": 0})

    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    return {
        "success": True,
        "message": "Audio version uploaded successfully",
        "version": new_version.to_dict()
    }


# ==================== 删除版本 ====================

@router.delete("/versions/{version_id}")
async def delete_media_version(
    version_id: int,
    db: Session = Depends(get_db)
):
    """删除指定版本（不能删除活跃版本）"""
    version = db.query(MediaVersion).filter(MediaVersion.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    if version.is_active:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete active version. Please set another version as active first."
        )

    # 删除本地文件
    if version.local_path and os.path.exists(version.local_path):
        try:
            os.remove(version.local_path)
        except Exception as e:
            print(f"删除本地文件失败: {str(e)}")

    # 删除云存储文件（可选）
    if version.cloud_url:
        try:
            storage = get_storage_provider()
            # 从URL提取cloud_path
            # 这里需要根据实际URL格式解析
            # storage.delete_file(cloud_path)
        except Exception as e:
            print(f"删除云存储文件失败: {str(e)}")

    db.delete(version)
    db.commit()

    return {
        "success": True,
        "message": "Version deleted successfully"
    }


# ==================== 获取活跃版本预览 ====================

@router.get("/projects/{project_id}/active-media")
async def get_active_media(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取所有活跃版本的媒体资源（用于视频合成预览）"""
    active_versions = db.query(MediaVersion).filter(
        MediaVersion.project_id == project_id,
        MediaVersion.is_active == 1
    ).order_by(
        MediaVersion.media_type,
        MediaVersion.filename
    ).all()

    images = {}
    audio = {}

    for v in active_versions:
        url = v.cloud_url or v.local_path
        if v.media_type == MediaType.IMAGE:
            images[v.filename] = {
                "url": url,
                "version": v.version,
                "width": v.width,
                "height": v.height
            }
        elif v.media_type == MediaType.AUDIO:
            audio[v.filename] = {
                "url": url,
                "version": v.version,
                "duration": v.duration_seconds
            }

    return {
        "project_id": project_id,
        "images": images,
        "audio": audio
    }
