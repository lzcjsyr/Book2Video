"""流水线服务层模块。

本文件提供面向上层（API/任务系统）的服务封装，职责分为两部分：
1. StepRunner：对 run_step_1~run_step_6 做统一门面封装，屏蔽底层函数细节。
2. PipelineService：提供自动执行、按步骤执行、异步任务提交与状态查询等服务能力。

此外，本模块还负责作业状态变更与事件记录（依赖 JobStoreSQLite），
用于支撑后续的异步 worker、任务监控与故障定位。
"""

import datetime
import json
from typing import Any, Callable, Dict, List, Optional

from core.contracts import JobStatus
from core.infra.sqlite_store import JobStoreSQLite

from . import run_auto as _run_auto_module
from .steps import (
    run_step_1 as _run_step_1,
    run_step_1_5 as _run_step_1_5,
    run_step_2 as _run_step_2,
    run_step_3 as _run_step_3,
    run_step_4 as _run_step_4,
    run_step_5 as _run_step_5,
    run_step_6 as _run_step_6,
)


class StepRunner:
    """Facade for step-wise execution."""

    def run_step_1(
        self,
        input_file: str,
        output_dir: str,
        llm_server: str,
        llm_model: str,
        target_length: int,
        num_segments: int,
    ) -> Dict[str, Any]:
        return _run_step_1(
            input_file=input_file,
            output_dir=output_dir,
            llm_server=llm_server,
            llm_model=llm_model,
            target_length=target_length,
            num_segments=num_segments,
        )

    def run_step_1_5(
        self,
        project_output_dir: str,
        num_segments: int,
        is_new_project: bool = False,
        raw_data: Optional[Dict[str, Any]] = None,
        auto_mode: bool = False,
        split_mode: str = "auto",
    ) -> Dict[str, Any]:
        return _run_step_1_5(
            project_output_dir=project_output_dir,
            num_segments=num_segments,
            is_new_project=is_new_project,
            raw_data=raw_data,
            auto_mode=auto_mode,
            split_mode=split_mode,
        )

    def run_step_2(
        self,
        llm_server: str,
        llm_model: str,
        project_output_dir: str,
        script_path: Optional[str] = None,
        images_method: str = "keywords",
    ) -> Dict[str, Any]:
        return _run_step_2(
            llm_server=llm_server,
            llm_model=llm_model,
            project_output_dir=project_output_dir,
            script_path=script_path,
            images_method=images_method,
        )

    def run_step_3(
        self,
        image_server: str,
        image_model: str,
        image_size: str,
        image_style_preset: str,
        project_output_dir: str,
        opening_image_style: str,
        images_method: str = "keywords",
        opening_quote: bool = True,
        target_segments: Optional[List[int]] = None,
        regenerate_opening: bool = True,
        llm_model: Optional[str] = None,
        llm_server: Optional[str] = None,
    ) -> Dict[str, Any]:
        return _run_step_3(
            image_server=image_server,
            image_model=image_model,
            image_size=image_size,
            image_style_preset=image_style_preset,
            project_output_dir=project_output_dir,
            opening_image_style=opening_image_style,
            images_method=images_method,
            opening_quote=opening_quote,
            target_segments=target_segments,
            regenerate_opening=regenerate_opening,
            llm_model=llm_model,
            llm_server=llm_server,
        )

    def run_step_4(
        self,
        tts_server: str,
        voice: str,
        project_output_dir: str,
        opening_quote: bool = True,
        target_segments: Optional[List[int]] = None,
        regenerate_opening: bool = True,
        speech_rate: int = 0,
        loudness_rate: int = 0,
        emotion: str = "neutral",
        emotion_scale: int = 4,
        mute_cut_threshold: int = 400,
        mute_cut_min_silence_ms: int = 200,
        mute_cut_remain_ms: int = 100,
    ) -> Dict[str, Any]:
        return _run_step_4(
            tts_server=tts_server,
            voice=voice,
            project_output_dir=project_output_dir,
            opening_quote=opening_quote,
            target_segments=target_segments,
            regenerate_opening=regenerate_opening,
            speech_rate=speech_rate,
            loudness_rate=loudness_rate,
            emotion=emotion,
            emotion_scale=emotion_scale,
            mute_cut_threshold=mute_cut_threshold,
            mute_cut_min_silence_ms=mute_cut_min_silence_ms,
            mute_cut_remain_ms=mute_cut_remain_ms,
        )

    def run_step_5(
        self,
        project_output_dir: str,
        image_size: str,
        enable_subtitles: bool,
        bgm_filename: str,
        voice: str,
        opening_quote: bool = True,
        speech_rate: int = 0,
        loudness_rate: int = 0,
        emotion: str = "neutral",
        emotion_scale: int = 4,
        mute_cut_threshold: int = 400,
        mute_cut_min_silence_ms: int = 200,
        mute_cut_remain_ms: int = 100,
    ) -> Dict[str, Any]:
        return _run_step_5(
            project_output_dir=project_output_dir,
            image_size=image_size,
            enable_subtitles=enable_subtitles,
            bgm_filename=bgm_filename,
            voice=voice,
            opening_quote=opening_quote,
            speech_rate=speech_rate,
            loudness_rate=loudness_rate,
            emotion=emotion,
            emotion_scale=emotion_scale,
            mute_cut_threshold=mute_cut_threshold,
            mute_cut_min_silence_ms=mute_cut_min_silence_ms,
            mute_cut_remain_ms=mute_cut_remain_ms,
        )

    def run_step_6(
        self,
        project_output_dir: str,
        cover_image_size: str,
        cover_image_server: str,
        cover_image_model: str,
        cover_image_style: str,
        cover_image_count: int,
    ) -> Dict[str, Any]:
        return _run_step_6(
            project_output_dir=project_output_dir,
            cover_image_size=cover_image_size,
            cover_image_server=cover_image_server,
            cover_image_model=cover_image_model,
            cover_image_style=cover_image_style,
            cover_image_count=cover_image_count,
        )


