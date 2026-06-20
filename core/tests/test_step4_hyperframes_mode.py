import json
import wave
from pathlib import Path

from core.config import get_generation_params
from core.cli import ui_helpers
from core.infra.project_paths import ProjectPaths
from core.pipeline import steps


def _write_project(project_dir: Path, *, with_voice: bool = True) -> ProjectPaths:
    paths = ProjectPaths(str(project_dir))
    paths.ensure_dirs_exist()
    script = {
        "actual_segments": 2,
        "segments": [
            {"index": 1, "content": "第一段口播", "title": "第一段"},
            {"index": 2, "content": "第二段口播", "title": "第二段"},
        ],
    }
    Path(paths.script_json()).write_text(json.dumps(script, ensure_ascii=False), encoding="utf-8")
    Path(paths.keywords_json()).write_text(
        json.dumps({"segments": [{"index": 1, "keywords": ["增长"]}, {"index": 2, "keywords": ["风险"]}]}, ensure_ascii=False),
        encoding="utf-8",
    )
    if with_voice:
        _write_wav(Path(paths.voice) / "voice_1.wav", seconds=0.25)
        _write_wav(Path(paths.voice) / "voice_2.wav", seconds=0.5)
    return paths


def _write_wav(path: Path, *, seconds: float) -> None:
    frame_rate = 8000
    frame_count = int(frame_rate * seconds)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(frame_rate)
        handle.writeframes(b"\x00\x00" * frame_count)


def test_generation_params_include_hyperframes_visual_mode(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
step4:
  visual_mode: hyperframes_agent
  hyperframes_style_preset: data_driven
  hyperframes_max_turns: 12
  hyperframes_render_fps: 60
  hyperframes_concurrency: 2
""",
        encoding="utf-8",
    )

    params = get_generation_params(config_path)

    assert params["visual_mode"] == "hyperframes_agent"
    assert params["hyperframes_style_preset"] == "data_driven"
    assert params["hyperframes_max_turns"] == 12
    assert params["hyperframes_render_fps"] == 60
    assert params["hyperframes_concurrency"] == 2


def test_generation_params_include_mixed_visual_mode(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
step4:
  visual_mode: mixed
""",
        encoding="utf-8",
    )

    params = get_generation_params(config_path)

    assert params["visual_mode"] == "mixed"


def test_prompt_visual_mode_choice_offers_mixed_mode(monkeypatch):
    captured = {}

    def fake_prompt_choice(message, options, default_index=0):
        captured["message"] = message
        captured["options"] = options
        captured["default_index"] = default_index
        return options[2]

    monkeypatch.setattr(ui_helpers, "prompt_choice", fake_prompt_choice)

    selected = ui_helpers.prompt_visual_mode_choice("mixed")

    assert selected == "mixed"
    assert any(option.startswith("mixed:") for option in captured["options"])
    assert captured["default_index"] == 2


