"""AI API clients for LLM, TTS, and Image generation."""

from core.infra.ai.llm_client import (
    text_to_text,
    text_to_image_doubao,
    text_to_image_google,
    text_to_image_siliconflow,
)
from core.infra.ai.tts_client import text_to_audio_bytedance
from core.infra.ai.image_client import (
    generate_opening_image,
    generate_images_for_segments,
    generate_cover_images,
    synthesize_voice_for_segments,
)

__all__ = [
    # LLM & Logic
    "text_to_text",
    # Image Generation
    "text_to_image_doubao",
    "text_to_image_google",
    "text_to_image_siliconflow",
    "generate_opening_image",
    "generate_images_for_segments",
    "generate_cover_images",
    # Audio/TTS
    "text_to_audio_bytedance",
    "synthesize_voice_for_segments",
]
