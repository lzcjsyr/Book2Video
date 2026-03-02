"""Startup argument validation compatible with historical import path."""

from typing import Tuple

from core.application.provider_resolver import auto_detect_server_from_model, ensure_server_supported
from core.config import Config


def validate_startup_args(
    *,
    target_length: int,
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

    # Reuse central validation to keep behavior aligned with runtime.
    Config.validate_parameters(
        target_length=target_length,
        num_segments=num_segments,
        llm_server=llm_server,
        image_server=image_server,
        tts_server=tts_server,
        image_model=image_model,
        image_size=image_size,
        llm_model=llm_model,
    )
    return llm_server, image_server, tts_server


__all__ = ["validate_startup_args"]

