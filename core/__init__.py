"""
Core package marker. Public API should be imported from submodules
like core.text, core.media, core.pipeline, etc.
"""

# 导出新的工具类供外部使用
from core.project_paths import ProjectPaths
from core.generation_config import VideoGenerationConfig, StepExecutionConfig

__all__ = [
    'ProjectPaths',
    'VideoGenerationConfig',
    'StepExecutionConfig',
]
