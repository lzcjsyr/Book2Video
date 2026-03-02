"""Gateway module that isolates concrete LLM client imports from domain logic."""

from core.infra.ai.llm_client import text_to_text

__all__ = ["text_to_text"]
