from pathlib import Path
from types import SimpleNamespace


def test_build_atempo_filter_chain_splits_extreme_speed_factors():
    from core.infra.media.ffmpeg import build_atempo_filter_chain

    assert build_atempo_filter_chain(1.0) == ""
    assert build_atempo_filter_chain(4.0) == "atempo=2,atempo=2"
    assert build_atempo_filter_chain(0.25) == "atempo=0.5,atempo=0.5"
    assert build_atempo_filter_chain(1.3333) == "atempo=1.3333"


def test_adjust_audio_speed_runs_ffmpeg_and_tracks_temp_output(monkeypatch, tmp_path: Path):
    from core.infra.media import ffmpeg

    audio_path = tmp_path / "voice.wav"
    audio_path.write_bytes(b"fake audio")
    calls = []

    monkeypatch.setattr(ffmpeg.shutil, "which", lambda name: "/usr/bin/ffmpeg" if name == "ffmpeg" else None)

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace()

    monkeypatch.setattr(ffmpeg.subprocess, "run", fake_run)

    temp_audio_paths = []
    result = ffmpeg.adjust_audio_speed(str(audio_path), 1.25, temp_audio_paths)

    try:
        assert result == temp_audio_paths[0]
        command, kwargs = calls[0]
        assert command[:4] == ["/usr/bin/ffmpeg", "-y", "-hide_banner", "-loglevel"]
        assert command[command.index("-i") + 1] == str(audio_path)
        assert command[command.index("-filter:a") + 1] == "atempo=1.25"
        assert command[-1] == result
        assert kwargs["check"] is True
        assert kwargs["stdin"] is ffmpeg.subprocess.DEVNULL
    finally:
        Path(result).unlink(missing_ok=True)


def test_normalize_loudness_single_pass_fallback_uses_project_root(monkeypatch, tmp_path: Path):
    from core.infra.media import ffmpeg

    bgm_path = tmp_path / "bgm.mp3"
    bgm_path.write_bytes(b"fake audio")
    calls = []

    monkeypatch.setattr(ffmpeg.shutil, "which", lambda name: "/usr/bin/ffmpeg" if name == "ffmpeg" else None)

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        if len(calls) == 1:
            return SimpleNamespace(stderr="no loudnorm json here")
        return SimpleNamespace(stderr="")

    monkeypatch.setattr(ffmpeg.subprocess, "run", fake_run)

    result = ffmpeg.normalize_loudness(
        str(bgm_path),
        str(tmp_path),
        target_loudness=20.0,
        loudness_range=7.0,
        enabled=True,
    )

    expected_path = str(tmp_path / "bgm_normalized.wav")
    assert result == expected_path
    assert calls[1][0][-1] == expected_path
    assert "loudnorm=I=-20.0:TP=-2.0:LRA=7.0" in calls[1][0]

