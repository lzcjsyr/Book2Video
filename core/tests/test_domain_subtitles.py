import pytest


def test_calculate_mixed_length_counts_cjk_words_digits_and_other_letters():
    from core.domain.subtitles import calculate_mixed_length

    assert calculate_mixed_length("制度AI co-op 42é。") == 8.0


def test_calculate_subtitle_durations_weights_lines_by_mixed_length():
    from core.domain.subtitles import calculate_subtitle_durations

    durations = calculate_subtitle_durations(["制度", "AI co-op 42"], 10.0)

    assert durations[0] == pytest.approx(10.0 * 2.0 / 7.0)
    assert durations[1] == pytest.approx(10.0 - durations[0])


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
