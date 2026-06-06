def test_generation_params_match_cli_entrypoint_signature():
    from core.cli.ui_helpers import run_cli_main
    from core.config import get_generation_params

    params = get_generation_params()
    accepted = set(run_cli_main.__code__.co_varnames[:run_cli_main.__code__.co_argcount])

    assert set(params) <= accepted


def test_config_exposes_current_runtime_params():
    from core.config import config, get_generation_params

    params = get_generation_params()

    assert params["llm_server_step2"] == "volcengine"
    assert params["llm_base_url_step2"] == config.LLM_BASE_URL_STEP2
    assert params["llm_server_step3"] == "volcengine"
    assert params["llm_base_url_step3"] == config.LLM_BASE_URL_STEP3
    assert "volcengine" in config.SUPPORTED_LLM_SERVERS
    assert config.IMAGE_STYLE_PRESET == params["image_style_preset"]
    assert params["cover_image_server"] == "google_adc"

    config.validate_parameters(
        params["num_segments"],
        params["llm_server_step2"],
        params["image_server"],
        "bytedance",
        params["image_model"],
        params["image_size"],
        images_method=params["images_method"],
        llm_model=params["llm_model_step2"],
    )


def test_google_adc_image_server_is_inherited_by_gemini_cover_defaults():
    from core.config import VideoGenerationConfig

    config = VideoGenerationConfig(
        input_file="input.pdf",
        output_dir="output",
        image_server="google_adc",
        image_model="gemini-3.1-flash-image-preview",
        cover_image_server="",
        cover_image_model=None,
    )

    assert config.cover_image_model == "gemini-3.1-flash-image-preview"
    assert config.cover_image_server == "google_adc"


def test_config_rejects_unsupported_llm_server():
    import pytest

    from core.config import config

    with pytest.raises(ValueError, match="不支持的LLM服务商"):
        config.validate_parameters(
            num_segments=5,
            llm_server="unknown",
            image_server="google",
            tts_server="bytedance",
            image_model="gemini-3.1-flash-image-preview",
            image_size="1280x720",
            images_method="description",
            llm_model="model",
        )


def test_recovered_config_keeps_cover_validation_usable(monkeypatch, tmp_path):
    from core.pipeline import steps

    captured = {}

    def fake_generate_cover_images(
        project_output_dir,
        cover_image_server,
        cover_image_model,
        cover_image_size,
        cover_image_style,
        cover_image_count,
        cover_title,
        cover_subtitle,
    ):
        captured.update(
            server=cover_image_server,
            model=cover_image_model,
            size=cover_image_size,
            style=cover_image_style,
            count=cover_image_count,
            title=cover_title,
            subtitle=cover_subtitle,
        )
        return {"success": True, "cover_images": []}

    monkeypatch.setattr(steps, "generate_cover_images", fake_generate_cover_images)

    result = steps._run_cover_generation(
        str(tmp_path),
        cover_image_size=None,
        cover_image_server="google",
        cover_image_model=None,
        cover_image_style=None,
        cover_image_count=1,
        script_data={"title": "测试标题", "segments": []},
    )

    assert result["success"] is True
    assert captured["server"] == "google"
    assert captured["model"]
