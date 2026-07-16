from pathlib import Path

import pytest

from core.infra.ai import image_client


def test_static_image_generation_uses_selected_prompt_template(monkeypatch, tmp_path: Path):
    captured_prompts = []

    def fake_generate(args):
        segment_index, prompt, *_ = args
        captured_prompts.append(prompt)
        return {
            "success": True,
            "segment_index": segment_index,
            "image_path": str(tmp_path / f"segment_{segment_index}.png"),
        }

    monkeypatch.setattr(image_client, "_generate_single_image", fake_generate)

    result = image_client.generate_images_for_segments(
        image_server="doubao",
        model="doubao-seedream-4-0-250828",
        script_data={"segments": [{"index": 1, "content": "一个人在困境中找到新的方向"}]},
        image_style_preset="style01",
        image_size="1280x720",
        output_dir=str(tmp_path),
        description_data={"summary": "关于个人成长与选择的故事"},
        image_prompt_template="pure_images",
    )

    assert result["failed_segments"] == []
    assert len(captured_prompts) == 1
    assert "电影感叙事配图" in captured_prompts[0]
    assert "一个人在困境中找到新的方向" in captured_prompts[0]
    assert "关于个人成长与选择的故事" in captured_prompts[0]
    assert "不得出现任何文字" in captured_prompts[0]


def test_static_image_generation_rejects_unknown_prompt_template(tmp_path: Path):
    with pytest.raises(ValueError, match="不支持的步骤4生图提示词模板"):
        image_client.generate_images_for_segments(
            image_server="doubao",
            model="doubao-seedream-4-0-250828",
            script_data={"segments": [{"index": 1, "content": "测试段落"}]},
            image_style_preset="style01",
            image_size="1280x720",
            output_dir=str(tmp_path),
            description_data={"summary": "测试全文"},
            image_prompt_template="missing-template",
        )
