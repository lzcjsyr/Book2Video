"""Create a 3:4 distribution copy around an existing landscape master.

The landscape video is the single source of truth. Its pixel dimensions are
never scaled; the 3:4 canvas and both static panels are derived from the
encoded master's actual dimensions.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Mapping, Sequence, TextIO

from PIL import Image, ImageDraw, ImageFont


_EDITORIAL_TITLE_FONTS = (
    (Path("/System/Library/Fonts/Supplemental/Songti.ttc"), 0),
    (Path("C:/Windows/Fonts/simsun.ttc"), 0),
    (Path("/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"), 0),
    (Path("/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"), 0),
)

_EDITORIAL_SUBTITLE_FONTS = (
    (Path("/System/Library/Fonts/Hiragino Sans GB.ttc"), 2),
    (Path("/System/Library/Fonts/STHeiti Medium.ttc"), 1),
    (Path("C:/Windows/Fonts/msyh.ttc"), 0),
    (Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"), 0),
)

_PANEL_COLOR = (16, 19, 24)
_TITLE_COLOR = (241, 238, 231)
_SUBTITLE_COLOR = (201, 195, 184)
_ACCENT_COLOR = (196, 90, 71)
_SEPARATOR_COLOR = (48, 55, 64)


@dataclass(frozen=True)
class _VideoMetadata:
    width: int
    height: int
    duration: float


@dataclass(frozen=True)
class ThreeByFourLayout:
    canvas_width: int
    canvas_height: int
    top_panel_height: int
    bottom_panel_height: int
    main_x: int
    main_y: int
    main_width: int
    main_height: int


def calculate_layout(source_width: int, source_height: int) -> ThreeByFourLayout:
    """Derive an encoder-safe 3:4 canvas while preserving the source rectangle."""
    width = int(source_width)
    height = int(source_height)
    if width <= 0 or height <= 0:
        raise ValueError("视频尺寸必须为正整数")
    if width <= height:
        raise ValueError("3:4贴片版只支持横屏主视频")
    if width % 2 or height % 2:
        raise ValueError("视频宽高必须为偶数，才能使用 yuv420p 编码")

    # A multiple of four keeps the canvas and both symmetric panels even,
    # while choosing the closest encoder-safe approximation to exact 3:4.
    canvas_height = max(height, int(round((width * 4 / 3) / 4)) * 4)
    remaining_height = canvas_height - height
    if remaining_height <= 0:
        raise ValueError("主视频高度超过了按宽度推导出的3:4画布")
    panel_height = remaining_height // 2

    return ThreeByFourLayout(
        canvas_width=width,
        canvas_height=canvas_height,
        top_panel_height=panel_height,
        bottom_panel_height=remaining_height - panel_height,
        main_x=0,
        main_y=panel_height,
        main_width=width,
        main_height=height,
    )


def select_cover_copy(script_data: Mapping[str, Any] | None) -> tuple[str, str]:
    """Select the first usable cover title/subtitle with legacy title fallback."""
    data = script_data or {}
    title = _first_text(data.get("cover_titles"))
    subtitle = _first_text(data.get("cover_subtitles"))
    if not title:
        title = _first_text(data.get("video_titles")) or _clean_text(data.get("source_name"))
    return title, subtitle


def derive_output_path(source_path: str | os.PathLike[str]) -> Path:
    source = Path(source_path)
    return source.with_name(f"{source.stem}_3x4{source.suffix or '.mp4'}")


def build_export_command(
    *,
    ffmpeg_path: str,
    source_path: str | os.PathLike[str],
    background_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str],
    layout: ThreeByFourLayout,
    video_codec: str,
    quality_level: int,
    hardware: bool = False,
) -> list[str]:
    """Build the post-processing command. Deliberately contains no scale filter."""
    codec_args = _encoder_args(video_codec, quality_level, hardware=hardware)
    filter_graph = (
        f"[0:v]pad={layout.canvas_width}:{layout.canvas_height}:"
        f"{layout.main_x}:{layout.main_y}:color=black[padded];"
        "[padded][1:v]overlay=0:0:shortest=1,"
        "format=yuv420p[video]"
    )
    return [
        ffmpeg_path,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-i",
        str(source_path),
        "-loop",
        "1",
        "-i",
        str(background_path),
        "-filter_complex",
        filter_graph,
        "-map",
        "[video]",
        "-map",
        "0:a?",
        *codec_args,
        "-c:a",
        "copy",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-progress",
        "pipe:1",
        "-nostats",
        "-shortest",
        str(output_path),
    ]


def export_three_by_four_video(
    source_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str] | None,
    script_data: Mapping[str, Any] | None,
    *,
    font_path: str | os.PathLike[str] | None = None,
    font_ttc_index: int = 0,
    video_codec: str = "h264",
    quality_level: int = 70,
) -> Path:
    """Add static 3:4 panels to an already-rendered landscape master."""
    source = Path(source_path)
    destination = Path(output_path) if output_path is not None else derive_output_path(source)
    if not source.is_file():
        raise FileNotFoundError(f"横屏母版不存在: {source}")
    if source.resolve() == destination.resolve():
        raise ValueError("3:4输出路径不能覆盖横屏母版")

    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")
    if not ffmpeg_path or not ffprobe_path:
        raise RuntimeError("生成3:4贴片版需要 FFmpeg 和 FFprobe")

    metadata = _probe_video_metadata(source, ffprobe_path)
    layout = calculate_layout(metadata.width, metadata.height)
    title, subtitle = select_cover_copy(script_data)
    destination.parent.mkdir(parents=True, exist_ok=True)

    temporary_output = destination.with_name(f".{destination.stem}.tmp{destination.suffix or '.mp4'}")
    with tempfile.TemporaryDirectory(prefix="aigc-video-3x4-") as temporary_dir:
        background_path = Path(temporary_dir) / "background.png"
        _render_static_background(
            background_path,
            layout,
            title,
            subtitle,
            font_path=Path(font_path) if font_path else None,
            font_ttc_index=int(font_ttc_index or 0),
        )
        software_command = build_export_command(
            ffmpeg_path=ffmpeg_path,
            source_path=source,
            background_path=background_path,
            output_path=temporary_output,
            layout=layout,
            video_codec=video_codec,
            quality_level=quality_level,
            hardware=False,
        )
        try:
            try:
                _run_export_command(
                    software_command,
                    metadata.duration,
                    label="生成3:4贴片版（高质量编码）",
                )
            except subprocess.CalledProcessError as software_error:
                temporary_output.unlink(missing_ok=True)
                print("⚠️ 高质量编码不可用，切换硬件编码…")
                hardware_command = build_export_command(
                    ffmpeg_path=ffmpeg_path,
                    source_path=source,
                    background_path=background_path,
                    output_path=temporary_output,
                    layout=layout,
                    video_codec=video_codec,
                    quality_level=quality_level,
                    hardware=True,
                )
                try:
                    _run_export_command(
                        hardware_command,
                        metadata.duration,
                        label="生成3:4贴片版（硬件编码）",
                    )
                except subprocess.CalledProcessError as hardware_error:
                    software_detail = _process_error_detail(software_error)
                    hardware_detail = _process_error_detail(hardware_error)
                    raise RuntimeError(
                        "3:4贴片版软件编码和硬件编码均失败: "
                        f"软件编码: {software_detail}; 硬件编码: {hardware_detail}"
                    ) from hardware_error

            if not temporary_output.is_file():
                raise RuntimeError("3:4贴片版编码完成但未生成输出文件")
            os.replace(temporary_output, destination)
        finally:
            temporary_output.unlink(missing_ok=True)

    return destination


def _probe_video_metadata(source_path: Path, ffprobe_path: str) -> _VideoMetadata:
    result = subprocess.run(
        [
            ffprobe_path,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height:format=duration",
            "-of",
            "json",
            str(source_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(result.stdout)
        stream = payload["streams"][0]
        return _VideoMetadata(
            width=int(stream["width"]),
            height=int(stream["height"]),
            duration=float(payload["format"]["duration"]),
        )
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"无法读取横屏母版尺寸: {source_path}") from exc


def _render_static_background(
    output_path: Path,
    layout: ThreeByFourLayout,
    title: str,
    subtitle: str,
    *,
    font_path: Path | None,
    font_ttc_index: int,
) -> None:
    title_font_path, title_font_index = _resolve_editorial_font(
        _EDITORIAL_TITLE_FONTS,
        font_path,
        font_ttc_index,
    )
    subtitle_font_path, subtitle_font_index = _resolve_editorial_font(
        _EDITORIAL_SUBTITLE_FONTS,
        font_path,
        font_ttc_index,
    )
    image = Image.new("RGBA", (layout.canvas_width, layout.canvas_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle(
        (0, 0, layout.canvas_width - 1, layout.top_panel_height - 1),
        fill=_PANEL_COLOR,
    )
    separator = max(2, layout.canvas_width // 640)
    draw.rectangle(
        (0, layout.main_y - separator, layout.canvas_width, layout.main_y - 1),
        fill=_SEPARATOR_COLOR,
    )
    bottom_y = layout.main_y + layout.main_height
    draw.rectangle(
        (0, bottom_y, layout.canvas_width - 1, layout.canvas_height - 1),
        fill=_PANEL_COLOR,
    )
    draw.rectangle(
        (0, bottom_y, layout.canvas_width, bottom_y + separator - 1),
        fill=_SEPARATOR_COLOR,
    )

    horizontal_padding = max(16, int(layout.canvas_width * 0.08))
    max_text_width = layout.canvas_width - horizontal_padding * 2
    if title:
        _draw_fitted_tracking_text(
            draw,
            title,
            centre=(layout.canvas_width // 2, int(layout.top_panel_height * 0.48)),
            max_width=max_text_width,
            max_height=max(1, int(layout.top_panel_height * 0.42)),
            preferred_size=max(18, int(layout.canvas_width * 0.082)),
            tracking_ratio=0.035,
            fill=_TITLE_COLOR,
            font_path=title_font_path,
            font_ttc_index=title_font_index,
        )
        ornament_y = int(layout.top_panel_height * 0.72)
        ornament_half_width = max(28, int(layout.canvas_width * 0.065))
        ornament_gap = max(10, int(layout.canvas_width * 0.008))
        centre_x = layout.canvas_width // 2
        draw.line(
            (centre_x - ornament_half_width, ornament_y, centre_x - ornament_gap, ornament_y),
            fill=_ACCENT_COLOR,
            width=max(1, layout.canvas_width // 1000),
        )
        draw.line(
            (centre_x + ornament_gap, ornament_y, centre_x + ornament_half_width, ornament_y),
            fill=_ACCENT_COLOR,
            width=max(1, layout.canvas_width // 1000),
        )
        diamond = max(3, int(layout.canvas_width * 0.004))
        draw.polygon(
            (
                (centre_x, ornament_y - diamond),
                (centre_x + diamond, ornament_y),
                (centre_x, ornament_y + diamond),
                (centre_x - diamond, ornament_y),
            ),
            fill=_ACCENT_COLOR,
        )
    if subtitle:
        rule_half_width = int(layout.canvas_width * 0.28)
        bottom_centre_x = layout.canvas_width // 2
        for rule_y in (
            bottom_y + int(layout.bottom_panel_height * 0.25),
            bottom_y + int(layout.bottom_panel_height * 0.73),
        ):
            draw.line(
                (bottom_centre_x - rule_half_width, rule_y, bottom_centre_x + rule_half_width, rule_y),
                fill=_SEPARATOR_COLOR,
                width=max(1, layout.canvas_width // 1200),
            )
        _draw_fitted_tracking_text(
            draw,
            subtitle,
            centre=(
                layout.canvas_width // 2,
                bottom_y + int(layout.bottom_panel_height * 0.49),
            ),
            max_width=max_text_width,
            max_height=max(1, int(layout.bottom_panel_height * 0.30)),
            preferred_size=max(16, int(layout.canvas_width * 0.047)),
            tracking_ratio=0.12,
            fill=_SUBTITLE_COLOR,
            font_path=subtitle_font_path,
            font_ttc_index=subtitle_font_index,
        )
    image.save(output_path, format="PNG", optimize=True)


def _draw_fitted_tracking_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    centre: tuple[int, int],
    max_width: int,
    max_height: int,
    preferred_size: int,
    tracking_ratio: float,
    fill: tuple[int, int, int],
    font_path: Path | None,
    font_ttc_index: int,
) -> None:
    minimum_size = max(12, preferred_size // 2)
    selected_font = _load_font(font_path, preferred_size, font_ttc_index)
    selected_tracking = max(0, int(preferred_size * tracking_ratio))
    selected_width = 0.0
    selected_bounds = (0, 0, 0, 0)
    for size in range(preferred_size, minimum_size - 1, -2):
        font = _load_font(font_path, size, font_ttc_index)
        tracking = max(0, int(size * tracking_ratio))
        advances = [float(draw.textlength(character, font=font)) for character in text]
        width = sum(advances) + tracking * max(0, len(text) - 1)
        bounds = draw.textbbox((0, 0), text, font=font, stroke_width=1)
        height = bounds[3] - bounds[1]
        selected_font = font
        selected_tracking = tracking
        selected_width = width
        selected_bounds = bounds
        if width <= max_width and height <= max_height:
            break

    x = centre[0] - selected_width / 2
    y = centre[1] - (selected_bounds[3] - selected_bounds[1]) / 2 - selected_bounds[1]
    for character in text:
        draw.text(
            (round(x), round(y)),
            character,
            font=selected_font,
            fill=fill,
            stroke_width=1,
            stroke_fill=(0, 0, 0),
        )
        x += float(draw.textlength(character, font=selected_font)) + selected_tracking


def _resolve_editorial_font(
    candidates: Sequence[tuple[Path, int]],
    fallback_path: Path | None,
    fallback_index: int,
) -> tuple[Path | None, int]:
    for candidate_path, candidate_index in candidates:
        if candidate_path.is_file():
            return candidate_path, candidate_index
    if fallback_path and fallback_path.is_file():
        return fallback_path, fallback_index
    return None, 0


def _load_font(font_path: Path | None, size: int, font_ttc_index: int):
    if font_path and font_path.is_file():
        return ImageFont.truetype(str(font_path), size=size, index=font_ttc_index)
    return ImageFont.load_default(size=size)


def _encoder_args(video_codec: str, quality_level: int, *, hardware: bool) -> list[str]:
    quality = max(0, min(100, int(quality_level)))
    is_hevc = str(video_codec or "h264").strip().lower() == "hevc"
    if hardware:
        args = [
            "-c:v",
            "hevc_videotoolbox" if is_hevc else "h264_videotoolbox",
            "-q:v",
            str(quality),
        ]
        if is_hevc:
            args.extend(["-tag:v", "hvc1"])
        return args
    if is_hevc:
        crf = max(0, min(32, round(32 - quality * 0.2)))
        return ["-c:v", "libx265", "-preset", "fast", "-crf", str(crf), "-tag:v", "hvc1"]
    crf = max(0, min(30, round(30 - quality * 0.2)))
    return ["-c:v", "libx264", "-preset", "fast", "-crf", str(crf)]


class _CliProgressBar:
    def __init__(
        self,
        total_seconds: float,
        *,
        label: str = "生成3:4贴片版",
        stream: TextIO | None = None,
        width: int = 28,
    ) -> None:
        self.total_seconds = max(0.001, float(total_seconds))
        self.label = label
        self.stream = stream or sys.stdout
        self.width = max(10, int(width))
        self._last_percent = -1
        self.update(0.0)

    def update(self, completed_seconds: float) -> None:
        completed = max(0.0, min(float(completed_seconds), self.total_seconds))
        ratio = completed / self.total_seconds
        percent = min(100, int(ratio * 100))
        if percent == self._last_percent:
            return
        self._last_percent = percent
        filled = min(self.width, int(round(ratio * self.width)))
        bar = "█" * filled + "·" * (self.width - filled)
        self.stream.write(
            f"\r🎞️ {self.label} [{bar}] {percent:3d}% "
            f"{_format_clock(completed)}/{_format_clock(self.total_seconds)}"
        )
        self.stream.flush()

    def finish(self) -> None:
        self.update(self.total_seconds)
        self.stream.write("\n")
        self.stream.flush()

    def abort(self) -> None:
        self.stream.write("\n")
        self.stream.flush()


def _run_export_command(command: list[str], total_duration: float, *, label: str) -> None:
    progress = _CliProgressBar(total_duration, label=label)
    with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as error_file:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=error_file,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert process.stdout is not None
        for raw_line in process.stdout:
            completed_seconds = _parse_progress_seconds(raw_line.strip())
            if completed_seconds is not None:
                progress.update(completed_seconds)
        return_code = process.wait()
        if return_code == 0:
            progress.finish()
            return

        progress.abort()
        error_file.seek(0)
        detail = error_file.read().strip()
        raise subprocess.CalledProcessError(
            return_code,
            command,
            stderr=detail,
        )


def _parse_progress_seconds(line: str) -> float | None:
    key, separator, value = line.partition("=")
    if not separator:
        return None
    try:
        if key in {"out_time_us", "out_time_ms"}:
            return float(value) / 1_000_000
        if key == "out_time":
            hours, minutes, seconds = value.split(":", 2)
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    except (TypeError, ValueError):
        return None
    return None


def _format_clock(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _process_error_detail(exc: subprocess.CalledProcessError) -> str:
    return (exc.stderr or exc.stdout or str(exc)).strip()


def _first_text(value: Any) -> str:
    if isinstance(value, str):
        return _clean_text(value)
    if isinstance(value, Sequence):
        for item in value:
            cleaned = _clean_text(item)
            if cleaned:
                return cleaned
    return ""


def _clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split()).strip()


__all__ = [
    "ThreeByFourLayout",
    "build_export_command",
    "calculate_layout",
    "derive_output_path",
    "export_three_by_four_video",
    "select_cover_copy",
]
