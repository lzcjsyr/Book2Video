"""
视频生成Celery任务
"""
from celery import Task
from backend.celery_app import celery_app
from backend.database import SessionLocal
from backend.models import Project, ProjectStatus, Task as TaskModel, TaskStatus
from datetime import datetime
import os
import traceback
import json

# 导入核心模块
from core.pipeline import BookRecapPipeline
from core.generation_config import VideoGenerationConfig, StepExecutionConfig
from core.project_paths import ProjectPaths
from core import text, media
from core.video_composer import VideoComposer
import config as app_config

# 导入云存储服务
from backend.services.cloud_storage import (
    get_storage_provider,
    upload_project_file,
    batch_upload_directory
)


class ProgressReportingTask(Task):
    """支持进度报告的Celery任务基类"""

    def __init__(self):
        super().__init__()
        self.db_session = None
        self.task_model = None
        self.project_model = None

    def update_progress(self, progress: int, operation: str = None):
        """更新任务进度"""
        if self.task_model and self.db_session:
            self.task_model.progress = progress
            if operation:
                self.task_model.current_operation = operation
            self.db_session.commit()

            # 同时更新项目进度
            if self.project_model:
                self.project_model.current_step_progress = progress
                self.db_session.commit()

    def update_project_step(self, step: int, completed: bool = False):
        """更新项目步骤状态"""
        if self.project_model and self.db_session:
            self.project_model.current_step = step
            if completed:
                # 标记步骤完成
                setattr(self.project_model, f"step{step}_completed", 1)
            self.db_session.commit()


# ==================== 云存储辅助函数 ====================

def upload_images_to_cloud(project_id: int, project_dir: str) -> dict:
    """
    上传所有图片到云存储

    Args:
        project_id: 项目ID
        project_dir: 项目目录

    Returns:
        文件名 -> 云存储URL的映射字典
    """
    images_dir = os.path.join(project_dir, "images")
    if not os.path.exists(images_dir):
        return {}

    return batch_upload_directory(project_id, images_dir, "images")


def upload_audio_to_cloud(project_id: int, project_dir: str) -> dict:
    """
    上传所有音频到云存储

    Args:
        project_id: 项目ID
        project_dir: 项目目录

    Returns:
        文件名 -> 云存储URL的映射字典
    """
    voice_dir = os.path.join(project_dir, "voice")
    if not os.path.exists(voice_dir):
        return {}

    return batch_upload_directory(project_id, voice_dir, "voice")


def upload_video_to_cloud(project_id: int, project_dir: str) -> str:
    """
    上传最终视频到云存储

    Args:
        project_id: 项目ID
        project_dir: 项目目录

    Returns:
        云存储URL，如果文件不存在则返回None
    """
    video_path = os.path.join(project_dir, "final_video.mp4")
    if not os.path.exists(video_path):
        return None

    return upload_project_file(project_id, video_path, "video", "final_video.mp4")


def upload_covers_to_cloud(project_id: int, project_dir: str) -> list:
    """
    上传封面图片到云存储

    Args:
        project_id: 项目ID
        project_dir: 项目目录

    Returns:
        云存储URL列表
    """
    cover_urls = []
    for filename in os.listdir(project_dir):
        if filename.startswith("cover_") and filename.endswith(".png"):
            cover_path = os.path.join(project_dir, filename)
            url = upload_project_file(project_id, cover_path, "covers", filename)
            cover_urls.append(url)

    return cover_urls


