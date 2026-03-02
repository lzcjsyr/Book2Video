"""Compatibility alias for historical ``core.application.run_auto`` module."""

import importlib
import sys

_run_auto_module = importlib.import_module("core.pipeline.run_auto")

sys.modules[__name__] = _run_auto_module
