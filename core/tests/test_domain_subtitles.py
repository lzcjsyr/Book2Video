import pytest
from PIL import Image


def test_calculate_mixed_length_counts_cjk_words_digits_and_other_letters():
    from core.domain.subtitles import calculate_mixed_length

    assert calculate_mixed_length("制度AI co-op 42é。") == 8.0


def test_calculate_subtitle_durations_weights_lines_by_mixed_length():
    from core.domain.subtitles import calculate_subtitle_durations

    durations = calculate_subtitle_durations(["制度", "AI co-op 42"], 10.0)

    assert durations[0] == pytest.approx(10.0 * 2.0 / 7.0)
    assert durations[1] == pytest.approx(10.0 - durations[0])


@pytest.mark.parametrize(
    "source,expected",
    [
        ("真正的自由，是摆脱不必要的选择。", "真正的自由 是摆脱不必要的选择"),
        ("他说：“读完《系统》，再行动！”", "他说 “读完《系统》 再行动”"),
        ('He said: "slow-down, now!"', 'He said "slow down now"'),
        ("看《思考，快与慢》：然后决定。", "看《思考 快与慢》 然后决定"),
    ],
)
def test_format_subtitle_display_text_keeps_only_double_quotes_and_book_marks(source, expected):
    from core.domain.subtitles import format_subtitle_display_text

    assert format_subtitle_display_text(source) == expected


def test_editorial_split_uses_rendered_width_and_keeps_three_char_phrase_intact():
    from core.domain.subtitles import format_subtitle_display_text, split_text_for_subtitle

    source = "教科书只告诉你三个字——李鸿章，卖国贼；"

    assert split_text_for_subtitle(
        source,
        max_chars_per_line=18,
        display_formatter=format_subtitle_display_text,
    ) == [source]
    assert format_subtitle_display_text(source) == "教科书只告诉你三个字 李鸿章 卖国贼"


@pytest.mark.parametrize(
    "source",
    [
        "请记住三个字——别着急，慢慢来；然后再做决定。",
        "答案只有两个字：系统。真正决定结果的，是结构。",
        "这本书告诉我们三件事：选择、代价和责任。",
        "他说：“教科书只告诉你三个字——李鸿章。”然后停了一下。",
        "读完《万历十五年》，你会重新理解历史叙事。",
    ],
)
def test_editorial_split_corpus_has_no_hanging_marks_or_bad_quantity_breaks(source):
    from core.domain.subtitles import format_subtitle_display_text, split_text_for_subtitle

    lines = split_text_for_subtitle(
        source,
        max_chars_per_line=18,
        display_formatter=format_subtitle_display_text,
    )
    display_lines = [format_subtitle_display_text(line) for line in lines]

    assert "".join(lines) == source
    assert all(len(line) <= 20 for line in display_lines)
    assert all(not line.endswith(tuple("《〈“‘「『（(【[")) for line in lines)
    assert all(not line.startswith(tuple("》〉”’」』）)】]，。！？；：")) for line in lines)
    assert all(not (left.endswith("三个") and right.startswith("字")) for left, right in zip(lines, lines[1:]))
    assert all(not (left.endswith("两个") and right.startswith("字")) for left, right in zip(lines, lines[1:]))


def test_editorial_split_never_cuts_inside_segmented_chinese_words():
    from core.domain.subtitles import format_subtitle_display_text, split_text_for_subtitle

    source = "你可能不熟悉这个名字，但普通人也能把复杂的经济历史讲明白。文明的兴衰，从来不是偶然。"
    lines = split_text_for_subtitle(
        source,
        max_chars_per_line=12,
        display_formatter=format_subtitle_display_text,
    )

    boundaries = {(left[-1:], right[:1]) for left, right in zip(lines, lines[1:])}
    for word in ("普通人", "复杂", "经济", "历史", "文明", "兴衰", "偶然"):
        assert all((word[index - 1], word[index]) not in boundaries for index in range(1, len(word)))


