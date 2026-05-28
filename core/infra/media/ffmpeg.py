"""FFmpeg-backed media operations.

This module owns command construction and process execution so domain code can
stay focused on timeline decisions.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
from contextlib import suppress
from typing import List, Optional

from core.shared import VideoProcessingError, logger


def build_atempo_filter_chain(speed_factor: float) -> str:
    """Build an FFmpeg atempo filter chain for any positive speed factor."""
    if abs(speed_factor - 1.0) <= 1e-3:
        return ""

    factors: List[float] = []
    remaining = speed_factor

    while remaining > 2.0:
        factors.append(2.0)
        remaining /= 2.0

    while remaining < 0.5:
        factors.append(0.5)
        remaining /= 0.5

    factors.append(remaining)

    normalized = [f for f in factors if abs(f - 1.0) > 1e-6]
    if not normalized:
        return ""

    filter_parts = []
    for factor in normalized:
        factor = min(max(factor, 0.5), 2.0)
        filter_parts.append(f"atempo={factor:.6f}".rstrip("0").rstrip("."))

    return ",".join(filter_parts)


def adjust_audio_speed(audio_path: str, speed_factor: float,
                       temp_audio_paths: Optional[List[str]] = None) -> str:
    """Use FFmpeg to change audio speed while preserving pitch."""
    if not audio_path or not os.path.exists(audio_path):
        raise VideoProcessingError(f"口播音频不存在: {audio_path}")

    if speed_factor <= 0:
        raise VideoProcessingError("口播变速系数必须大于0")

    if abs(speed_factor - 1.0) <= 1e-3:
        return audio_path

    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise VideoProcessingError("未找到FFmpeg，无法执行口播变速。请将变速系数设为1.0后重试。")

    filter_chain = build_atempo_filter_chain(speed_factor)
    if not filter_chain:
        return audio_path

    fd, temp_output = tempfile.mkstemp(suffix=".wav", prefix="narration_speed_")
    os.close(fd)

    command = [
        ffmpeg_path,
        "-y",
        "-hide_banner",
        "-loglevel", "error",
        "-i", audio_path,
        "-vn",
        "-filter:a", filter_chain,
        temp_output,
    ]

    try:
        subprocess.run(command, check=True, stdin=subprocess.DEVNULL)
        if temp_audio_paths is not None:
            temp_audio_paths.append(temp_output)
        return temp_output
    except subprocess.CalledProcessError as exc:
        with suppress(Exception):
            os.remove(temp_output)
        raise VideoProcessingError("口播变速处理失败，请将变速系数设为1.0后重试。") from exc


def normalize_loudness(
    bgm_audio_path: str,
    project_root: str,
    *,
    target_loudness: float,
    loudness_range: float,
    enabled: bool,
) -> str:
    """Normalize BGM loudness with FFmpeg loudnorm, preserving prior fallbacks."""
    if not enabled:
        return bgm_audio_path

    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        logger.warning("未找到FFmpeg，跳过BGM响度标准化")
        return bgm_audio_path

    try:
        if target_loudness > 0:
            target_loudness = -target_loudness

        print(f"🎵 开始BGM响度标准化（目标: {target_loudness} LUFS，范围: {loudness_range} LU）")

        os.makedirs(project_root, exist_ok=True)

        print("🎵 步骤1/2: 分析BGM响度参数...")
        analysis_command = [
            ffmpeg_path,
            "-hide_banner",
            "-i", bgm_audio_path,
            "-af", f"loudnorm=I={target_loudness}:TP=-2.0:LRA={loudness_range}:print_format=json",
            "-f", "null",
            "-"
        ]

        result = subprocess.run(
            analysis_command,
            capture_output=True,
            text=True,
            timeout=60,
            stdin=subprocess.DEVNULL,
        )

        stderr_output = result.stderr or ""
        json_match = re.search(r'\{[^{}]*"input_i"[^{}]*\}', stderr_output, re.DOTALL)

        if not json_match:
            logger.warning("无法解析loudnorm分析结果，使用单步标准化")
            normalized_path = os.path.join(project_root, "bgm_normalized.wav")
            normalize_command = [
                ffmpeg_path,
                "-y",
                "-hide_banner",
                "-loglevel", "error",
                "-i", bgm_audio_path,
                "-af", f"loudnorm=I={target_loudness}:TP=-2.0:LRA={loudness_range}",
                normalized_path
            ]
            subprocess.run(normalize_command, check=True, timeout=120, stdin=subprocess.DEVNULL)
            print("🎵 BGM响度标准化完成（单步模式）")
            return normalized_path

        loudness_data = json.loads(json_match.group(0))
        input_i = loudness_data.get("input_i")
        input_tp = loudness_data.get("input_tp")
        input_lra = loudness_data.get("input_lra")
        input_thresh = loudness_data.get("input_thresh")

        print(f"🎵 原始响度: {input_i} LUFS, 峰值: {input_tp} dB, 范围: {input_lra} LU")

        print("🎵 步骤2/2: 应用响度标准化...")
        normalized_path = os.path.join(project_root, "bgm_normalized.wav")

        normalize_command = [
            ffmpeg_path,
            "-y",
            "-hide_banner",
            "-loglevel", "error",
            "-i", bgm_audio_path,
            "-af", (
                f"loudnorm=I={target_loudness}:TP=-2.0:LRA={loudness_range}:"
                f"measured_I={input_i}:measured_TP={input_tp}:"
                f"measured_LRA={input_lra}:measured_thresh={input_thresh}:"
                f"linear=true:print_format=summary"
            ),
            normalized_path
        ]

        subprocess.run(normalize_command, check=True, timeout=120, stdin=subprocess.DEVNULL)

        print(f"🎵 BGM响度标准化完成！标准化文件: {os.path.basename(normalized_path)}")
        return normalized_path

    except subprocess.TimeoutExpired:
        logger.warning("BGM响度标准化超时，使用原始音频")
        return bgm_audio_path
    except subprocess.CalledProcessError as exc:
        logger.warning(f"BGM响度标准化失败: {exc}，使用原始音频")
        return bgm_audio_path
    except Exception as exc:
        logger.warning(f"BGM响度标准化异常: {exc}，使用原始音频")
        return bgm_audio_path

