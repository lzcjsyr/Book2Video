"""应用层统一导出模块。

本文件负责聚合并导出 application 层的公共能力，供 CLI、API 与其他模块稳定引用：
1. 导出 PipelineService/StepRunner，提供按步骤执行与作业编排入口。
2. 导出 run_auto，提供全流程自动化执行入口。
3. 导出 run_step_1~run_step_6，提供分步执行能力，避免上层直接依赖具体实现文件。

通过集中导出，调用方可使用 `core.pipeline` 作为稳定边界，降低目录重构时的改动面。
"""

from core.pipeline.run_auto import run_auto
from core.pipeline.service import PipelineService, StepRunner
from core.pipeline.steps import (
    run_step_1,
    run_step_1_5,
    run_step_2,
    run_step_3,
    run_step_4,
    run_step_5,
    run_step_6,
)

__all__ = [
    "PipelineService",
    "StepRunner",
    "run_auto",
    "run_step_1",
    "run_step_1_5",
    "run_step_2",
    "run_step_3",
    "run_step_4",
    "run_step_5",
    "run_step_6",
]
