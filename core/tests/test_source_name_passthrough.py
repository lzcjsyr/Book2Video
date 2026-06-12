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
        "content": "今天的天气非常晴朗，温度适宜。\n小明背着书包去上学，路过公园。",
        "target_segments": 2,
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
                "target_segments": 2,
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


def test_process_raw_to_script_enforces_visualizer_ratio_range():
    # Case 1: All segments are plain text (normally 100% image). Min hyper should be 30% (3 segments).
    raw_data_plain = {
        "source_name": "Test",
        "video_titles": ["Test"],
        "cover_titles": ["Test"],
        "cover_subtitles": [],
        "golden_quotes": [],
        "content": "今天天气很好。\n今天温度适宜。\n今天适合郊游。\n大家都去爬山。\n山上风景极美。\n山下有小溪流。\n溪水十分清澈。\n鱼儿自由游动。\n晚风吹拂树梢。\n月亮挂在夜空。",
        "target_segments": 10,
    }
    script_data_plain = process_raw_to_script(raw_data_plain, num_segments=10, split_mode="manual")
    visualizers_plain = [seg["visualizer"] for seg in script_data_plain["segments"]]
    hyper_count_plain = visualizers_plain.count("hyper")
    assert len(script_data_plain["segments"]) == 10
    assert hyper_count_plain >= 3

    # Case 2: All segments contain logical/data words (normally 100% hyper). Max hyper should be 70% (7 segments, meaning 3 image).
    raw_data_hyper = {
        "source_name": "Test",
        "video_titles": ["Test"],
        "cover_titles": ["Test"],
        "cover_subtitles": [],
        "golden_quotes": [],
        "content": "因为这是第一层。\n所以这是第二层。\n这意味着第三层。\n相比之下有40%。\n代码是601133。\n比手机高出两档。\n关键在于市占率。\n核心是新签订单。\n也就是说要对比。\n只要努力就成功。",
        "target_segments": 10,
    }
    script_data_hyper = process_raw_to_script(raw_data_hyper, num_segments=10, split_mode="manual")
    visualizers_hyper = [seg["visualizer"] for seg in script_data_hyper["segments"]]
    image_count_hyper = visualizers_hyper.count("image")
    assert len(script_data_hyper["segments"]) == 10
    assert image_count_hyper >= 3