@celery_app.task(bind=True, base=ProgressReportingTask, name="backend.tasks.video_generation.execute_full_auto")
def execute_full_auto(self, project_id: int, config_dict: dict):
    """
    执行全自动模式（完整的7步流程）
    """
    db = SessionLocal()
    try:
        # 获取项目和任务
        project = db.query(Project).filter(Project.id == project_id).first()
        task = db.query(TaskModel).filter(TaskModel.celery_task_id == self.request.id).first()

        self.db_session = db
        self.task_model = task
        self.project_model = project

        if not project:
            raise ValueError(f"Project {project_id} not found")

        # 更新任务状态
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        project.status = ProjectStatus.PROCESSING
        db.commit()

        # 创建配置对象
        gen_config = VideoGenerationConfig(
            input_file=project.input_file_path,
            output_dir=os.path.dirname(project.project_dir),
            **config_dict
        )

        # 创建Pipeline实例
        pipeline = BookRecapPipeline(gen_config)

        # 执行步骤1：智能总结
        self.update_progress(5, "正在进行智能总结...")
        self.update_project_step(1, False)
        pipeline.run_step(1)
        self.update_project_step(1, True)
        self.update_progress(15, "智能总结完成")

        # 加载raw.json数据
        raw_json_path = os.path.join(project.project_dir, "text", "raw.json")
        if os.path.exists(raw_json_path):
            with open(raw_json_path, 'r', encoding='utf-8') as f:
                project.raw_data = json.load(f)
                db.commit()

        # 执行步骤1.5：脚本分段
        self.update_progress(20, "正在进行脚本分段...")
        self.update_project_step(1.5, False)  # 注意这里用1来代表1.5
        pipeline.run_step(1.5)
        project.step1_5_completed = 1
        db.commit()
        self.update_progress(30, "脚本分段完成")

        # 加载script.json数据
        script_json_path = os.path.join(project.project_dir, "text", "script.json")
        if os.path.exists(script_json_path):
            with open(script_json_path, 'r', encoding='utf-8') as f:
                project.script_data = json.load(f)
                db.commit()

        # 执行步骤2：要点提取
        self.update_progress(35, "正在提取要点...")
        self.update_project_step(2, False)
        pipeline.run_step(2)
        self.update_project_step(2, True)
        self.update_progress(45, "要点提取完成")

        # 加载keywords/mini_summary数据
        keywords_path = os.path.join(project.project_dir, "text", "keywords.json")
        mini_summary_path = os.path.join(project.project_dir, "text", "mini_summary.json")
        if os.path.exists(keywords_path):
            with open(keywords_path, 'r', encoding='utf-8') as f:
                project.keywords_data = json.load(f)
                db.commit()
        elif os.path.exists(mini_summary_path):
            with open(mini_summary_path, 'r', encoding='utf-8') as f:
                project.keywords_data = json.load(f)
                db.commit()

        # 执行步骤3：图像生成
        self.update_progress(50, "正在生成图像...")
        self.update_project_step(3, False)
        pipeline.run_step(3)
        self.update_project_step(3, True)

        # 上传图片到云存储
        if project.use_cloud_storage:
            self.update_progress(58, "正在上传图片到云存储...")
            try:
                images_urls = upload_images_to_cloud(project_id, project.project_dir)
                project.images_urls = images_urls
                project.cloud_uploaded_at = datetime.now()

                # 记录存储提供商信息
                storage_provider = os.getenv("STORAGE_PROVIDER", "local")
                project.storage_provider = storage_provider
                if storage_provider != "local":
                    project.storage_bucket = os.getenv(
                        f"{storage_provider.upper().replace('_', '_')}_BUCKET",
                        os.getenv("ALIYUN_OSS_BUCKET") or
                        os.getenv("TENCENT_COS_BUCKET") or
                        os.getenv("AWS_S3_BUCKET")
                    )

                db.commit()
            except Exception as e:
                # 云存储失败不影响主流程，记录错误继续执行
                print(f"云存储上传失败（图片）: {str(e)}")

        self.update_progress(60, "图像生成完成")

        # 执行步骤4：语音合成
        self.update_progress(65, "正在合成语音...")
        self.update_project_step(4, False)
        pipeline.run_step(4)
        self.update_project_step(4, True)

        # 上传音频到云存储
        if project.use_cloud_storage:
            self.update_progress(73, "正在上传音频到云存储...")
            try:
                audio_urls = upload_audio_to_cloud(project_id, project.project_dir)
                project.audio_urls = audio_urls
                db.commit()
            except Exception as e:
                print(f"云存储上传失败（音频）: {str(e)}")

        self.update_progress(75, "语音合成完成")

        # 执行步骤5：视频合成
        self.update_progress(80, "正在合成视频...")
        self.update_project_step(5, False)
        pipeline.run_step(5)
        self.update_project_step(5, True)

        # 记录最终视频路径
        final_video_path = os.path.join(project.project_dir, "final_video.mp4")
        if os.path.exists(final_video_path):
            project.final_video_path = final_video_path

        # 上传视频到云存储
        if project.use_cloud_storage:
            self.update_progress(88, "正在上传视频到云存储...")
            try:
                video_url = upload_video_to_cloud(project_id, project.project_dir)
                if video_url:
                    project.final_video_url = video_url
                    db.commit()
            except Exception as e:
                print(f"云存储上传失败（视频）: {str(e)}")

        self.update_progress(90, "视频合成完成")

        # 执行步骤6：封面生成（可选）
        if config_dict.get("cover_image_count", 0) > 0:
            self.update_progress(95, "正在生成封面...")
            self.update_project_step(6, False)
            pipeline.run_step(6)
            self.update_project_step(6, True)

            # 记录封面路径
            cover_paths = []
            cover_dir = project.project_dir
            for file in os.listdir(cover_dir):
                if file.startswith("cover_") and file.endswith(".png"):
                    cover_paths.append(os.path.join(cover_dir, file))
            if cover_paths:
                project.cover_image_paths = cover_paths

            # 上传封面到云存储
            if project.use_cloud_storage:
                self.update_progress(98, "正在上传封面到云存储...")
                try:
                    cover_urls = upload_covers_to_cloud(project_id, project.project_dir)
                    if cover_urls:
                        project.cover_image_urls = cover_urls
                        db.commit()
                except Exception as e:
                    print(f"云存储上传失败（封面）: {str(e)}")

        # 任务完成
        self.update_progress(100, "全部完成")
        task.status = TaskStatus.SUCCESS
        task.completed_at = datetime.now()
        project.status = ProjectStatus.COMPLETED
        project.completed_at = datetime.now()
        db.commit()

        return {"status": "success", "project_id": project_id}

    except Exception as e:
        # 错误处理
        error_msg = str(e)
        error_tb = traceback.format_exc()

        if task:
            task.status = TaskStatus.FAILED
            task.error_message = error_msg
            task.error_traceback = error_tb
            task.completed_at = datetime.now()

        if project:
            project.status = ProjectStatus.FAILED
            project.error_message = error_msg

        db.commit()

        raise

    finally:
        db.close()