def test_editorial_split_treats_sentence_end_as_hard_boundary():
    from core.domain.subtitles import format_subtitle_display_text, split_text_for_subtitle

    lines = split_text_for_subtitle(
        "这不是巧合。真正重要的是理解结构！然后，再做选择？",
        max_chars_per_line=18,
        display_formatter=format_subtitle_display_text,
    )

    assert lines == ["这不是巧合。", "真正重要的是理解结构！", "然后，再做选择？"]


def test_editorial_split_uses_long_comma_clauses_as_natural_boundaries():
    from core.domain.subtitles import format_subtitle_display_text, split_text_for_subtitle

    lines = split_text_for_subtitle(
        "你可能不熟悉这个名字，但他绝对是金融圈里的重要人物。",
        max_chars_per_line=18,
        display_formatter=format_subtitle_display_text,
    )

    assert lines == ["你可能不熟悉这个名字，", "但他绝对是金融圈里的重要人物。"]


def test_split_text_for_subtitle_keeps_short_book_title_pairs_together():
    from core.domain.subtitles import split_text_for_subtitle

    assert split_text_for_subtitle("先看《系统》,再行动", max_chars_per_line=5) == [
        "先看",
        "《系统》,",
        "再行动",
    ]


def test_split_text_for_subtitle_evenly_splits_text_without_punctuation():
    from core.domain.subtitles import split_text_for_subtitle

    assert split_text_for_subtitle("abcdefghij", max_chars_per_line=4) == [
        "abcd",
        "efg",
        "hij",
    ]


@pytest.mark.parametrize(
    "text,pair",
    [
        ('他说："别急，答案会来。"然后笑了。', '"别急，答案会来。"'),
        ('他说：“别急，答案会来。”然后笑了。', '“别急，答案会来。”'),
        ("读完《被讨厌的勇气》，你会重新理解自由。", "《被讨厌的勇气》"),
        ("先看「系统」，再谈『努力』。", "「系统」"),
    ],
)
def test_split_text_for_subtitle_keeps_common_short_pairs_in_one_caption(text, pair):
    from core.domain.subtitles import split_text_for_subtitle

    lines = split_text_for_subtitle(text, max_chars_per_line=18)

    assert any(pair in line for line in lines)


def test_split_text_for_subtitle_avoids_hanging_pair_marks_and_tiny_tail():
    from core.domain.subtitles import split_text_for_subtitle

    lines = split_text_for_subtitle(
        '他说："真正的自由，是摆脱不必要的选择。"然后沉默了。',
        max_chars_per_line=18,
    )

    assert lines == ['他说：', '"真正的自由，是摆脱不必要的选择。"', '然后沉默了。']
    assert all(not line.endswith(tuple("《〈“‘「『（(【[")) for line in lines)
    assert all(not line.startswith(tuple("》〉”’」』）)】]，。！？；：")) for line in lines)
    assert len(lines[-1]) >= 4


def test_split_text_for_subtitle_prefers_natural_phrase_boundary_over_short_tail():
    from core.domain.subtitles import split_text_for_subtitle

    assert split_text_for_subtitle(
        "很多人以为努力就会成功，但真正决定结果的，是系统。",
        max_chars_per_line=18,
    ) == [
        "很多人以为努力就会成功，",
        "但真正决定结果的，是系统。",
    ]


def test_split_text_for_subtitle_keeps_trailing_punctuation_with_max_size_pair():
    from core.domain.subtitles import split_text_for_subtitle

    pair = "《一二三四五六七八九十一二三四五六七八》"
    lines = split_text_for_subtitle(f"读完{pair}，再行动。", max_chars_per_line=18)

    assert any(line == f"{pair}，" for line in lines)
    assert all(not line.startswith("，") for line in lines)


def test_split_text_for_subtitle_protects_short_nested_pair_inside_long_quote():
    from core.domain.subtitles import split_text_for_subtitle

    nested = "【那只咬了（那只吃了老鼠的）猫的】"
    lines = split_text_for_subtitle(
        f"你还可以说“{nested}狗叫了”。",
        max_chars_per_line=18,
    )

    assert any(nested in line for line in lines)
    assert all(not line.endswith(tuple("《〈“‘「『（(【[")) for line in lines)


