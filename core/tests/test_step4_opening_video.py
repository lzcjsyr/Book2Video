import json
from pathlib import Path

import pytest

from core.pipeline import steps


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    text_dir = project / "text"
    images_dir = project / "images"
    text_dir.mkdir(parents=True)
    images_dir.mkdir(parents=True)
    script = {
        "segments": [{"content": "segment 1"}],
        "actual_segments": 1,
        "golden_quotes": ["真正拉开差距的，不是努力，而是系统。"],
        "source_name": "系统思维",
    }
    (text_dir / "script.json").write_text(json.dumps(script, ensure_ascii=False), encoding="utf-8")
    (text_dir / "keywords.json").write_text(json.dumps({"segments": []}, ensure_ascii=False), encoding="utf-8")
    return project


def test_run_step_4_uses_opening_video_renderer_when_regenerating(monkeypatch, project_dir: Path):
    called = {"renderer": 0, "image": 0}

    def fake_load_json_file(path):
        candidate = Path(path)
        if not candidate.exists():
            return None
        return json.loads(candidate.read_text(encoding="utf-8"))

    def fake_segment_images(*args, **kwargs):
        segment_path = project_dir / "images" / "segment_1.png"
        segment_path.write_bytes(b"segment-image")
        return {"image_paths": [str(segment_path)], "failed_segments": [], "processed_segments": [1]}

    def fake_render_opening_video(*args, **kwargs):
        called["renderer"] += 1
        output_path = project_dir / "images" / "opening.mp4"
        output_path.write_bytes(b"opening-video")
        return str(output_path)

    monkeypatch.setattr(steps, "load_json_file", fake_load_json_file)
    monkeypatch.setattr(steps, "generate_images_for_segments", fake_segment_images)
    monkeypatch.setattr(steps, "render_opening_video", fake_render_opening_video)

    result = steps.run_step_4(
        image_server="doubao",
        image_model="model",
        image_size="1280x720",
        image_style_preset="style01",
        project_output_dir=str(project_dir),
        images_method="keywords",
        opening_quote=True,
        regenerate_opening=True,
    )

    assert result["success"] is True
    assert called["renderer"] == 1
    assert called["image"] == 0
    assert result["opening_image_path"].endswith("opening.mp4")


def test_run_step_4_reuses_existing_opening_video_when_not_regenerating(monkeypatch, project_dir: Path):
    existing_opening = project_dir / "images" / "opening.mp4"
    existing_opening.write_bytes(b"existing-opening-video")

    def fake_load_json_file(path):
        candidate = Path(path)
        if not candidate.exists():
            return None
        return json.loads(candidate.read_text(encoding="utf-8"))

    def fake_segment_images(*args, **kwargs):
        segment_path = project_dir / "images" / "segment_1.png"
        segment_path.write_bytes(b"segment-image")
        return {"image_paths": [str(segment_path)], "failed_segments": [], "processed_segments": [1]}

    def fail_render_opening_video(*args, **kwargs):
        raise AssertionError("renderer should not be called when opening video already exists")

    monkeypatch.setattr(steps, "load_json_file", fake_load_json_file)
    monkeypatch.setattr(steps, "generate_images_for_segments", fake_segment_images)
    monkeypatch.setattr(steps, "render_opening_video", fail_render_opening_video)

    result = steps.run_step_4(
        image_server="doubao",
        image_model="model",
        image_size="1280x720",
        image_style_preset="style01",
        project_output_dir=str(project_dir),
        images_method="keywords",
        opening_quote=True,
        regenerate_opening=False,
    )

    assert result["success"] is True
    assert result["opening_image_path"] == str(existing_opening)


def test_run_step_4_forwards_llm_config_to_image_prompt_safety(monkeypatch, project_dir: Path):
    captured = {}

    def fake_load_json_file(path):
        candidate = Path(path)
        if not candidate.exists():
            return None
        return json.loads(candidate.read_text(encoding="utf-8"))

    def fake_segment_images(*args, **kwargs):
        captured.update(kwargs)
        segment_path = project_dir / "images" / "segment_1.png"
        segment_path.write_bytes(b"segment-image")
        return {"image_paths": [str(segment_path)], "failed_segments": [], "processed_segments": [1]}

    monkeypatch.setattr(steps, "load_json_file", fake_load_json_file)
    monkeypatch.setattr(steps, "generate_images_for_segments", fake_segment_images)
    monkeypatch.setattr(steps, "render_opening_video", lambda *args, **kwargs: None)

    result = steps.run_step_4(
        image_server="doubao",
        image_model="model",
        image_size="1280x720",
        image_style_preset="style01",
        project_output_dir=str(project_dir),
        images_method="keywords",
        opening_quote=False,
        llm_model="some-llm",
        llm_server="siliconflow",
        llm_base_url="https://api.siliconflow.cn/v1",
    )

    assert result["success"] is True
    assert captured["llm_model"] == "some-llm"
    assert captured["llm_server"] == "siliconflow"
    assert captured["llm_base_url"] == "https://api.siliconflow.cn/v1"
