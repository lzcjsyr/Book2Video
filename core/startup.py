"""CLI startup validation: resolve providers from model names."""

from typing import Tuple

from core.config import Config


def auto_detect_server_from_model(model: str, model_type: str) -> str:
    """Infer provider from model identifier with conservative defaults."""
    model_text = (model or "").strip()
    lower_model = model_text.lower()
    kind = (model_type or "").strip().lower()

    if kind == "llm":
        siliconflow_prefixes = ("zai-org/", "moonshotai/", "qwen/", "deepseek-ai/")
        if lower_model.startswith(siliconflow_prefixes):
            return "siliconflow"
        return "openrouter"

    if kind == "image":
        if "doubao" in lower_model or "seedream" in lower_model:
            return "doubao"
        if "gemini" in lower_model or "imagen" in lower_model:
            return "google"
        raise ValueError(f"无法根据图像模型推断供应商: {model}")

    if kind == "voice":
        return "bytedance"

    raise ValueError(f"不支持的模型类型: {model_type}")


def ensure_server_supported(server: str, model_type: str) -> str:
    """Validate a resolved server against current Config support lists."""
    normalized = (server or "").strip().lower()
    kind = (model_type or "").strip().lower()

    if kind == "llm":
        if normalized not in Config.SUPPORTED_LLM_SERVERS:
            raise ValueError(f"不支持的LLM服务商: {normalized}")
        return normalized
    if kind == "image":
        if normalized not in Config.SUPPORTED_IMAGE_SERVERS:
            raise ValueError(f"不支持的图像服务商: {normalized}")
        return normalized
    if kind == "voice":
        if normalized not in Config.SUPPORTED_TTS_SERVERS:
            raise ValueError(f"不支持的TTS服务商: {normalized}")
        return normalized
    raise ValueError(f"不支持的模型类型: {model_type}")


def validate_startup_args(
    *,
    num_segments: int,
    image_size: str,
    llm_model: str,
    image_model: str,
    voice: str,
) -> Tuple[str, str, str]:
    """Resolve providers from model names and validate startup parameters."""
    llm_server = ensure_server_supported(auto_detect_server_from_model(llm_model, "llm"), "llm")
    image_server = ensure_server_supported(auto_detect_server_from_model(image_model, "image"), "image")
    tts_server = ensure_server_supported(auto_detect_server_from_model(voice, "voice"), "voice")

    Config.validate_parameters(
        num_segments=num_segments,
        llm_server=llm_server,
        image_server=image_server,
        tts_server=tts_server,
        image_model=image_model,
        image_size=image_size,
        llm_model=llm_model,
    )
    return llm_server, image_server, tts_server


__all__ = [
    "auto_detect_server_from_model",
    "ensure_server_supported",
    "validate_startup_args",
]
