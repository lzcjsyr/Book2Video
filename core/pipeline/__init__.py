"""Lazy orchestration exports for CLI and scripts."""

from core._lazy import lazy_dir, lazy_getattr

_EXPORT_NAMES = (
    "run_step_1",
    "run_step_1_5",
    "run_step_2",
    "run_step_3",
    "run_step_4",
    "run_step_5",
    "run_step_6",
)
_EXPORTS = {
    "run_auto": ("core.pipeline.run_auto", "run_auto"),
    **{name: ("core.pipeline.steps", name) for name in _EXPORT_NAMES},
}
__all__ = list(_EXPORTS)

__getattr__ = lazy_getattr(__name__, globals(), _EXPORTS)
__dir__ = lazy_dir(globals(), __all__)
