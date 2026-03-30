"""Helpers for normalizing and reading content metadata from the new schema."""

from typing import Any, Dict, List


def ensure_book_title_format(source_name: str, fallback: str = "") -> str:
    title = (source_name or "").strip()
    if not title:
        title = (fallback or "").strip()
    if not title:
        return "《未命名作品》"
    if not (title.startswith("《") and title.endswith("》")):
        title = f"《{title.strip('《》')}》"
    return title


def strip_book_title_marks(text: str) -> str:
    return (text or "").strip().strip("《》").strip()


def normalize_text_list(raw_value: Any) -> List[str]:
    items: List[str] = []
    if isinstance(raw_value, list):
        for item in raw_value:
            if isinstance(item, str):
                candidate = item.strip()
                if candidate and candidate not in items:
                    items.append(candidate)
    elif isinstance(raw_value, str):
        candidate = raw_value.strip()
        if candidate:
            items.append(candidate)
    return items


def get_source_name(data: Dict[str, Any], fallback: str = "") -> str:
    return strip_book_title_marks((data or {}).get("source_name") or fallback)


def get_video_titles(data: Dict[str, Any]) -> List[str]:
    return normalize_text_list((data or {}).get("video_titles"))


def get_primary_video_title(data: Dict[str, Any], fallback: str = "untitled") -> str:
    titles = get_video_titles(data)
    return titles[0] if titles else fallback


def get_cover_titles(data: Dict[str, Any], fallback_title: str = "") -> List[str]:
    titles = normalize_text_list((data or {}).get("cover_titles"))
    if titles:
        return titles
    return [fallback_title] if fallback_title else []


def get_primary_cover_title(data: Dict[str, Any], fallback: str = "") -> str:
    titles = get_cover_titles(data, fallback)
    return titles[0] if titles else fallback


def get_cover_subtitles(data: Dict[str, Any]) -> List[str]:
    return normalize_text_list((data or {}).get("cover_subtitles"))


def get_primary_cover_subtitle(data: Dict[str, Any], fallback: str = "") -> str:
    subtitles = get_cover_subtitles(data)
    return subtitles[0] if subtitles else fallback


def get_golden_quotes(data: Dict[str, Any]) -> List[str]:
    return normalize_text_list((data or {}).get("golden_quotes"))


def get_primary_golden_quote(data: Dict[str, Any], fallback: str = "") -> str:
    quotes = get_golden_quotes(data)
    return quotes[0] if quotes else fallback


def get_content_title(data: Dict[str, Any], fallback: str = "") -> str:
    source_name = get_source_name(data, fallback)
    return ensure_book_title_format(source_name, fallback)
