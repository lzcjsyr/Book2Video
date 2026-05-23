from core.domain.summarizer import process_raw_to_script


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
