"""Backward-compatible application facade.

This package preserves historical import paths (``core.application``) while
internally delegating to the current ``core.pipeline`` implementation.
"""

import importlib

from core.pipeline import PipelineService, StepRunner
from core.pipeline.steps import (
    run_step_1,
    run_step_1_5,
    run_step_2,
    run_step_3,
    run_step_4,
    run_step_5,
    run_step_6,
)


class _CallableModuleProxy:
    """Expose a module as a callable object while forwarding attribute edits."""

    def __init__(self, module, callable_name: str):
        object.__setattr__(self, "_module", module)
        object.__setattr__(self, "_callable_name", callable_name)

    def __call__(self, *args, **kwargs):
        func = getattr(self._module, self._callable_name)
        return func(*args, **kwargs)

    def __getattr__(self, item):
        return getattr(self._module, item)

    def __setattr__(self, key, value):
        setattr(self._module, key, value)


_run_auto_module = importlib.import_module("core.application.run_auto")
run_auto = _CallableModuleProxy(_run_auto_module, "run_auto")

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
