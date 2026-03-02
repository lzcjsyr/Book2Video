"""Compatibility alias for historical ``core.application.service`` module."""

import sys

import core.pipeline.service as _service_module

sys.modules[__name__] = _service_module

