from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from core.config import config
from core.domain.composer import VideoComposer


class _FakeAudioClip:
    duration = 4.0


class _FakeVideoClip:
    def __init__(self, label: str):
        self.label = label
        self.audio = None

    def with_audio(self, audio_clip):
        self.audio = audio_clip
        return self


def _write_horizontal_gradient(path: Path, size=(400, 200)) -> None:
    width, height = size
    gradient = np.linspace(0, 255, width, dtype=np.uint8)
    image = np.repeat(gradient[np.newaxis, :, np.newaxis], height, axis=0)
    image = np.repeat(image, 3, axis=2)
    Image.fromarray(image).save(path)


def test_image_zoom_is_linear_and_keeps_output_size(tmp_path: Path):
    image_path = tmp_path / "gradient.png"
    _write_horizontal_gradient(image_path)

    clip = VideoComposer()._create_image_material_clip(
        str(image_path),
        duration=4.0,
        target_size=(200, 100),
        zoom_ratio=1.08,
    )

    first = clip.get_frame(0.0)
    middle = clip.get_frame(2.0)
    last = clip.get_frame(4.0)

    assert first.shape == middle.shape == last.shape == (100, 200, 3)
    assert first[50, 0, 0] < middle[50, 0, 0] < last[50, 0, 0]
    assert last[50, 0, 0] == pytest.approx(9, abs=2)
    assert middle[50, 0, 0] == pytest.approx(last[50, 0, 0] / 2, abs=2)
    clip.close()


def test_last_static_image_does_not_zoom_and_video_material_is_unchanged(monkeypatch):
    composer = VideoComposer()
    image_calls = []
    video_calls = []

    monkeypatch.setattr(
        "core.domain.composer.AudioFileClip",
        lambda _path: _FakeAudioClip(),
    )
    monkeypatch.setattr(
        composer,
        "_create_image_material_clip",
        lambda path, duration, size, ratio: (
            image_calls.append((path, duration, size, ratio))
            or _FakeVideoClip(path)
        ),
    )
    monkeypatch.setattr(
        composer,
        "_create_video_segment",
        lambda path, audio, size: (
            video_calls.append((path, audio, size))
            or _FakeVideoClip(path).with_audio(audio)
        ),
    )

    video_clips = []
    audio_clips = []
    composer._create_main_segments(
        ["first.png", "middle.mp4", "last.png", "ending.mp4"],
        ["1.wav", "2.wav", "3.wav", "4.wav"],
        video_clips,
        audio_clips,
        (1600, 900),
        narration_speed_factor=1.0,
        temp_audio_paths=[],
        image_zoom_in_ratio=1.08,
    )

    assert [call[3] for call in image_calls] == [1.08, 1.0]
    assert [call[0] for call in video_calls] == ["middle.mp4", "ending.mp4"]
    assert len(video_clips) == len(audio_clips) == 4


@pytest.mark.parametrize("ratio", [0, 0.99, 1.16, float("inf"), "invalid", None])
def test_image_zoom_ratio_rejects_invalid_values(monkeypatch, ratio):
    monkeypatch.setattr(config, "IMAGE_ZOOM_IN_RATIO", ratio)

    with pytest.raises(ValueError, match="Zoom In"):
        VideoComposer()._resolve_image_zoom_in_ratio()
