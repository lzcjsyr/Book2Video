"""Compatibility alias for historical media import path."""

import importlib
import sys

_image_module = importlib.import_module("core.infra.ai.image_client")
sys.modules[__name__] = _image_module