def test_video_composer_keeps_subtitle_helper_compatibility():
    from core.domain.composer import VideoComposer
    from core.domain.subtitles import calculate_subtitle_durations, split_text_for_subtitle

    composer = VideoComposer()

    assert composer.split_text_for_subtitle("先看《系统》,再行动", 5) == split_text_for_subtitle(
        "先看《系统》,再行动",
        5,
    )
    assert composer._calculate_subtitle_durations(["制度", "AI co-op 42"], 10.0) == (
        calculate_subtitle_durations(["制度", "AI co-op 42"], 10.0)
    )


def test_video_composer_scales_subtitle_style_from_720p_baseline():
    from core.domain.composer import VideoComposer

    scaled = VideoComposer()._scale_subtitle_config_for_video(
        {
            "font_size": 58,
            "stroke_width": 6,
            "margin_bottom": 70,
            "letter_spacing": 1,
            "shadow_offset": (0, 3),
        },
        1600,
        900,
    )

    assert scaled["font_size"] == 72
    assert scaled["stroke_width"] == 8
    assert scaled["margin_bottom"] == 88
    assert scaled["letter_spacing"] == 1
    assert scaled["shadow_offset"] == (0, 4)


def test_editorial_subtitle_card_has_rounded_dark_panel_without_accent_line(monkeypatch):
    from core.domain.composer import VideoComposer

    composer = VideoComposer()
    monkeypatch.setattr(
        composer,
        "_create_text_image_pil",
        lambda **_kwargs: Image.new("RGBA", (760, 70), (246, 240, 226, 255)),
    )

    card = composer._create_editorial_subtitle_card(
        "真正的自由，是摆脱不必要的选择",
        {"font_size": 66, "letter_spacing": 1},
        "/fonts/serif.ttc",
        1,
        1280,
    )

    assert card.width <= int(1280 * 0.90)
    assert card.getpixel((card.width // 2, 4))[3] > 0
    assert all(pixel[:3] != (202, 91, 69) for pixel in card.getdata())


def test_editorial_style_replaces_other_punctuation_with_spaces(monkeypatch):
    from core.domain.composer import VideoComposer

    composer = VideoComposer()
    captured = []
    monkeypatch.setattr(composer, "resolve_subtitle_font", lambda *_args: ("/fonts/serif.ttc", 1))
    monkeypatch.setattr(
        composer,
        "_create_subtitle_clips_internal",
        lambda display_text, *_args: captured.append(display_text) or [],
    )

    composer.create_subtitle_clips(
        {"segments": [{"content": "读完《被讨厌的勇气》，你会重新理解自由。", "estimated_duration": 3}]},
        {
            "style": "editorial",
            "font_family": "auto",
            "ttc_index": 0,
            "font_size": 66,
            "video_size": (1280, 720),
            "max_chars_per_line": 18,
            "max_lines": 1,
        },
    )

    assert captured == ["读完《被讨厌的勇气》", "你会重新理解自由"]


def test_editorial_composer_keeps_target_sentence_in_one_caption(monkeypatch):
    from core.domain.composer import VideoComposer

    composer = VideoComposer()
    captured = []
    monkeypatch.setattr(composer, "resolve_subtitle_font", lambda *_args: ("/fonts/serif.ttc", 1))
    monkeypatch.setattr(
        composer,
        "_create_subtitle_clips_internal",
        lambda display_text, *_args: captured.append(display_text) or [],
    )

    composer.create_subtitle_clips(
        {"segments": [{"content": "教科书只告诉你三个字——李鸿章，卖国贼；", "estimated_duration": 3}]},
        {
            "style": "editorial",
            "font_family": "auto",
            "ttc_index": 0,
            "font_size": 66,
            "video_size": (1280, 720),
            "max_chars_per_line": 18,
            "max_lines": 1,
        },
    )

    assert captured == ["教科书只告诉你三个字 李鸿章 卖国贼"]
