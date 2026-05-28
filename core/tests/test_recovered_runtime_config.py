def test_recovered_prompts_keep_step2_summarizer_importable():
    import core.domain.summarizer as summarizer

    assert hasattr(summarizer, "generate_description_summary")
    assert hasattr(summarizer, "extract_keywords")
    assert not hasattr(summarizer, "intelligent_summarize")


def test_generation_params_match_cli_entrypoint_signature():
    from cli.ui_helpers import run_cli_main
    from core.config import get_generation_params

    params = get_generation_params()
    accepted = set(run_cli_main.__code__.co_varnames[:run_cli_main.__code__.co_argcount])

    assert set(params) <= accepted
    assert "llm_endpoint_step1" not in params
    assert "llm_api_key_env_step1" not in params
    assert "llm_skill_step1" not in params
    assert "llm_server_step1" not in params
    assert "target_length" not in params


def test_config_uses_single_llm_configuration_shape():
    from core.config import config

    assert hasattr(config, "LLM_SERVER_STEP2")
    assert hasattr(config, "LLM_SERVER_STEP3")
    assert hasattr(config, "LLM_BASE_URL_STEP2")
    assert hasattr(config, "LLM_BASE_URL_STEP3")
    assert hasattr(config, "LLM_SERVER_STEP1")
    assert hasattr(config, "LLM_MODEL_STEP1")
    assert not hasattr(config, "LLM_BASE_URL_STEP1")
    assert not hasattr(config, "TARGET_LENGTH")
    assert not hasattr(config, "SILICONFLOW_BASE_URL")
    assert not hasattr(config, "OPENROUTER_BASE_URL")
    assert not hasattr(config, "LLM_ENDPOINT_STEP1")
    assert not hasattr(config, "LLM_API_KEY_ENV_STEP1")
    assert not hasattr(config, "LLM_SKILL_STEP1")


def test_config_exposes_current_runtime_params():
    from core.config import config, get_generation_params

    params = get_generation_params()

    assert params["llm_server_step2"] == "siliconflow"
    assert params["llm_base_url_step2"] == config.LLM_BASE_URL_STEP2
    assert params["llm_server_step3"] == "siliconflow"
    assert params["llm_base_url_step3"] == config.LLM_BASE_URL_STEP3
    assert "siliconflow" in config.SUPPORTED_LLM_SERVERS
    assert config.IMAGE_STYLE_PRESET == params["image_style_preset"]
    assert config.RECOMMENDED_MODELS["llm"]["siliconflow"][0] == params["llm_model_step2"]
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
    from core.generation_config import VideoGenerationConfig

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
