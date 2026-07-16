"""Gateway that exposes media infrastructure without direct domain imports."""

from core.infra.media.ffmpeg import (
    adjust_audio_speed,
    normalize_loudness as normalize_bgm_loudness,
)
from core.infra.media.exporter import export_video

__all__ = [
    "adjust_audio_speed",
    "export_video",
    "normalize_bgm_loudness",
]
