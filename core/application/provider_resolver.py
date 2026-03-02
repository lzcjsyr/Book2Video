"""Provider auto-detection helpers for startup compatibility."""

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
        # Keep legacy default for existing image models like Qwen/Qwen-Image.
        return "siliconflow"

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


def validate_startup_args(**kwargs):
    """Backward-compatible shim kept under provider_resolver path."""
    from core.application.startup_validator import validate_startup_args as _validate

    return _validate(**kwargs)


__all__ = [
    "auto_detect_server_from_model",
    "ensure_server_supported",
    "validate_startup_args",
]
