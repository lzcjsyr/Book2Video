"""Public core API with lazy imports to keep package loading side-effect free."""

from core._lazy import lazy_dir, lazy_getattr

_EXPORTS = {
    "ProjectPaths": ("core.infra.project_paths", "ProjectPaths"),
    "VideoGenerationConfig": ("core.config", "VideoGenerationConfig"),
    "run_auto": ("core.pipeline", "run_auto"),
    **{
        f"run_step_{step}": ("core.pipeline", f"run_step_{step}")
        for step in (1, "1_5", 2, 3, 4, 5, 6)
    },
}

__all__ = list(_EXPORTS)

__getattr__ = lazy_getattr(__name__, globals(), _EXPORTS)
__dir__ = lazy_dir(globals(), __all__)
