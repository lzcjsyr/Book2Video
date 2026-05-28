"""Image provider adapters and registry."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from core.infra.ai.llm_client import text_to_image_doubao, text_to_image_google


class ImageProvider(ABC):
    @abstractmethod
    def generate(self, *, prompt: str, size: str, model: str) -> Dict[str, Any]:
        """Generate an image and return normalized image data."""


class DoubaoImageProvider(ImageProvider):
    def generate(self, *, prompt: str, size: str, model: str) -> Dict[str, Any]:
        image_url = text_to_image_doubao(
            prompt=prompt,
            size=size,
            model=model,
        )
        if not image_url:
            raise ValueError("图像生成返回空URL")
        return {"type": "url", "data": image_url}


class GoogleImageProvider(ImageProvider):
    def __init__(self, *, use_adc: bool = False):
        self.use_adc = use_adc

    def generate(self, *, prompt: str, size: str, model: str) -> Dict[str, Any]:
        return text_to_image_google(
            prompt=prompt,
            size=size,
            model=model,
            use_adc=self.use_adc,
        )


IMAGE_PROVIDERS: Dict[str, ImageProvider] = {
    "doubao": DoubaoImageProvider(),
    "google": GoogleImageProvider(),
    "google_adc": GoogleImageProvider(use_adc=True),
}