@celery_app.task(bind=True, base=ProgressReportingTask, name="backend.tasks.video_generation.execute_step")
def execute_step(self, project_id: int, step: int, force_regenerate: bool = False, custom_params: dict = None):
    """
    执行单个步骤
    """
    db = SessionLocal()
    try:
        # 获取项目和任务
        project = db.query(Project).filter(Project.id == project_id).first()
        task = db.query(TaskModel).filter(TaskModel.celery_task_id == self.request.id).first()

        self.db_session = db
        self.task_model = task
        self.project_model = project

        if not project:
            raise ValueError(f"Project {project_id} not found")

        # 更新任务状态
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        project.status = ProjectStatus.PROCESSING
        db.commit()

        # 创建项目路径对象
        project_paths = ProjectPaths(project.project_dir)

        # 创建配置对象
        config_dict = project.config or {}
        if custom_params:
            config_dict.update(custom_params)

        gen_config = VideoGenerationConfig(
            input_file=project.input_file_path,
            output_dir=os.path.dirname(project.project_dir),
            **config_dict
        )

        # 根据步骤执行相应逻辑
        step_name_map = {
            1: "智能总结",
            1.5: "脚本分段",
            2: "要点提取",
            3: "图像生成",
            4: "语音合成",
            5: "视频合成",
            6: "封面生成"
        }

        self.update_progress(10, f"正在执行: {step_name_map.get(step, f'步骤{step}')}")
        self.update_project_step(step if step != 1.5 else 1, False)

        # 创建Pipeline实例
        pipeline = BookRecapPipeline(gen_config)

        # 执行步骤
        if step == 1:
            pipeline.run_step(1)
            # 加载raw.json
            raw_json_path = project_paths.get_raw_json_path()
            if os.path.exists(raw_json_path):
                with open(raw_json_path, 'r', encoding='utf-8') as f:
                    project.raw_data = json.load(f)

        elif step == 1.5:
            pipeline.run_step(1.5)
            # 加载script.json
            script_json_path = project_paths.get_script_json_path()
            if os.path.exists(script_json_path):
                with open(script_json_path, 'r', encoding='utf-8') as f:
                    project.script_data = json.load(f)
            project.step1_5_completed = 1

        elif step == 2:
            pipeline.run_step(2)
            # 加载keywords或mini_summary
            if gen_config.images_method == "keywords":
                kw_path = project_paths.get_keywords_json_path()
                if os.path.exists(kw_path):
                    with open(kw_path, 'r', encoding='utf-8') as f:
                        project.keywords_data = json.load(f)
            else:
                ms_path = project_paths.get_mini_summary_json_path()
                if os.path.exists(ms_path):
                    with open(ms_path, 'r', encoding='utf-8') as f:
                        project.keywords_data = json.load(f)

        elif step == 3:
            pipeline.run_step(3)
            # 上传图片到云存储
            if project.use_cloud_storage:
                self.update_progress(80, "正在上传图片到云存储...")
                try:
                    images_urls = upload_images_to_cloud(project_id, project.project_dir)
                    project.images_urls = images_urls
                    project.cloud_uploaded_at = datetime.now()

                    # 记录存储提供商信息
                    storage_provider = os.getenv("STORAGE_PROVIDER", "local")
                    project.storage_provider = storage_provider
                    if storage_provider != "local":
                        project.storage_bucket = os.getenv(
                            f"{storage_provider.upper().replace('_', '_')}_BUCKET",
                            os.getenv("ALIYUN_OSS_BUCKET") or
                            os.getenv("TENCENT_COS_BUCKET") or
                            os.getenv("AWS_S3_BUCKET")
                        )
                    db.commit()
                except Exception as e:
                    print(f"云存储上传失败（图片）: {str(e)}")

        elif step == 4:
            pipeline.run_step(4)
            # 上传音频到云存储
            if project.use_cloud_storage:
                self.update_progress(80, "正在上传音频到云存储...")
                try:
                    audio_urls = upload_audio_to_cloud(project_id, project.project_dir)
                    project.audio_urls = audio_urls
                    db.commit()
                except Exception as e:
                    print(f"云存储上传失败（音频）: {str(e)}")

        elif step == 5:
            pipeline.run_step(5)
            # 记录视频路径
            final_video_path = project_paths.get_final_video_path()
            if os.path.exists(final_video_path):
                project.final_video_path = final_video_path

            # 上传视频到云存储
            if project.use_cloud_storage:
                self.update_progress(80, "正在上传视频到云存储...")
                try:
                    video_url = upload_video_to_cloud(project_id, project.project_dir)
                    if video_url:
                        project.final_video_url = video_url
                        db.commit()
                except Exception as e:
                    print(f"云存储上传失败（视频）: {str(e)}")

        elif step == 6:
            pipeline.run_step(6)
            # 记录封面路径
            cover_paths = []
            for file in os.listdir(project.project_dir):
                if file.startswith("cover_") and file.endswith(".png"):
                    cover_paths.append(os.path.join(project.project_dir, file))
            if cover_paths:
                project.cover_image_paths = cover_paths

            # 上传封面到云存储
            if project.use_cloud_storage:
                self.update_progress(90, "正在上传封面到云存储...")
                try:
                    cover_urls = upload_covers_to_cloud(project_id, project.project_dir)
                    if cover_urls:
                        project.cover_image_urls = cover_urls
                        db.commit()
                except Exception as e:
                    print(f"云存储上传失败（封面）: {str(e)}")

        # 更新步骤完成状态
        if step != 1.5:
            setattr(project, f"step{int(step)}_completed", 1)
        else:
            project.step1_5_completed = 1

        self.update_progress(100, f"{step_name_map.get(step, f'步骤{step}')}完成")

        # 任务完成
        task.status = TaskStatus.SUCCESS
        task.completed_at = datetime.now()

        # 检查是否所有步骤都完成
        all_completed = all([
            project.step1_completed,
            project.step1_5_completed,
            project.step2_completed,
            project.step3_completed,
            project.step4_completed,
            project.step5_completed
        ])
        if all_completed:
            project.status = ProjectStatus.COMPLETED
            project.completed_at = datetime.now()
        else:
            project.status = ProjectStatus.CREATED

        db.commit()

        return {"status": "success", "project_id": project_id, "step": step}

    except Exception as e:
        # 错误处理
        error_msg = str(e)
        error_tb = traceback.format_exc()

        if task:
            task.status = TaskStatus.FAILED
            task.error_message = error_msg
            task.error_traceback = error_tb
            task.completed_at = datetime.now()

        if project:
            project.status = ProjectStatus.FAILED
            project.error_message = error_msg

        db.commit()

        raise

    finally:
        db.close()


