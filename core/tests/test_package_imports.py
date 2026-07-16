import subprocess
import sys


def test_core_package_is_lazy_and_public_exports_still_resolve():
    code = """
import sys
import core
assert 'core.pipeline.steps' not in sys.modules
import core.cli
import core.infra.ai
import core.infra.hyperframes
assert 'core.cli.ui_helpers' not in sys.modules
assert 'core.infra.ai.image_client' not in sys.modules
assert 'core.infra.hyperframes.opening_renderer' not in sys.modules
from core.cli import main
from core.infra.ai import text_to_text
from core.infra.hyperframes import render_opening_video
assert callable(main)
assert callable(text_to_text)
assert callable(render_opening_video)
from core import ProjectPaths, VideoGenerationConfig, run_auto, run_step_1
assert ProjectPaths.__name__ == 'ProjectPaths'
assert VideoGenerationConfig.__name__ == 'VideoGenerationConfig'
assert callable(run_auto)
assert callable(run_step_1)
"""
    subprocess.run([sys.executable, "-c", code], check=True)
