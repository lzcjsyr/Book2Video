from pathlib import Path

from core.domain.composer import VideoComposer


def test_resolve_subtitle_font_prefers_existing_user_path(tmp_path: Path) -> None:
    user_font = tmp_path / "custom.ttf"
    user_font.write_bytes(b"font")
    composer = VideoComposer()

    font_path, ttc_index = composer.resolve_subtitle_font(str(user_font), preferred_ttc_index=7)

    assert font_path == str(user_font)
    assert ttc_index == 7


def test_resolve_subtitle_font_falls_back_to_auto_when_user_path_is_missing(monkeypatch) -> None:
    composer = VideoComposer()
    existing_paths = {"C:/Windows/Fonts/msyh.ttc"}
    monkeypatch.setattr("core.domain.composer.os.path.exists", lambda path: path in existing_paths)

    font_path, ttc_index = composer.resolve_subtitle_font("/missing/font.ttc", preferred_ttc_index=11)

    assert font_path == "C:/Windows/Fonts/msyh.ttc"
    assert ttc_index == 0


def test_resolve_subtitle_font_auto_uses_common_system_font(monkeypatch) -> None:
    composer = VideoComposer()
    existing_paths = {"/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"}
    monkeypatch.setattr("core.domain.composer.os.path.exists", lambda path: path in existing_paths)

    font_path, ttc_index = composer.resolve_subtitle_font("auto", preferred_ttc_index=11)

    assert font_path == "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    assert ttc_index == 0
