"""Compatibility alias for historical ``core.application.steps`` module."""

import sys

import core.pipeline.steps as _steps_module

sys.modules[__name__] = _steps_module

