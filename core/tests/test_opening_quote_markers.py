from pathlib import Path

from core.pipeline import steps


def test_ensure_opening_narration_strips_keyword_markers_for_tts(monkeypatch, tmp_path: Path):
    captured = {}

    def fake_tts(text, output_path, **kwargs):
        captured["text"] = text
        captured["output_path"] = output_path
        Path(output_path).write_bytes(b"audio")
        return True

    monkeypatch.setattr(steps, "text_to_audio_bytedance", fake_tts)

    output = steps._ensure_opening_narration(
        script_data={
            "golden_quotes": ["真正拉开差距的，不是【努力】，而是你能不能看懂【系统】。"],
        },
        voice_dir=str(tmp_path),
        voice="voice-id",
        tts_model="tts-model",
        opening_quote=True,
        force_regenerate=True,
    )

    assert output == str(tmp_path / "opening.wav")
    assert captured["output_path"] == str(tmp_path / "opening.wav")
    assert captured["text"] == "真正拉开差距的，不是努力，而是你能不能看懂系统。"