def test_cli_step_4_mixed_mode_prompts_both_style_choices(monkeypatch, tmp_path):
    style_calls = []
    captured = {}

    monkeypatch.setattr(ui_helpers, "prompt_visual_mode_choice", lambda *_args, **_kwargs: "mixed")
    monkeypatch.setattr(
        ui_helpers,
        "prompt_image_style_choice",
        lambda *_args, **_kwargs: style_calls.append("image") or "style08",
    )
    monkeypatch.setattr(
        ui_helpers,
        "prompt_hyperframes_style_choice",
        lambda *_args, **_kwargs: style_calls.append("hf") or "dark_premium",
    )
    monkeypatch.setattr(
        ui_helpers,
        "_prompt_segment_generation_scope",
        lambda *_args, **_kwargs: {"mode": "full", "segments": []},
    )

    def fake_run_step_4(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return {"success": True}

    monkeypatch.setattr(steps, "run_step_4", fake_run_step_4)

    result = ui_helpers._run_specific_step(
        4,
        str(tmp_path),
        "llm2",
        "model2",
        "base2",
        "llm4",
        "model4",
        "base4",
        "doubao",
        "image-model",
        "1280x720",
        "1280x720",
        "style01",
        "keywords",
        "bytedance",
        "voice-id",
        "tts-model",
        0,
        0,
        "neutral",
        4,
        2,
        True,
        None,
        "1280x720",
        "doubao",
        "cover-model",
        "cover01",
        1,
        False,
        400,
        200,
        100,
        "static_image",
        "data_driven",
        20,
        30,
        1,
    )

    assert result["success"] is True
    assert style_calls == ["image", "hf"]
    assert captured["args"][3] == "style08"
    assert captured["kwargs"]["visual_mode"] == "mixed"
    assert captured["kwargs"]["hyperframes_style_preset"] == "dark_premium"


def test_run_step_4_static_image_mode_keeps_existing_generator(monkeypatch, tmp_path):
    paths = _write_project(tmp_path / "project")
    captured = {}

    def fake_generate_images(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        image_path = Path(paths.images) / "segment_1.png"
        image_path.write_bytes(b"image")
        return {"image_paths": [str(image_path)], "failed_segments": [], "processed_segments": [1]}

    monkeypatch.setattr(steps, "generate_images_for_segments", fake_generate_images)
    monkeypatch.setattr(steps, "render_opening_video", lambda *args, **kwargs: None)

    result = steps.run_step_4(
        image_server="doubao",
        image_model="model",
        image_size="1280x720",
        image_style_preset="style01",
        project_output_dir=str(tmp_path / "project"),
        images_method="keywords",
        opening_quote=False,
        target_segments=[1],
        visual_mode="static_image",
    )

    assert result["success"] is True
    assert captured["args"][0] == "doubao"
    assert captured["kwargs"]["target_segments"] == [1]


def test_run_step_4_mixed_mode_dispatches_by_segment_visualizer(monkeypatch, tmp_path):
    paths = _write_project(tmp_path / "project")
    script_path = Path(paths.script_json())
    script = json.loads(script_path.read_text(encoding="utf-8"))
    script["segments"][0]["visualizer"] = "image"
    script["segments"][1]["visualizer"] = "hf"
    script_path.write_text(json.dumps(script, ensure_ascii=False), encoding="utf-8")

    captured = {"static_targets": None, "hyper_targets": None}

    def fake_generate_images(*args, **kwargs):
        captured["static_targets"] = kwargs["target_segments"]
        image_path = Path(paths.images) / "segment_1.png"
        image_path.write_bytes(b"image")
        return {"image_paths": [str(image_path), ""], "failed_segments": [], "processed_segments": [1]}

    def fake_hyperframes_renderer(**kwargs):
        captured["hyper_targets"] = kwargs["target_segments"]
        video_path = Path(paths.images) / "segment_2.mp4"
        video_path.write_bytes(b"video")
        return {"image_paths": ["", str(video_path)], "failed_segments": [], "processed_segments": [2]}

    monkeypatch.setattr(steps, "generate_images_for_segments", fake_generate_images)
    monkeypatch.setattr(steps, "render_hyperframes_segments_with_agent", fake_hyperframes_renderer, raising=False)
    monkeypatch.setattr(steps, "render_opening_video", lambda *args, **kwargs: None)

    result = steps.run_step_4(
        image_server="doubao",
        image_model="model",
        image_size="1280x720",
        image_style_preset="style01",
        project_output_dir=str(tmp_path / "project"),
        images_method="keywords",
        opening_quote=False,
        visual_mode="mixed",
    )

    assert result["success"] is True
    assert captured["static_targets"] == [1]
    assert captured["hyper_targets"] == [2]
    assert result["image_paths"][0].endswith("segment_1.png")
    assert result["image_paths"][1].endswith("segment_2.mp4")
    assert result["processed_segments"] == [1, 2]


def test_run_step_4_hyperframes_mode_dispatches_to_renderer(monkeypatch, tmp_path):
    paths = _write_project(tmp_path / "project")
    captured = {}

    def fake_hyperframes_renderer(**kwargs):
        captured.update(kwargs)
        video_path = Path(paths.images) / "segment_2.mp4"
        video_path.write_bytes(b"video")
        return {"image_paths": ["", str(video_path)], "failed_segments": [], "processed_segments": [2]}

    monkeypatch.setattr(steps, "render_opening_video", lambda *args, **kwargs: None)
    monkeypatch.setattr(steps, "render_hyperframes_segments_with_agent", fake_hyperframes_renderer, raising=False)

    result = steps.run_step_4(
        image_server="doubao",
        image_model="model",
        image_size="1280x720",
        image_style_preset="style01",
        project_output_dir=str(tmp_path / "project"),
        images_method="keywords",
        opening_quote=False,
        target_segments=[2],
        visual_mode="hyperframes_agent",
        hyperframes_style_preset="data_driven",
        hyperframes_max_turns=9,
        hyperframes_render_fps=60,
        hyperframes_concurrency=1,
        llm_server="siliconflow",
        llm_model="step4-model",
        llm_base_url="https://llm-gateway.example.test/anthropic",
    )

    assert result["success"] is True
    assert result["image_paths"][1].endswith("segment_2.mp4")
    assert captured["target_segments"] == [2]
    assert captured["style_preset"] == "data_driven"
    assert captured["max_turns"] == 9
    assert captured["render_fps"] == 60
    assert captured["llm_server"] == "siliconflow"
    assert captured["llm_model"] == "step4-model"
    assert captured["llm_base_url"] == "https://llm-gateway.example.test/anthropic"


def test_run_step_4_hyperframes_mode_requires_step3_voice(tmp_path):
    _write_project(tmp_path / "project", with_voice=False)

    result = steps.run_step_4(
        image_server="doubao",
        image_model="model",
        image_size="1280x720",
        image_style_preset="style01",
        project_output_dir=str(tmp_path / "project"),
        images_method="keywords",
        opening_quote=False,
        visual_mode="hyperframes_agent",
    )

    assert result["success"] is False
    assert result["failed_segments"] == [1, 2]
    assert "步骤3" in result["message"]
