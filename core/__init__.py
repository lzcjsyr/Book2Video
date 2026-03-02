"""Core package marker."""

# 导出新的工具类供外部使用
from core.infra.project_paths import ProjectPaths
from core.generation_config import VideoGenerationConfig, StepExecutionConfig
from core.pipeline import PipelineService, StepRunner

__all__ = [
    'ProjectPaths',
    'VideoGenerationConfig',
    'StepExecutionConfig',
    'PipelineService',
    'StepRunner',
]