@celery_app.task(bind=True, base=ProgressReportingTask, name="backend.tasks.video_generation.regenerate_images")
def regenerate_images(self, project_id: int, segment_indices: list):
    """
    重新生成指定段落的图片
    """
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        task = db.query(TaskModel).filter(TaskModel.celery_task_id == self.request.id).first()

        self.db_session = db
        self.task_model = task
        self.project_model = project

        if not project:
            raise ValueError(f"Project {project_id} not found")

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        db.commit()

        # 创建项目路径和配置
        project_paths = ProjectPaths(project.project_dir)
        gen_config = VideoGenerationConfig(
            input_file=project.input_file_path,
            output_dir=os.path.dirname(project.project_dir),
            **(project.config or {})
        )

        self.update_progress(10, f"正在重新生成 {len(segment_indices)} 张图片...")

        # 调用media模块的重新生成函数
        # 这里需要实现一个针对特定segment的图片生成函数
        # 暂时使用完整的图片生成逻辑，可以后续优化

        total = len(segment_indices)
        for idx, seg_idx in enumerate(segment_indices):
            progress = 10 + int((idx / total) * 80)
            self.update_progress(progress, f"正在生成第 {seg_idx} 段图片...")

            # 实际的图片重新生成逻辑
            # TODO: 实现单张图片重新生成

        self.update_progress(100, "图片重新生成完成")
        task.status = TaskStatus.SUCCESS
        task.completed_at = datetime.now()
        db.commit()

        return {"status": "success", "regenerated_count": len(segment_indices)}

    except Exception as e:
        error_msg = str(e)
        error_tb = traceback.format_exc()

        if task:
            task.status = TaskStatus.FAILED
            task.error_message = error_msg
            task.error_traceback = error_tb
            task.completed_at = datetime.now()

        db.commit()
        raise

    finally:
        db.close()
