import sys
import types

from core.config import config
from core.infra.ai.llm_client import text_to_image_doubao


def test_seedream5_uses_new_image_generation_parameters(monkeypatch):
    captured = {}

    class FakeImages:
        def generate(self, **kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(
                data=[types.SimpleNamespace(url="https://example.com/image.png")]
            )

    class FakeArk:
        def __init__(self, **kwargs):
            captured["client"] = kwargs
            self.images = FakeImages()

    fake_module = types.SimpleNamespace(Ark=FakeArk)
    monkeypatch.setitem(sys.modules, "volcenginesdkarkruntime", fake_module)
    monkeypatch.setattr(config, "VOLCENGINE_API_KEY", "test-key")

    url = text_to_image_doubao(
        "test prompt",
        size="1920x1920",
        model="doubao-seedream-5-0-260128",
    )

    assert url == "https://example.com/image.png"
    assert captured["model"] == "doubao-seedream-5-0-260128"
    assert captured["size"] == "1920x1920"
    assert captured["response_format"] == "url"
    assert captured["watermark"] is False
    assert "guidance_scale" not in captured


def test_seedream5_size_requires_at_least_3686400_pixels():
    assert config.validate_image_size("1920x1920", "doubao-seedream-5-0-260128")
    assert not config.validate_image_size("1024x1024", "doubao-seedream-5-0-260128")
