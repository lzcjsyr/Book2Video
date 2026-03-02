"""Compatibility alias for historical ``core.application.scanner`` module."""

import sys

import core.pipeline.scanner as _scanner_module

sys.modules[__name__] = _scanner_module

