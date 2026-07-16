"""Lazy public exports for the domain layer."""

from core._lazy import lazy_dir, lazy_getattr

_EXPORT_NAMES = (
    "generate_description_summary",
    "process_raw_to_script",
    "export_plain_text_segments",
)
_EXPORTS = {name: ("core.domain.summarizer", name) for name in _EXPORT_NAMES}
__all__ = list(_EXPORTS)

__getattr__ = lazy_getattr(__name__, globals(), _EXPORTS)
__dir__ = lazy_dir(globals(), __all__)
