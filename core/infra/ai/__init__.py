"""Lazy public exports for AI adapters."""

from core._lazy import lazy_dir, lazy_getattr

_EXPORTS = {
    "text_to_text": ("core.infra.ai.llm_client", "text_to_text"),
    "text_to_image_doubao": ("core.infra.ai.llm_client", "text_to_image_doubao"),
    "text_to_image_google": ("core.infra.ai.llm_client", "text_to_image_google"),
    "text_to_audio_bytedance": (
        "core.infra.ai.tts_client",
        "text_to_audio_bytedance",
    ),
    "generate_images_for_segments": (
        "core.infra.ai.image_client",
        "generate_images_for_segments",
    ),
    "generate_cover_images": ("core.infra.ai.image_client", "generate_cover_images"),
    "synthesize_voice_for_segments": (
        "core.infra.ai.image_client",
        "synthesize_voice_for_segments",
    ),
}

__all__ = list(_EXPORTS)

__getattr__ = lazy_getattr(__name__, globals(), _EXPORTS)
__dir__ = lazy_dir(globals(), __all__)
