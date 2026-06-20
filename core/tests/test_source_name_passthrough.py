import json
from pathlib import Path

from core.domain.summarizer import process_raw_to_script
from core.pipeline import steps


def test_process_raw_to_script_preserves_source_name_exactly():
    raw_source_name = "《置身事内（修订版）》｜兰小欢"
    raw_data = {
        "source_name": raw_source_name,
        "video_titles": ["为什么中国经济总在关键时刻转向"],
        "cover_titles": ["为什么中国经济总在关键时刻转向"],
        "cover_subtitles": ["读懂政策与增长的底层结构"],
        "golden_quotes": ["理解宏观，不等于预测宏观。"],
        "content": "第一段内容。第二段内容。第三段内容。",
    }

    script_data = process_raw_to_script(raw_data, num_segments=2, split_mode="auto")

    assert script_data["source_name"] == raw_source_name


def test_process_raw_to_script_defaults_segment_visualizer_to_image():
    raw_data = {
        "source_name": "原始作品标题",
        "video_titles": ["视频标题"],
        "cover_titles": ["封面标题"],
        "cover_subtitles": [],
        "golden_quotes": [],
        "content": "第一段内容。\n第二段内容。",
    }

    script_data = process_raw_to_script(raw_data, num_segments=2, split_mode="manual")

    assert [segment["visualizer"] for segment in script_data["segments"]] == ["image", "image"]


def test_run_step_1_5_preserves_docx_source_name_in_script_json(monkeypatch, tmp_path: Path):
    project_dir = tmp_path / "project"
    text_dir = project_dir / "text"
    text_dir.mkdir(parents=True)

    raw_json_path = text_dir / "raw.json"
    raw_docx_path = text_dir / "raw.docx"
    script_json_path = text_dir / "script.json"

    raw_json_path.write_text(
        json.dumps(
            {
                "source_name": "旧标题",
                "video_titles": ["旧标题"],
                "cover_titles": ["旧标题"],
                "cover_subtitles": [],
                "golden_quotes": [],
                "content": "旧内容。",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    raw_docx_path.write_bytes(b"placeholder")

    raw_source_name = "《变量》：看见中国社会运行的真实逻辑"

    monkeypatch.setattr(
        "core.domain.docx_transform.parse_raw_from_docx",
        lambda _path: {
            "source_name": raw_source_name,
            "video_titles": ["看懂中国社会运行逻辑"],
            "cover_titles": ["看懂中国社会运行逻辑"],
            "cover_subtitles": ["从变化里识别结构"],
            "golden_quotes": ["真正重要的，不是结论，而是变量。"],
            "content": "第一段内容。第二段内容。第三段内容。",
        },
    )
    monkeypatch.setattr("core.domain.docx_transform.export_script_to_docx", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(steps, "export_plain_text_segments", lambda *_args, **_kwargs: str(text_dir / "script.txt"))

    result = steps.run_step_1_5(
        project_output_dir=str(project_dir),
        num_segments=2,
        is_new_project=False,
        split_mode="auto",
    )

    assert result["success"] is True
    script_data = json.loads(script_json_path.read_text(encoding="utf-8"))
    assert script_data["source_name"] == raw_source_name


def test_run_step_1_5_agent_mode_uses_agent_segments(monkeypatch, tmp_path: Path):
    project_dir = tmp_path / "project"
    text_dir = project_dir / "text"
    text_dir.mkdir(parents=True)

    raw_json_path = text_dir / "raw.json"
    script_json_path = text_dir / "script.json"
    raw_json_path.write_text(
        json.dumps(
            {
                "source_name": "测试来源",
                "video_titles": ["测试标题"],
                "cover_titles": ["测试标题"],
                "cover_subtitles": [],
                "golden_quotes": [],
                "content": "收入增长很快，但利润率承压。她走进雨夜，把灯留在窗口。",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    captured = {}

    def fake_agent(**kwargs):
        captured.update(kwargs)
        return [
            {"content": "收入增长很快，但利润率承压。", "visualizer": "hf"},
            {"content": "她走进雨夜，把灯留在窗口。", "visualizer": "image"},
        ]

    monkeypatch.setattr(steps, "run_step1_5_segment_agent", fake_agent)
    monkeypatch.setattr("core.domain.docx_transform.export_script_to_docx", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(steps, "export_plain_text_segments", lambda *_args, **_kwargs: str(text_dir / "script.txt"))

    result = steps.run_step_1_5(
        project_output_dir=str(project_dir),
        num_segments=2,
        is_new_project=False,
        split_mode="agent",
    )

    assert result["success"] is True
    assert captured["raw_json_path"] == str(raw_json_path)
    assert captured["target_segments"] == 2
    script_data = json.loads(script_json_path.read_text(encoding="utf-8"))
    assert [segment["visualizer"] for segment in script_data["segments"]] == ["hf", "image"]
