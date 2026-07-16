"""Lazy public exports for the CLI adapter."""

from core._lazy import lazy_dir, lazy_getattr

_EXPORTS = {
    "main": ("core.cli.main", "main"),
    "run_cli_main": ("core.cli.ui_helpers", "run_cli_main"),
    "setup_cli_logging": ("core.cli.ui_helpers", "setup_cli_logging"),
}

__all__ = list(_EXPORTS)

__getattr__ = lazy_getattr(__name__, globals(), _EXPORTS)
__dir__ = lazy_dir(globals(), __all__)
