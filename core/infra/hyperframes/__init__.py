"""Lazy public exports for HyperFrames rendering."""

from core._lazy import lazy_dir, lazy_getattr

_EXPORTS = {
    "render_opening_video": (
        "core.infra.hyperframes.opening_renderer",
        "render_opening_video",
    )
}
__all__ = list(_EXPORTS)

__getattr__ = lazy_getattr(__name__, globals(), _EXPORTS)
__dir__ = lazy_dir(globals(), __all__)
