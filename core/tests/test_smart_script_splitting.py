from core.domain.summarizer import process_raw_to_script
import pytest


def test_auto_split_groups_short_sentences_without_empty_segments():
    raw_data = {
        "video_titles": ["测试"],
        "content": "好。是的！为什么？因为系统会放大选择。最后回到行动。",
    }

    script = process_raw_to_script(raw_data, num_segments=20, split_mode="auto")
    contents = [segment["content"] for segment in script["segments"]]

    assert contents == ["好。是的！为什么？", "因为系统会放大选择。最后回到行动。"]
    assert script["actual_segments"] == 2
    assert all(content.strip() for content in contents)


def test_auto_split_does_not_add_period_after_paragraph_newlines():
    raw_data = {
        "video_titles": ["测试"],
        "content": "第一段已经结束！\n第二段继续说明。\n第三段收束。",
    }

    script = process_raw_to_script(raw_data, num_segments=3, split_mode="auto")
    combined = "".join(segment["content"] for segment in script["segments"])

    assert "！。" not in combined
    assert "第一段已经结束！" in combined


def test_agent_segments_keep_script_shape_and_visualizer_choices():
    raw_data = {
        "source_name": "原始作品",
        "video_titles": ["测试"],
        "cover_titles": ["测试"],
        "cover_subtitles": [],
        "golden_quotes": [],
        "content": "收入增长了百分之三十，但利润率继续承压。小镇的夜雨落下来，母亲把灯留到很晚。",
    }

    script = process_raw_to_script(
        raw_data,
        num_segments=2,
        split_mode="agent",
        agent_segments=[
            {"content": "收入增长了百分之三十，但利润率继续承压。", "visualizer": "hf"},
            {"content": "小镇的夜雨落下来，母亲把灯留到很晚。", "visualizer": "image"},
        ],
    )

    assert script["actual_segments"] == 2
    assert script["segments"][0]["index"] == 1
    assert script["segments"][0]["visualizer"] == "hf"
    assert script["segments"][1]["visualizer"] == "image"
    assert "length" in script["segments"][0]
    assert "estimated_duration" in script["segments"][0]


def test_agent_segments_reject_legacy_hyper_visualizer():
    raw_data = {
        "video_titles": ["测试"],
        "content": "收入增长了百分之三十，但利润率继续承压。",
    }

    with pytest.raises(ValueError, match="visualizer 不支持: hyper"):
        process_raw_to_script(
            raw_data,
            num_segments=1,
            split_mode="agent",
            agent_segments=[
                {"content": "收入增长了百分之三十，但利润率继续承压。", "visualizer": "hyper"},
            ],
        )


def test_manual_split_hf_marker_sets_visualizer_and_removes_marker():
    raw_data = {
        "video_titles": ["测试"],
        "content": "第一段普通画面。\n第二段调用动态画面。【hf】\n第三段普通画面。",
    }

    script = process_raw_to_script(raw_data, num_segments=3, split_mode="manual")

    assert [segment["content"] for segment in script["segments"]] == [
        "第一段普通画面。",
        "第二段调用动态画面。",
        "第三段普通画面。",
    ]
    assert [segment["visualizer"] for segment in script["segments"]] == ["image", "hf", "image"]


def test_agent_split_keeps_same_script_contract_as_rule_modes():
    raw_data = {
        "source_name": "测试来源",
        "video_titles": ["测试"],
        "cover_titles": ["封面"],
        "cover_subtitles": ["副标题"],
        "golden_quotes": ["金句。"],
        "content": "收入增长很快，但利润率承压。她走进雨夜，把灯留在窗口。",
    }

    auto_script = process_raw_to_script(raw_data, num_segments=2, split_mode="auto")
    agent_script = process_raw_to_script(
        raw_data,
        num_segments=2,
        split_mode="agent",
        agent_segments=[
            {"content": "收入增长很快，但利润率承压。", "visualizer": "hf"},
            {"content": "她走进雨夜，把灯留在窗口。", "visualizer": "image"},
        ],
    )

    assert set(agent_script) == set(auto_script)
    assert set(agent_script["segments"][0]) == set(auto_script["segments"][0])
    assert agent_script["actual_segments"] == len(agent_script["segments"])
    assert [segment["index"] for segment in agent_script["segments"]] == [1, 2]


def test_agent_segments_accept_sentence_ending_before_straight_quote():
    raw_data = {
        "video_titles": ["测试"],
        "content": '他说："你们一定是来叫魂的！"人群越聚越多。',
    }

    script = process_raw_to_script(
        raw_data,
        num_segments=2,
        split_mode="agent",
        agent_segments=[
            {"content": '他说："你们一定是来叫魂的！"', "visualizer": "image"},
            {"content": "人群越聚越多。", "visualizer": "image"},
        ],
    )

    assert script["actual_segments"] == 2


def test_agent_segments_reject_split_inside_sentence():
    raw_data = {
        "video_titles": ["测试"],
        "content": "收入增长了百分之三十，但利润率继续承压。",
    }

    with pytest.raises(ValueError, match="句子内部"):
        process_raw_to_script(
            raw_data,
            num_segments=2,
            split_mode="agent",
            agent_segments=[
                {"content": "收入增长了百分之三十，", "visualizer": "hf"},
                {"content": "但利润率继续承压。", "visualizer": "hf"},
            ],
        )