class PipelineService:
    """Coordinate full pipeline execution and async job tracking."""

    def __init__(self, job_store: Optional[JobStoreSQLite] = None):
        self.step_runner = StepRunner()
        self.job_store = job_store

    def run_auto(
        self,
        config,
        *,
        step_1_5_override: Optional[Callable[..., Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        if step_1_5_override is None:
            return _run_auto_module.run_auto(config)

        original = _run_auto_module._run_step_1_5
        _run_auto_module._run_step_1_5 = step_1_5_override
        try:
            return _run_auto_module.run_auto(config)
        finally:
            _run_auto_module._run_step_1_5 = original

    def run_step(self, step: float, **kwargs) -> Dict[str, Any]:
        handlers = {
            1: self.step_runner.run_step_1,
            1.5: self.step_runner.run_step_1_5,
            2: self.step_runner.run_step_2,
            3: self.step_runner.run_step_3,
            4: self.step_runner.run_step_4,
            5: self.step_runner.run_step_5,
            6: self.step_runner.run_step_6,
        }
        handler = handlers.get(step)
        if handler is None:
            return {"success": False, "message": f"不支持的步骤: {step}"}
        return handler(**kwargs)

    def submit_job(self, job_type: str, payload: Dict[str, Any]) -> Optional[str]:
        """Store a pending job for future async worker consumption."""
        if self.job_store is None:
            return None
        record = self.job_store.submit_job(job_type=job_type, payload=payload)
        return record.job_id

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        if self.job_store is None:
            return None
        record = self.job_store.get_job(job_id)
        if record is None:
            return None
        return {
            "job_id": record.job_id,
            "job_type": record.job_type,
            "status": record.status.value,
            "current_step": record.current_step,
            "progress": record.progress,
            "error": json.loads(record.error_json) if record.error_json else None,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
            "started_at": record.started_at,
            "finished_at": record.finished_at,
            "events": self.job_store.list_events(job_id),
        }

    def mark_job_running(self, job_id: str, current_step: Optional[str] = None, progress: float = 0.0) -> None:
        if self.job_store is None:
            return
        self.job_store.update_job_status(job_id, JobStatus.RUNNING, current_step=current_step, progress=progress)
        self.job_store.append_event(job_id, "INFO", "job started", {"step": current_step, "progress": progress})

    def mark_job_succeeded(self, job_id: str) -> None:
        if self.job_store is None:
            return
        self.job_store.update_job_status(job_id, JobStatus.SUCCEEDED, progress=1.0)
        self.job_store.append_event(job_id, "INFO", "job succeeded", {"finished_at": datetime.datetime.now().isoformat()})

    def mark_job_failed(self, job_id: str, error: Dict[str, Any]) -> None:
        if self.job_store is None:
            return
        self.job_store.update_job_status(job_id, JobStatus.FAILED, error=error)
        self.job_store.append_event(job_id, "ERROR", "job failed", error)


__all__ = ["PipelineService", "StepRunner"]
