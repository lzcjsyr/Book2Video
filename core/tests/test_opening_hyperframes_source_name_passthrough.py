import json
from pathlib import Path

from core.infra import hyperframes
from core.infra.hyperframes import opening_renderer
from core.config import config


def test_render_opening_video_preserves_source_name_text(monkeypatch, tmp_path: Path):
    captured = {}

    def fake_run(command, cwd, check, stdin, *args, **kwargs):
        assert command[0] == "npx"
        assert command[1] == "--yes"
        assert command[2] == "hyperframes@0.6.84"
        assert command[3] == "render"
        assert command[4] == "--output"
        assert command[6] == "--variables"
        captured["props"] = json.loads(command[7])
        Path(command[5]).write_bytes(b"opening-video")

    monkeypatch.setattr(opening_renderer.subprocess, "run", fake_run)

    result = hyperframes.render_opening_video(
        image_size="1280x720",
        output_dir=str(tmp_path),
        script_data={
            "golden_quotes": ["真正拉开差距的，不是努力，而是你能不能看懂系统。"],
            "source_name": "《系统思维》：看见结构，而不是只看结果",
        },
        opening_quote=True,
    )

    assert result == str((tmp_path / "opening.mp4").resolve())
    assert captured["props"]["bookTitle"] == "——《系统思维》：看见结构，而不是只看结果——"


def test_render_opening_video_extracts_focus_words_from_markers(monkeypatch, tmp_path: Path):
    captured = {}

    def fake_run(command, cwd, check, stdin, *args, **kwargs):
        assert command[0] == "npx"
        captured["props"] = json.loads(command[7])
        Path(command[5]).write_bytes(b"opening-video")

    monkeypatch.setattr(opening_renderer.subprocess, "run", fake_run)

    hyperframes.render_opening_video(
        image_size="1280x720",
        output_dir=str(tmp_path),
        script_data={
            "golden_quotes": ["真正拉开差距的，不是【努力】，而是你能不能看懂【系统】。"],
            "source_name": "《系统思维》",
        },
        opening_quote=True,
    )

    assert captured["props"]["focusWords"] == ["努力", "系统"]
    assert "".join(captured["props"]["focusWords"]) == "努力系统"
    assert "".join(captured["props"]["quoteLines"]) == "真正拉开差距的，不是努力，而是你能不能看懂系统。"


def test_split_quote_lines_keeps_each_sentence_fragment_on_its_own_line(monkeypatch):
    monkeypatch.setattr(config, "OPENING_HYPERFRAMES_MAX_CHARS_PER_LINE", 20)
    monkeypatch.setattr(config, "OPENING_HYPERFRAMES_MAX_LINES", 4)

    assert opening_renderer._split_quote_lines("第一段，第二段，第三段。") == [
        "第一段，",
        "第二段，",
        "第三段。",
    ]


def test_render_opening_video_distributes_line_appearance_times(monkeypatch, tmp_path: Path):
    captured = {}

    monkeypatch.setattr(config, "OPENING_HYPERFRAMES_FIRST_LINE_SECONDS", 0.5)
    monkeypatch.setattr(config, "OPENING_HYPERFRAMES_LAST_LINE_SECONDS", 2.0)
    monkeypatch.setattr(
        opening_renderer,
        "_split_quote_lines",
        lambda _quote: ["第一行", "第二行", "第三行", "第四行"],
    )

    def fake_run(command, cwd, check, stdin, *args, **kwargs):
        assert command[0] == "npx"
        captured["props"] = json.loads(command[7])
        Path(command[5]).write_bytes(b"opening-video")

    monkeypatch.setattr(opening_renderer.subprocess, "run", fake_run)

    hyperframes.render_opening_video(
        image_size="1280x720",
        output_dir=str(tmp_path),
        script_data={
            "golden_quotes": ["任意金句内容"],
            "source_name": "《系统思维》",
        },
        opening_quote=True,
    )

    assert captured["props"]["lineAppearTimes"] == [0.5, 1.0, 1.5, 2.0]


def test_render_opening_video_uses_configured_hyperframes_params(monkeypatch, tmp_path: Path):
    captured = {}

    monkeypatch.setattr(config, "OPENING_HYPERFRAMES_IP_NAME", "测试刊头")
    monkeypatch.setattr(config, "OPENING_HYPERFRAMES_DURATION_SECONDS", 5.0)
    monkeypatch.setattr(config, "OPENING_HYPERFRAMES_FPS", 30)
    monkeypatch.setattr(config, "OPENING_HYPERFRAMES_FIRST_LINE_SECONDS", 0.8)
    monkeypatch.setattr(config, "OPENING_HYPERFRAMES_LAST_LINE_SECONDS", 2.6)
    monkeypatch.setattr(config, "OPENING_HYPERFRAMES_MAX_CHARS_PER_LINE", 8)
    monkeypatch.setattr(config, "OPENING_HYPERFRAMES_MAX_LINES", 3)

    def fake_run(command, cwd, check, stdin, *args, **kwargs):
        assert command[0] == "npx"
        captured["props"] = json.loads(command[7])
        Path(command[5]).write_bytes(b"opening-video")

    monkeypatch.setattr(opening_renderer.subprocess, "run", fake_run)

    hyperframes.render_opening_video(
        image_size="1280x720",
        output_dir=str(tmp_path),
        script_data={
            "golden_quotes": ["真正拉开差距的，不是努力，而是你能不能看懂系统。"],
            "source_name": "《系统思维》",
        },
        opening_quote=True,
    )

    assert captured["props"]["ipName"] == "测试刊头"
    assert captured["props"]["durationSeconds"] == 5.0
    assert len(captured["props"]["quoteLines"]) <= 3
    assert captured["props"]["lineAppearTimes"][0] == 0.8
    assert captured["props"]["lineAppearTimes"][-1] == 2.6


def test_render_opening_video_clamps_line_timing_within_duration(monkeypatch, tmp_path: Path):
    captured = {}

    monkeypatch.setattr(config, "OPENING_HYPERFRAMES_DURATION_SECONDS", 1.0)
    monkeypatch.setattr(config, "OPENING_HYPERFRAMES_FPS", 20)
    monkeypatch.setattr(config, "OPENING_HYPERFRAMES_FIRST_LINE_SECONDS", 0.8)
    monkeypatch.setattr(config, "OPENING_HYPERFRAMES_LAST_LINE_SECONDS", 2.0)

    def fake_run(command, cwd, check, stdin, *args, **kwargs):
        assert command[0] == "npx"
        captured["props"] = json.loads(command[7])
        Path(command[5]).write_bytes(b"opening-video")

    monkeypatch.setattr(opening_renderer.subprocess, "run", fake_run)

    hyperframes.render_opening_video(
        image_size="1280x720",
        output_dir=str(tmp_path),
        script_data={
            "golden_quotes": ["第一行。第二行。"],
            "source_name": "《系统思维》",
        },
        opening_quote=True,
    )

    assert captured["props"]["durationSeconds"] == 1.0
    assert captured["props"]["lineAppearTimes"][-1] <= 0.95
