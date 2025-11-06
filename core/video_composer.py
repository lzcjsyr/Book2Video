"""
视频合成器 - 统一的视频合成处理模块（迁移至 core）
整合视频合成、字幕生成、音频混合等功能
"""

import os
import re
import shutil
import subprocess
import tempfile
from contextlib import suppress
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

# MoviePy 2.x imports (no editor module)
from moviepy import (
    ImageClip,
    VideoFileClip,
    TextClip,
    ColorClip,
    CompositeVideoClip,
    CompositeAudioClip,
    concatenate_videoclips,
    AudioFileClip,
    concatenate_audioclips,
)

from config import config
from core.utils import logger, VideoProcessingError, handle_video_operation

# ==================== 系统常量 ====================
# 支持的视频格式（系统技术限制，非用户配置项）
SUPPORTED_VIDEO_FORMATS = [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".m4v"]


class VideoComposer:
    """统一的视频合成器"""
    
    def __init__(self):
        """初始化视频合成器"""
        pass
    
    def compose_video(self, image_paths: List[str], audio_paths: List[str], output_path: str,
                     script_data: Dict[str, Any] = None, enable_subtitles: bool = False,
                     bgm_audio_path: Optional[str] = None, bgm_volume: float = 0.15,
                     narration_volume: float = 1.0,
                     opening_image_path: Optional[str] = None,
                     opening_golden_quote: Optional[str] = None,
                     opening_narration_audio_path: Optional[str] = None,
                     image_size: str = "1280x720",
                     opening_quote: bool = True,
                     project_root: Optional[str] = None) -> str:
        """
        合成最终视频

        Args:
            image_paths: 图像文件路径列表
            audio_paths: 音频文件路径列表
            output_path: 输出视频路径
            script_data: 脚本数据，用于生成字幕
            enable_subtitles: 是否启用字幕
            bgm_audio_path: 背景音乐路径
            bgm_volume: 背景音乐音量
            narration_volume: 口播音量
            opening_image_path: 开场图片路径
            opening_golden_quote: 开场金句
            opening_narration_audio_path: 开场口播音频路径
            image_size: 目标图像尺寸，如"1280x720"
            opening_quote: 是否包含开场金句
            project_root: 项目根目录（用于存放响度标准化临时文件）

        Returns:
            str: 输出视频路径
        """
        video_clips: List = []
        audio_clips: List = []
        temp_audio_paths: List[str] = []
        final_video = None

        try:
            if len(image_paths) != len(audio_paths):
                raise ValueError("图像文件数量与音频文件数量不匹配")
            
            # 解析目标尺寸
            target_size = self._parse_image_size(image_size)
            print(f"目标视频尺寸: {target_size[0]}x{target_size[1]}")

            # 检测是否包含视频素材，决定输出帧率
            has_videos = self._has_video_materials(image_paths)
            target_fps = 30 if has_videos else 15
            print(f"检测到{'视频' if has_videos else '图片'}素材，使用{target_fps}fps输出")

            narration_speed_factor = float(getattr(config, "NARRATION_SPEED_FACTOR", 1.0) or 1.0)
            if narration_speed_factor <= 0:
                raise ValueError("口播变速系数必须大于0")
            if abs(narration_speed_factor - 1.0) > 1e-3:
                print(f"🎙️ 口播变速系数: {narration_speed_factor:.3f}")
                print("🎧 使用 FFmpeg atempo 保持音高进行口播变速")

            processed_opening_audio_path = None
            if opening_narration_audio_path and os.path.exists(opening_narration_audio_path):
                processed_opening_audio_path = self._ensure_speed_adjusted_audio(
                    opening_narration_audio_path,
                    narration_speed_factor,
                    temp_audio_paths
                )

            # 从script_data中提取书名
            content_title = None
            if script_data:
                content_title = script_data.get('content_title')

            # 创建开场片段
            opening_seconds = self._create_opening_segment(
                opening_image_path,
                opening_golden_quote,
                processed_opening_audio_path,
                video_clips,
                target_size,
                content_title,
                opening_quote
            )

            # 创建主要视频片段
            self._create_main_segments(
                image_paths,
                audio_paths,
                video_clips,
                audio_clips,
                target_size,
                narration_speed_factor,
                temp_audio_paths
            )
            
            # 连接所有视频片段
            print("正在合成最终视频...")
            if config.ENABLE_TRANSITIONS and config.TRANSITION_STYLE != "cut":
                # 使用过渡效果连接视频片段
                final_video = self._concatenate_with_transitions(
                    video_clips,
                    config.TRANSITION_STYLE,
                    config.TRANSITION_DURATION
                )
            else:
                # 简单拼接（无过渡效果）
                final_video = concatenate_videoclips(video_clips, method="chain")
            
            # 添加字幕
            final_video = self._add_subtitles(final_video, script_data, enable_subtitles, 
                                            audio_clips, opening_seconds)
            
            # 调整口播音量
            final_video = self._adjust_narration_volume(final_video, narration_volume)
            
            # 添加视觉效果
            final_video = self._add_visual_effects(final_video, image_paths, target_size)

            # 添加背景音乐
            final_video = self._add_background_music(final_video, bgm_audio_path, bgm_volume, project_root)
            
            # 输出视频
            self._export_video(final_video, output_path, target_fps)
            
            print(f"最终视频已保存: {output_path}")
            return output_path
            
        except Exception as e:
            raise ValueError(f"视频合成错误: {e}")
        finally:
            self._cleanup_resources(video_clips, audio_clips, final_video, temp_audio_paths)
    
    @handle_video_operation("开场片段生成", critical=False, fallback_value=0.0)
    def _create_opening_segment(self, opening_image_path: Optional[str],
                              opening_golden_quote: Optional[str],
                              opening_narration_audio_path: Optional[str],
                              video_clips: List, target_size: Tuple[int, int],
                              content_title: Optional[str] = None,
                              opening_quote: bool = True) -> float:
        """创建开场片段"""
        opening_seconds = 0.0
        opening_voice_clip = None

        # 如果不包含开场金句，直接返回
        if not opening_quote:
            return opening_seconds

        # 计算开场时长
        if opening_narration_audio_path and os.path.exists(opening_narration_audio_path):
            opening_voice_clip = AudioFileClip(opening_narration_audio_path)
            hold_after = float(getattr(config, "OPENING_HOLD_AFTER_NARRATION_SECONDS", 2.0))
            opening_seconds = float(opening_voice_clip.duration) + max(0.0, hold_after)

        if opening_image_path and os.path.exists(opening_image_path) and opening_seconds > 1e-3:
            print("正在创建开场片段…")

            # 检测并处理视频或图片格式
            if self._is_video_file(opening_image_path):
                # 视频素材处理
                print(f"  使用视频素材: {os.path.basename(opening_image_path)}")
                opening_base = VideoFileClip(opening_image_path).without_audio()
                opening_base = self._resize_video(opening_base, target_size)

                # 调整时长到音频长度
                original_duration = opening_base.duration
                print(f"  开场视频时长: {original_duration:.2f}s，目标时长: {opening_seconds:.2f}s")

                if original_duration < opening_seconds:
                    print(f"  视频较短，拉伸到 {opening_seconds:.2f}s")
                    opening_base = opening_base.with_duration(opening_seconds)
                elif original_duration > opening_seconds:
                    print(f"  视频较长，从头裁剪到 {opening_seconds:.2f}s")
                    opening_base = opening_base.subclipped(0, opening_seconds)
                else:
                    print(f"  视频时长匹配，无需调整")
            else:
                # 图片素材处理（原有逻辑）
                print(f"  使用图片素材: {os.path.basename(opening_image_path)}")
                opening_base = ImageClip(opening_image_path).with_duration(opening_seconds)
                # 调整开场图片尺寸到目标尺寸
                opening_base = self._resize_image(opening_base, target_size)
            
            # 添加开场金句
            if opening_golden_quote and opening_golden_quote.strip():
                opening_clip = self._add_opening_quote(opening_base, opening_golden_quote, opening_seconds, content_title)
            else:
                opening_clip = opening_base
            
            # 绑定开场音频
            if opening_voice_clip is not None:
                opening_clip = opening_clip.with_audio(opening_voice_clip)
            
            # 添加渐隐效果
            opening_clip = self._add_opening_fade_effect(opening_clip, opening_voice_clip, opening_seconds)
            
            video_clips.append(opening_clip)

        return opening_seconds

    def _ensure_speed_adjusted_audio(self, audio_path: str, speed_factor: float,
                                     temp_audio_paths: List[str]) -> str:
        """使用FFmpeg执行变速并保持音高，返回处理后的音频路径"""
        if not audio_path or not os.path.exists(audio_path):
            raise VideoProcessingError(f"口播音频不存在: {audio_path}")

        if speed_factor <= 0:
            raise VideoProcessingError("口播变速系数必须大于0")

        if abs(speed_factor - 1.0) <= 1e-3:
            return audio_path

        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            raise VideoProcessingError("未找到FFmpeg，无法执行口播变速。请将变速系数设为1.0后重试。")

        filter_chain = self._build_atempo_filter_chain(speed_factor)
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
            subprocess.run(command, check=True)
            temp_audio_paths.append(temp_output)
            return temp_output
        except subprocess.CalledProcessError as exc:
            with suppress(Exception):
                os.remove(temp_output)
            raise VideoProcessingError("口播变速处理失败，请将变速系数设为1.0后重试。") from exc

    def _build_atempo_filter_chain(self, speed_factor: float) -> str:
        """根据目标变速系数生成FFmpeg atempo滤镜链"""
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
            filter_parts.append(f"atempo={factor:.6f}".rstrip('0').rstrip('.'))

        return ",".join(filter_parts)

    def _create_text_image_pil(self, text: str, font_size: int, font_path: str,
                               text_color: str, stroke_color: str, stroke_width: int) -> Image.Image:
        """
        使用 PIL 渲染文字到图片，完整保留 descender（下伸笔画）

        这个方法解决了 MoviePy TextClip 裁切行楷字体底部笔画的问题

        Args:
            text: 要渲染的文字
            font_size: 字体大小
            font_path: 字体文件路径
            text_color: 文字颜色
            stroke_color: 描边颜色
            stroke_width: 描边宽度

        Returns:
            PIL.Image.Image: 带透明背景的文字图片
        """
        try:
            # 加载字体
            font = ImageFont.truetype(font_path, font_size)

            # 使用临时图片测量文字边界框
            temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
            temp_draw = ImageDraw.Draw(temp_img)

            # 获取文字边界框 (left, top, right, bottom)
            # textbbox 会包含完整的 descender
            bbox = temp_draw.textbbox((0, 0), text, font=font, anchor='lt', stroke_width=stroke_width)

            # 计算实际画布大小（包含描边空间）
            width = bbox[2] - bbox[0] + stroke_width * 2
            height = bbox[3] - bbox[1] + stroke_width * 2

            # 创建带透明背景的图片
            img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # 计算绘制位置（考虑 bbox 的偏移）
            draw_x = -bbox[0] + stroke_width
            draw_y = -bbox[1] + stroke_width

            # 转换颜色
            if text_color == 'white':
                fill = (255, 255, 255, 255)
            else:
                fill = text_color

            if stroke_color == 'black':
                stroke = (0, 0, 0, 255)
            else:
                stroke = stroke_color

            # 绘制文字
            draw.text(
                (draw_x, draw_y),
                text,
                font=font,
                fill=fill,
                stroke_width=stroke_width,
                stroke_fill=stroke,
                anchor='lt'
            )

            return img

        except Exception as e:
            logger.warning(f"PIL 文字渲染失败: {e}，将返回空图片")
            return Image.new('RGBA', (1, 1), (0, 0, 0, 0))

    def _add_opening_quote(self, opening_base, opening_golden_quote: str, opening_seconds: float, content_title: Optional[str] = None):
        """添加开场金句文字叠加（以及可选的书名标题）"""
        # 检查是否显示文字
        if not config.OPENING_QUOTE_SHOW_TEXT:
            return opening_base  # 不显示文字，直接返回原始片段

        preferred_font_path = config.OPENING_QUOTE_FONT_FAMILY or config.SUBTITLE_FONT_FAMILY
        resolved_font = self.resolve_font_path(preferred_font_path)
        base_font = int(config.SUBTITLE_FONT_SIZE)
        scale = float(config.OPENING_QUOTE_FONT_SCALE)
        font_size = int(config.OPENING_QUOTE_FONT_SIZE or base_font * scale)
        text_color = config.OPENING_QUOTE_COLOR
        stroke_color = config.OPENING_QUOTE_STROKE_COLOR
        stroke_width = int(config.OPENING_QUOTE_STROKE_WIDTH)
        pos = config.OPENING_QUOTE_POSITION
        
        # 处理文字换行
        try:
            max_chars = int(config.OPENING_QUOTE_MAX_CHARS_PER_LINE)
            max_q_lines = int(config.OPENING_QUOTE_MAX_LINES)
            candidate_lines = self.split_text_for_subtitle(opening_golden_quote, max_chars, max_q_lines)
            lines = candidate_lines[:max_q_lines] if candidate_lines else [opening_golden_quote]
        except Exception:
            lines = [opening_golden_quote]

        # 使用 PIL 渲染文字，完整保留 descender
        line_spacing = int(config.OPENING_QUOTE_LINE_SPACING)
        video_height = opening_base.h
        temp_image_paths = []  # 临时图片路径列表
        text_clips = []

        try:
            # 步骤1: 使用 PIL 渲染每行文字到临时图片
            line_heights = []
            for i, line in enumerate(lines):
                if line.strip():
                    # 用 PIL 渲染文字
                    text_img = self._create_text_image_pil(
                        text=line,
                        font_size=font_size,
                        font_path=resolved_font or preferred_font_path,
                        text_color=text_color,
                        stroke_color=stroke_color,
                        stroke_width=stroke_width
                    )

                    # 保存到临时文件
                    temp_path = tempfile.mktemp(suffix=f"_quote_line_{i}.png")
                    text_img.save(temp_path)
                    temp_image_paths.append(temp_path)
                    line_heights.append(text_img.height)
                else:
                    line_heights.append(0)
                    temp_image_paths.append(None)

            # 步骤2: 计算总高度和顶部Y坐标
            total_height = sum(line_heights) + (len(lines) - 1) * line_spacing
            top_y = max(0, (int(video_height) - int(total_height)) // 2)

            # 步骤3: 用 ImageClip 加载图片并定位
            current_y = top_y
            for i, temp_path in enumerate(temp_image_paths):
                if temp_path:
                    line_clip = ImageClip(temp_path).with_start(0).with_duration(opening_seconds).with_position(("center", current_y))
                    text_clips.append(line_clip)
                    current_y += line_heights[i] + line_spacing

            # 步骤4: 如果启用书名显示且有书名，渲染书名标题
            if config.OPENING_QUOTE_SHOW_TITLE and content_title and content_title.strip():
                # 格式化书名为 --书名--
                formatted_title = f"--{content_title}--"

                # 获取书名样式配置
                title_font_size = int(config.OPENING_QUOTE_TITLE_FONT_SIZE)
                title_color = config.OPENING_QUOTE_TITLE_COLOR
                title_stroke_color = config.OPENING_QUOTE_TITLE_STROKE_COLOR
                title_stroke_width = int(config.OPENING_QUOTE_TITLE_STROKE_WIDTH)
                title_position_y = float(config.OPENING_QUOTE_TITLE_POSITION_Y)

                # 使用 PIL 渲染书名文字
                title_img = self._create_text_image_pil(
                    text=formatted_title,
                    font_size=title_font_size,
                    font_path=resolved_font or preferred_font_path,
                    text_color=title_color,
                    stroke_color=title_stroke_color,
                    stroke_width=title_stroke_width
                )

                # 保存到临时文件
                title_temp_path = tempfile.mktemp(suffix="_quote_title.png")
                title_img.save(title_temp_path)
                temp_image_paths.append(title_temp_path)

                # 计算书名的Y坐标（基于相对位置）
                title_y = int(video_height * title_position_y - title_img.height / 2)

                # 创建书名图层
                title_clip = ImageClip(title_temp_path).with_start(0).with_duration(opening_seconds).with_position(("center", title_y))
                text_clips.append(title_clip)

            return CompositeVideoClip([opening_base] + text_clips)

        finally:
            # 清理临时图片文件
            for temp_path in temp_image_paths:
                if temp_path and os.path.exists(temp_path):
                    with suppress(Exception):
                        os.remove(temp_path)
    
    def _add_opening_fade_effect(self, opening_clip, opening_voice_clip, opening_seconds: float):
        """为开场片段添加渐隐效果（仅限开场，时长较短，对性能影响可忽略）"""
        try:
            if opening_voice_clip is not None:
                hold_after = float(getattr(config, "OPENING_HOLD_AFTER_NARRATION_SECONDS", 2.0))
                if hold_after > 1e-3:
                    voice_duration = float(opening_voice_clip.duration)
                    fade_start_time = voice_duration
                    fade_duration = hold_after

                    def _opening_fade_out(gf, t):
                        try:
                            if t < fade_start_time:
                                return gf(t)
                            elif t >= opening_seconds:
                                return 0.0 * gf(t)
                            else:
                                fade_progress = (t - fade_start_time) / fade_duration
                                alpha = max(0.0, 1.0 - fade_progress)
                                return alpha * gf(t)
                        except Exception:
                            return gf(t)

                    opening_clip = opening_clip.transform(_opening_fade_out, keep_duration=True)
        except Exception as e:
            logger.warning(f"开场片段渐隐效果添加失败: {e}")
        return opening_clip

    def _apply_fade_in(self, clip, duration: float):
        """
        对视频片段应用淡入效果

        Args:
            clip: 要处理的视频片段
            duration: 淡入时长（秒）

        Returns:
            应用淡入效果后的片段
        """
        def fade_in_transform(gf, t):
            if t < duration:
                alpha = t / duration
                return gf(t) * alpha
            return gf(t)

        return clip.transform(fade_in_transform, keep_duration=True)

    def _apply_fade_out(self, clip, duration: float):
        """
        对视频片段应用淡出效果

        Args:
            clip: 要处理的视频片段
            duration: 淡出时长（秒）

        Returns:
            应用淡出效果后的片段
        """
        clip_duration = clip.duration
        fade_start = clip_duration - duration

        def fade_out_transform(gf, t):
            if t > fade_start:
                alpha = 1.0 - ((t - fade_start) / duration)
                return gf(t) * max(0.0, alpha)
            return gf(t)

        return clip.transform(fade_out_transform, keep_duration=True)

    def _create_color_clip(self, duration: float, color: Tuple[int, int, int], size: Tuple[int, int]):
        """
        创建纯色过渡帧

        Args:
            duration: 持续时长（秒）
            color: RGB颜色值
            size: 视频尺寸 (width, height)

        Returns:
            纯色视频片段
        """
        return ColorClip(size=size, color=color, duration=duration)

    def _create_wipe_transition(self, clip1, clip2, duration: float, direction: str):
        """
        创建擦除过渡效果（类似翻书）

        Args:
            clip1: 第一个视频片段
            clip2: 第二个视频片段
            duration: 过渡时长（秒）
            direction: 擦除方向 ('left' 或 'right')

        Returns:
            带过渡效果的组合片段
        """
        import numpy as np

        # 获取片段尺寸
        width, height = clip1.size

        # 创建过渡片段
        def make_wipe_frame(t):
            # 计算过渡进度 (0 到 1)
            progress = min(1.0, t / duration)

            # 获取两个片段在当前时间的帧
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)

            # 计算擦除边界
            if direction == "left":
                # 从左向右擦除
                boundary = int(width * progress)
                result = frame1.copy()
                result[:, :boundary] = frame2[:, :boundary]
            else:  # right
                # 从右向左擦除
                boundary = int(width * (1 - progress))
                result = frame1.copy()
                result[:, boundary:] = frame2[:, boundary:]

            return result

        # 创建过渡片段
        from moviepy import VideoClip
        transition_clip = VideoClip(make_wipe_frame, duration=duration)

        # 组合：clip1主体部分 + 过渡 + clip2主体部分
        clip1_main = clip1.subclipped(0, clip1.duration - duration)
        clip2_main = clip2.subclipped(duration, clip2.duration)

        return concatenate_videoclips([clip1_main, transition_clip, clip2_main], method="chain")

    def _create_slide_transition(self, clip1, clip2, duration: float, direction: str):
        """
        创建滑动过渡效果（新片段滑入覆盖旧片段）

        Args:
            clip1: 第一个视频片段
            clip2: 第二个视频片段
            duration: 过渡时长（秒）
            direction: 滑动方向 ('left' 或 'right')

        Returns:
            带过渡效果的组合片段
        """
        import numpy as np

        # 获取片段尺寸
        width, height = clip1.size

        # 创建过渡片段
        def make_slide_frame(t):
            # 计算过渡进度 (0 到 1)
            progress = min(1.0, t / duration)

            # 获取两个片段在当前时间的帧
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)

            # 创建结果帧
            result = np.zeros_like(frame1)

            if direction == "left":
                # 从右向左滑动：新片段从右侧滑入
                offset = int(width * (1 - progress))
                # 旧片段向左移动
                if offset > 0:
                    result[:, :width - offset] = frame1[:, offset:]
                # 新片段从右侧进入
                if offset < width:
                    result[:, width - offset:] = frame2[:, :offset]
            else:  # right
                # 从左向右滑动：新片段从左侧滑入
                offset = int(width * progress)
                # 新片段从左侧进入
                if offset > 0:
                    result[:, :offset] = frame2[:, width - offset:]
                # 旧片段向右移动
                if offset < width:
                    result[:, offset:] = frame1[:, :width - offset]

            return result

        # 创建过渡片段
        from moviepy import VideoClip
        transition_clip = VideoClip(make_slide_frame, duration=duration)

        # 组合：clip1主体部分 + 过渡 + clip2主体部分
        clip1_main = clip1.subclipped(0, clip1.duration - duration)
        clip2_main = clip2.subclipped(duration, clip2.duration)

        return concatenate_videoclips([clip1_main, transition_clip, clip2_main], method="chain")

    def _create_zoom_transition(self, clip1, clip2, duration: float, zoom_type: str):
        """
        创建缩放过渡效果

        Args:
            clip1: 第一个视频片段
            clip2: 第二个视频片段
            duration: 过渡时长（秒）
            zoom_type: 缩放类型 ('in' 或 'out')

        Returns:
            带过渡效果的组合片段
        """
        import numpy as np

        # 获取片段尺寸
        width, height = clip1.size

        # 创建过渡片段
        def make_zoom_frame(t):
            # 计算过渡进度 (0 到 1)
            progress = min(1.0, t / duration)

            # 获取两个片段在当前时间的帧
            frame1 = clip1.get_frame(clip1.duration - duration + t)
            frame2 = clip2.get_frame(t)

            if zoom_type == "in":
                # Zoom In: 旧片段放大淡出，新片段淡入
                # 旧片段缩放因子 (1.0 -> 1.5)
                scale1 = 1.0 + 0.5 * progress
                # 新片段透明度 (0 -> 1)
                alpha2 = progress
            else:  # out
                # Zoom Out: 旧片段缩小淡出，新片段淡入
                # 旧片段缩放因子 (1.0 -> 0.5)
                scale1 = 1.0 - 0.5 * progress
                # 新片段透明度 (0 -> 1)
                alpha2 = progress

            # 缩放旧片段
            new_width = int(width * scale1)
            new_height = int(height * scale1)

            # 使用简单的最近邻插值进行缩放
            from PIL import Image
            img1 = Image.fromarray(frame1)
            img1_resized = img1.resize((new_width, new_height), Image.NEAREST)
            frame1_scaled = np.array(img1_resized)

            # 创建结果帧
            result = np.zeros_like(frame2, dtype=float)

            # 将缩放后的旧片段居中放置
            if scale1 > 0:
                y_offset = max(0, (height - new_height) // 2)
                x_offset = max(0, (width - new_width) // 2)

                y_end = min(height, y_offset + new_height)
                x_end = min(width, x_offset + new_width)

                crop_h = y_end - y_offset
                crop_w = x_end - x_offset

                result[y_offset:y_end, x_offset:x_end] = frame1_scaled[:crop_h, :crop_w].astype(float)

            # 混合新片段（使用透明度）
            result = result * (1 - alpha2) + frame2.astype(float) * alpha2

            return result.astype(np.uint8)

        # 创建过渡片段
        from moviepy import VideoClip
        transition_clip = VideoClip(make_zoom_frame, duration=duration)

        # 组合：clip1主体部分 + 过渡 + clip2主体部分
        clip1_main = clip1.subclipped(0, clip1.duration - duration)
        clip2_main = clip2.subclipped(duration, clip2.duration)

        return concatenate_videoclips([clip1_main, transition_clip, clip2_main], method="chain")

    def _concatenate_with_transitions(self, clips: List, style: str, duration: float):
        """
        使用指定过渡效果连接视频片段

        Args:
            clips: 视频片段列表
            style: 过渡样式 (crossfade, fade_white, fade_black, wipe_left, wipe_right)
            duration: 过渡时长（秒）

        Returns:
            连接后的最终视频
        """
        if len(clips) == 0:
            raise ValueError("没有视频片段可以连接")

        if len(clips) == 1:
            return clips[0]

        # 参数验证和限制
        duration = max(0.1, min(duration, 2.0))  # 限制在0.1-2.0秒

        valid_styles = ["crossfade", "fade_white", "fade_black", "wipe_left", "wipe_right",
                       "slide_left", "slide_right", "zoom_in", "zoom_out"]
        if style not in valid_styles:
            logger.warning(f"不支持的过渡样式 '{style}'，使用默认 'crossfade'")
            style = "crossfade"

        try:
            print(f"正在应用 {style} 过渡效果 (时长: {duration}秒)...")

            if style == "crossfade":
                # 使用MoviePy内置的交叉淡化
                return concatenate_videoclips(clips, method="compose", padding=-duration)

            elif style in ["fade_white", "fade_black"]:
                # 通过颜色淡化
                color = (255, 255, 255) if style == "fade_white" else (0, 0, 0)
                composited_clips = []
                current_time = 0

                for i, clip in enumerate(clips):
                    if i > 0:
                        # 添加颜色过渡帧
                        color_clip = self._create_color_clip(duration, color, clip.size)
                        color_clip = color_clip.with_start(current_time)
                        composited_clips.append(color_clip)
                        current_time += duration

                        # 当前片段添加淡入
                        clip = self._apply_fade_in(clip, duration)

                    if i < len(clips) - 1:
                        # 当前片段添加淡出
                        clip = self._apply_fade_out(clip, duration)

                    clip = clip.with_start(current_time)
                    composited_clips.append(clip)
                    current_time += clip.duration

                return CompositeVideoClip(composited_clips)

            elif style in ["wipe_left", "wipe_right"]:
                # 擦除过渡效果
                direction = "left" if style == "wipe_left" else "right"
                result = clips[0]

                for i in range(1, len(clips)):
                    result = self._create_wipe_transition(result, clips[i], duration, direction)

                return result

            elif style in ["slide_left", "slide_right"]:
                # 滑动过渡效果
                direction = "left" if style == "slide_left" else "right"
                result = clips[0]

                for i in range(1, len(clips)):
                    result = self._create_slide_transition(result, clips[i], duration, direction)

                return result

            elif style in ["zoom_in", "zoom_out"]:
                # 缩放过渡效果
                zoom_type = "in" if style == "zoom_in" else "out"
                result = clips[0]

                for i in range(1, len(clips)):
                    result = self._create_zoom_transition(result, clips[i], duration, zoom_type)

                return result

        except Exception as e:
            logger.warning(f"过渡效果应用失败: {e}，回退到简单拼接")
            return concatenate_videoclips(clips, method="chain")

    def _create_main_segments(self, image_paths: List[str], audio_paths: List[str], 
                            video_clips: List, audio_clips: List, target_size: Tuple[int, int],
                            narration_speed_factor: float, temp_audio_paths: List[str]):
        """创建主要视频片段（支持图片和视频混合）"""
        for i, (media_path, audio_path) in enumerate(zip(image_paths, audio_paths)):
            print(f"正在处理第{i+1}段素材...")

            processed_audio_path = self._ensure_speed_adjusted_audio(
                audio_path,
                narration_speed_factor,
                temp_audio_paths
            )

            audio_clip = AudioFileClip(processed_audio_path)
            
            if self._is_video_file(media_path):
                # 视频素材处理
                video_clip = self._create_video_segment(media_path, audio_clip, target_size)
            else:
                # 图片素材处理
                image_clip = ImageClip(media_path).with_duration(audio_clip.duration)
                # 调整图片尺寸到目标尺寸
                image_clip = self._resize_image(image_clip, target_size)
                video_clip = image_clip.with_audio(audio_clip)
            
            video_clips.append(video_clip)
            audio_clips.append(audio_clip)
    
    @handle_video_operation("字幕添加", critical=False, fallback_value=lambda self, final_video, *args: final_video)
    def _add_subtitles(self, final_video, script_data: Dict[str, Any], enable_subtitles: bool, 
                      audio_clips: List, opening_seconds: float):
        """添加字幕"""
        if enable_subtitles and script_data:
            print("正在添加字幕...")
            # 从独立变量构建字幕配置字典
            subtitle_config = {
                "font_size": config.SUBTITLE_FONT_SIZE,
                "font_family": config.SUBTITLE_FONT_FAMILY,
                "color": config.SUBTITLE_COLOR,
                "stroke_color": config.SUBTITLE_STROKE_COLOR,
                "stroke_width": config.SUBTITLE_STROKE_WIDTH,
                "position": config.SUBTITLE_POSITION,
                "margin_bottom": config.SUBTITLE_MARGIN_BOTTOM,
                "max_chars_per_line": config.SUBTITLE_MAX_CHARS_PER_LINE,
                "max_lines": config.SUBTITLE_MAX_LINES,
                "line_spacing": config.SUBTITLE_LINE_SPACING,
                "background_color": config.SUBTITLE_BACKGROUND_COLOR,
                "background_opacity": config.SUBTITLE_BACKGROUND_OPACITY,
                "background_horizontal_padding": config.SUBTITLE_BACKGROUND_H_PADDING,
                "background_vertical_padding": config.SUBTITLE_BACKGROUND_V_PADDING,
                "shadow_enabled": config.SUBTITLE_SHADOW_ENABLED,
                "shadow_color": config.SUBTITLE_SHADOW_COLOR,
                "shadow_offset": config.SUBTITLE_SHADOW_OFFSET,
                "video_size": final_video.size,
                "segment_durations": [ac.duration for ac in audio_clips],
                "offset_seconds": opening_seconds,
            }
            subtitle_clips = self.create_subtitle_clips(script_data, subtitle_config)
            
            if subtitle_clips:
                final_video = CompositeVideoClip([final_video] + subtitle_clips)
                print(f"已添加 {len(subtitle_clips)} 个字幕剪辑")
            else:
                print("未生成任何字幕剪辑")
        
        return final_video
    
    def _adjust_narration_volume(self, final_video, narration_volume: float):
        """调整口播音量"""
        try:
            if final_video.audio is not None and narration_volume is not None:
                narration_audio = final_video.audio
                if isinstance(narration_volume, (int, float)) and abs(float(narration_volume) - 1.0) > 1e-9:
                    narration_audio = narration_audio.with_volume_scaled(float(narration_volume))
                    final_video = final_video.with_audio(narration_audio)
                    print(f"🔊 口播音量调整为: {float(narration_volume)}")
        except Exception as e:
            logger.warning(f"口播音量调整失败: {str(e)}，将使用原始音量")
        
        return final_video
    
    @handle_video_operation("视觉效果添加", critical=False, fallback_value=lambda self, final_video, *args: final_video)
    def _add_visual_effects(self, final_video, image_paths: List[str], target_size: Tuple[int, int]):
        """添加视觉效果（开场渐显和片尾渐隐）"""
        # 性能优化：跳过逐帧开场渐显
        
        # 性能优化：仅添加片尾静帧，不做逐帧渐隐
        tail_seconds = float(getattr(config, "ENDING_FADE_SECONDS", 2.5))
        if isinstance(image_paths, list) and len(image_paths) > 0 and tail_seconds > 1e-3:
            last_image_path = image_paths[-1]
            tail_clip = ImageClip(last_image_path).with_duration(tail_seconds)
            # 调整片尾图片尺寸到目标尺寸
            tail_clip = self._resize_image(tail_clip, target_size)
            final_video = concatenate_videoclips([final_video, tail_clip], method="chain")
            print(f"🎬 已添加片尾静帧 {tail_seconds}s")
        
        return final_video
    
    @handle_video_operation("背景音乐添加", critical=False, fallback_value=lambda self, final_video, *args: final_video)
    def _add_background_music(self, final_video, bgm_audio_path: Optional[str], bgm_volume: float, project_root: Optional[str] = None):
        """添加背景音乐"""
        if not bgm_audio_path or not os.path.exists(bgm_audio_path):
            if bgm_audio_path:
                print(f"⚠️ 背景音乐文件不存在: {bgm_audio_path}")
            else:
                print("ℹ️ 未指定背景音乐文件")
            return final_video

        print(f"🎵 开始处理背景音乐: {bgm_audio_path}")

        # 如果启用了响度标准化且提供了project_root，先进行标准化处理
        if project_root and getattr(config, "BGM_NORMALIZE_LOUDNESS", False):
            bgm_audio_path = self._normalize_bgm_loudness(bgm_audio_path, project_root)

        bgm_clip = AudioFileClip(bgm_audio_path)
        print(f"🎵 BGM加载成功，时长: {bgm_clip.duration:.2f}秒")
        
        # 调整BGM音量
        if isinstance(bgm_volume, (int, float)) and abs(float(bgm_volume) - 1.0) > 1e-9:
            bgm_clip = bgm_clip.with_volume_scaled(float(bgm_volume))
            print(f"🎵 BGM音量调整为: {float(bgm_volume)}")
        
        # 调整BGM长度
        bgm_clip = self._adjust_bgm_duration(bgm_clip, final_video.duration)
        
        if bgm_clip is not None:
            # 应用音频效果
            bgm_clip = self._apply_audio_effects(bgm_clip, final_video)
            
            # 合成音频
            if final_video.audio is not None:
                mixed_audio = CompositeAudioClip([final_video.audio, bgm_clip])
                print("🎵 BGM与口播音频合成完成")
            else:
                mixed_audio = CompositeAudioClip([bgm_clip])
                print("🎵 仅添加BGM音频（无口播音频）")
            
            final_video = final_video.with_audio(mixed_audio)
            print("🎵 背景音乐添加成功！")
        
        return final_video

    def _normalize_bgm_loudness(self, bgm_audio_path: str, project_root: str) -> str:
        """
        使用FFmpeg loudnorm滤镜标准化BGM响度

        Args:
            bgm_audio_path: 原始BGM音频文件路径
            project_root: 项目根目录（用于存放临时文件）

        Returns:
            str: 标准化后的音频文件路径（失败时返回原路径）
        """
        # 检查是否启用响度标准化
        if not getattr(config, "BGM_NORMALIZE_LOUDNESS", False):
            return bgm_audio_path

        # 检查FFmpeg是否可用
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            logger.warning("未找到FFmpeg，跳过BGM响度标准化")
            return bgm_audio_path

        try:
            # 读取配置参数（用户填写正数，自动转换为负数）
            target_loudness = float(getattr(config, "BGM_TARGET_LOUDNESS", 20.0))
            # 确保为负数（LUFS标准）
            if target_loudness > 0:
                target_loudness = -target_loudness
            loudness_range = float(getattr(config, "BGM_LOUDNESS_RANGE", 7.0))

            print(f"🎵 开始BGM响度标准化（目标: {target_loudness} LUFS，范围: {loudness_range} LU）")

            # 确保项目根目录存在
            os.makedirs(project_root, exist_ok=True)

            # 第一步：分析BGM的响度参数
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
                timeout=60
            )

            # 解析loudnorm输出的JSON数据
            import json
            import re

            # 从stderr中提取JSON数据（loudnorm输出在stderr中）
            stderr_output = result.stderr
            json_match = re.search(r'\{[^{}]*"input_i"[^{}]*\}', stderr_output, re.DOTALL)

            if not json_match:
                logger.warning("无法解析loudnorm分析结果，使用单步标准化")
                # 单步标准化（不使用测量数据）
                normalized_path = os.path.join(temp_dir, "bgm_normalized.wav")
                normalize_command = [
                    ffmpeg_path,
                    "-y",
                    "-hide_banner",
                    "-loglevel", "error",
                    "-i", bgm_audio_path,
                    "-af", f"loudnorm=I={target_loudness}:TP=-2.0:LRA={loudness_range}",
                    normalized_path
                ]
                subprocess.run(normalize_command, check=True, timeout=120)
                print(f"🎵 BGM响度标准化完成（单步模式）")
                return normalized_path

            # 解析测量数据
            loudness_data = json.loads(json_match.group(0))
            input_i = loudness_data.get("input_i")
            input_tp = loudness_data.get("input_tp")
            input_lra = loudness_data.get("input_lra")
            input_thresh = loudness_data.get("input_thresh")

            print(f"🎵 原始响度: {input_i} LUFS, 峰值: {input_tp} dB, 范围: {input_lra} LU")

            # 第二步：使用测量数据进行线性标准化
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

            subprocess.run(normalize_command, check=True, timeout=120)

            print(f"🎵 BGM响度标准化完成！标准化文件: {os.path.basename(normalized_path)}")
            return normalized_path

        except subprocess.TimeoutExpired:
            logger.warning("BGM响度标准化超时，使用原始音频")
            return bgm_audio_path
        except subprocess.CalledProcessError as e:
            logger.warning(f"BGM响度标准化失败: {e}，使用原始音频")
            return bgm_audio_path
        except Exception as e:
            logger.warning(f"BGM响度标准化异常: {e}，使用原始音频")
            return bgm_audio_path

    def _adjust_bgm_duration(self, bgm_clip, target_duration: float):
        """调整BGM时长：优先手动平铺循环，始终铺满并裁剪到目标时长"""
        try:
            print(f"🎵 视频总时长: {target_duration:.2f}秒，BGM时长: {bgm_clip.duration:.2f}秒")

            # 基本校验
            if target_duration <= 0:
                return bgm_clip
            unit_duration = float(bgm_clip.duration)
            if unit_duration <= 1e-6:
                raise RuntimeError("BGM源时长为0")

            # 若BGM长于目标，直接裁剪
            if unit_duration >= target_duration - 1e-6:
                try:
                    return bgm_clip.with_duration(target_duration)
                except Exception:
                    # 兜底：子片段裁剪
                    return bgm_clip.subclipped(0, target_duration)

            # 手动平铺：重复拼接 + 末段精确裁剪
            clips = []
            accumulated = 0.0
            # 先整段重复
            while accumulated + unit_duration <= target_duration - 1e-6:
                clips.append(bgm_clip.subclipped(0, unit_duration))
                accumulated += unit_duration
            # 末段裁剪
            remaining = max(0.0, target_duration - accumulated)
            if remaining > 1e-6:
                clips.append(bgm_clip.subclipped(0, remaining))

            looped = concatenate_audioclips(clips)
            print(f"🎵 BGM长度适配完成（manual loop），最终时长: {looped.duration:.2f}秒")
            return looped

        except Exception as e:
            print(f"⚠️ 背景音乐长度适配失败: {e}，将不添加BGM继续生成")
            logger.warning(f"背景音乐循环/裁剪失败: {e}")
            return None
    
    def _apply_audio_effects(self, bgm_clip, final_video):
        """应用音频效果（Ducking和淡出）"""
        return self._apply_ducking_effect(bgm_clip, final_video)
    
    def _apply_ducking_effect(self, bgm_clip, final_video):
        """应用自动Ducking效果"""
        strength = float(getattr(config, "AUDIO_DUCKING_STRENGTH", 0.7))
        smooth_sec = float(getattr(config, "AUDIO_DUCKING_SMOOTH_SECONDS", 0.12))
        total_dur = float(final_video.duration)
        
        # 采样频率
        env_fps = 20.0
        num_samples = max(2, int(total_dur * env_fps) + 1)
        times = np.linspace(0.0, total_dur, num_samples)
        
        # 估算口播瞬时幅度
        amp = np.zeros_like(times)
        for i, t in enumerate(times):
            try:
                frame = final_video.audio.get_frame(float(min(max(0.0, t), total_dur - 1e-6)))
                amp[i] = float(np.mean(np.abs(frame)))
            except Exception:
                amp[i] = 0.0
        
        # 平滑处理
        win = max(1, int(smooth_sec * env_fps))
        if win > 1:
            kernel = np.ones(win, dtype=float) / win
            amp = np.convolve(amp, kernel, mode="same")
        
        # 归一化
        max_amp = float(np.max(amp)) if np.max(amp) > 1e-8 else 1.0
        env = amp / max_amp
        
        # 计算ducking增益曲线
        gains = 1.0 - strength * env
        gains = np.clip(gains, 0.0, 1.0)
        
        # 构建时间变增益函数
        def ducking_gain_lookup(t_any):
            def lookup_single(ts: float) -> float:
                if ts <= 0.0:
                    return float(gains[0])
                if ts >= total_dur:
                    return float(gains[-1])
                idx = max(0, min(int(ts * env_fps), gains.shape[0] - 1))
                return float(gains[idx])
            
            if hasattr(t_any, "__len__"):
                return np.array([lookup_single(float(ts)) for ts in t_any])
            return lookup_single(float(t_any))
        
        # 应用时间变增益
        bgm_clip = bgm_clip.transform(
            lambda gf, t: (
                (ducking_gain_lookup(t)[:, None] if hasattr(t, "__len__") else ducking_gain_lookup(t))
                * gf(t)
            ),
            keep_duration=True,
        )
        print(f"🎚️ 已启用自动Ducking（strength={strength}, smooth={smooth_sec}s）")
        
        return bgm_clip
    
    def _create_linear_fade_out_gain(self, total: float, tail: float):
        """创建线性淡出增益函数"""
        cutoff = max(0.0, total - tail)
        
        def linear_fade_gain(t_any):
            def calc_single_gain(ts: float) -> float:
                if ts <= cutoff:
                    return 1.0
                if ts >= total:
                    return 0.0
                return max(0.0, 1.0 - (ts - cutoff) / tail)
            
            if hasattr(t_any, "__len__"):
                return np.array([calc_single_gain(float(ts)) for ts in t_any])
            return calc_single_gain(float(t_any))
        
        return linear_fade_gain
    
    def _export_video(self, final_video, output_path: str, fps: int = 15):
        """导出视频"""
        moviepy_logger = 'bar'
        
        try:
            # 使用ffmpeg视频滤镜实现淡入/淡出（仅视频，不处理音频，避免与stream copy冲突）
            fade_in_seconds = float(getattr(config, "OPENING_FADEIN_SECONDS", 0.0))
            tail_seconds = float(getattr(config, "ENDING_FADE_SECONDS", 0.0))
            total_duration = float(getattr(final_video, "duration", 0.0) or 0.0)
            vf_parts = []
            if fade_in_seconds > 1e-3:
                vf_parts.append(f"fade=t=in:st=0:d={fade_in_seconds}")
            if tail_seconds > 1e-3 and total_duration > 0.0:
                fade_out_start = max(0.0, total_duration - tail_seconds)
                vf_parts.append(f"fade=t=out:st={fade_out_start}:d={tail_seconds}")
            vf_filter = ",".join(vf_parts) if vf_parts else None

            # 优先尝试macOS硬件编码
            bitrate = '8M' if fps == 30 else '3M'
            audio_bitrate = '256k'  # 提升到256k以匹配48kHz WAV无损源音频
            bufsize = '12M' if fps == 30 else '6M'

            width = int(getattr(final_video, "w", 0) or 0)
            height = int(getattr(final_video, "h", 0) or 0)
            # 根据分辨率动态选择 profile/level，避免 videotoolbox 初始化失败（-12902）
            # 720p 及以下: Main@3.1；1080p: Main@4.1；1440p: High@5.1；4K: High@5.2
            if width and height:
                if width > 3840 or height > 2160:
                    profile_param = ['-profile:v', 'high']
                    level_param = ['-level', '5.2']
                elif width > 2560 or height > 1440:
                    profile_param = ['-profile:v', 'high']
                    level_param = ['-level', '5.2']
                elif width > 1920 or height > 1080:
                    profile_param = ['-profile:v', 'high']
                    level_param = ['-level', '5.1']
                elif width > 1280 or height > 720:
                    profile_param = ['-profile:v', 'main']
                    level_param = ['-level', '4.1']
                else:
                    profile_param = ['-profile:v', 'main']
                    level_param = ['-level', '3.1']
            else:
                profile_param = ['-profile:v', 'main']
                level_param = []
            print("🎞️ 使用硬件编码 (h264_videotoolbox) 导出视频…")
            final_video.write_videofile(
                output_path,
                fps=fps,
                codec='h264_videotoolbox',
                audio_codec='aac',
                audio_bitrate=audio_bitrate,
                bitrate=bitrate,
                ffmpeg_params=(
                    ['-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-maxrate', bitrate, '-bufsize', bufsize]
                    + profile_param
                    + level_param
                    + (['-vf', vf_filter] if vf_filter else [])
                ),
                logger=moviepy_logger
            )
        except Exception as e:
            print(f"⚠️ 硬件编码不可用或失败，回退到软件编码: {e}")
            # 回退到软件编码
            audio_bitrate = '256k'  # 提升到256k以匹配48kHz WAV无损源音频
            crf = '20' if fps == 30 else '25'
            preset = 'medium'
            print("🎞️ 改用软件编码 (libx264) 导出视频…")
            final_video.write_videofile(
                output_path,
                fps=fps,
                codec='libx264',
                audio_codec='aac',
                audio_bitrate=audio_bitrate,
                preset=preset,
                threads=os.cpu_count() or 4,
                ffmpeg_params=(
                    ['-crf', crf, '-pix_fmt', 'yuv420p', '-movflags', '+faststart']
                    + (['-vf', vf_filter] if vf_filter else [])
                ),
                logger=moviepy_logger
            )
    
    def _cleanup_resources(self, video_clips: List, audio_clips: List,
                           final_video, temp_audio_paths: Optional[List[str]] = None):
        """释放资源并清理由变速生成的临时文件"""
        for clip in video_clips:
            with suppress(Exception):
                clip.close()
        for aclip in audio_clips:
            with suppress(Exception):
                aclip.close()
        if final_video is not None:
            with suppress(Exception):
                final_video.close()
        if temp_audio_paths:
            for temp_path in temp_audio_paths:
                if temp_path and os.path.exists(temp_path):
                    with suppress(Exception):
                        os.remove(temp_path)
    
    def create_subtitle_clips(self, script_data: Dict[str, Any],
                            subtitle_config: Dict[str, Any] = None) -> List:
        """创建字幕剪辑列表"""
        if subtitle_config is None:
            # 从独立变量构建默认字幕配置
            subtitle_config = {
                "font_size": config.SUBTITLE_FONT_SIZE,
                "font_family": config.SUBTITLE_FONT_FAMILY,
                "color": config.SUBTITLE_COLOR,
                "stroke_color": config.SUBTITLE_STROKE_COLOR,
                "stroke_width": config.SUBTITLE_STROKE_WIDTH,
                "position": config.SUBTITLE_POSITION,
                "margin_bottom": config.SUBTITLE_MARGIN_BOTTOM,
                "max_chars_per_line": config.SUBTITLE_MAX_CHARS_PER_LINE,
                "max_lines": config.SUBTITLE_MAX_LINES,
                "line_spacing": config.SUBTITLE_LINE_SPACING,
                "background_color": config.SUBTITLE_BACKGROUND_COLOR,
                "background_opacity": config.SUBTITLE_BACKGROUND_OPACITY,
                "background_horizontal_padding": config.SUBTITLE_BACKGROUND_H_PADDING,
                "background_vertical_padding": config.SUBTITLE_BACKGROUND_V_PADDING,
                "shadow_enabled": config.SUBTITLE_SHADOW_ENABLED,
                "shadow_color": config.SUBTITLE_SHADOW_COLOR,
                "shadow_offset": config.SUBTITLE_SHADOW_OFFSET,
            }
        
        subtitle_clips = []
        current_time = float(subtitle_config.get("offset_seconds", 0.0))
        
        logger.info("开始创建字幕剪辑...")
        
        # 解析字体
        resolved_font = self.resolve_font_path(subtitle_config.get("font_family"))
        if not resolved_font:
            logger.warning("未能解析到可用中文字体")
        
        # 读取视频尺寸
        video_size = subtitle_config["video_size"]
        video_width, video_height = video_size
        
        segment_durations = subtitle_config.get("segment_durations", [])
        
        # 标点替换模式
        punctuation_pattern = r"[.,!?;:，。！？；：…、—]+"
        
        for i, segment in enumerate(script_data["segments"], 1):
            content = segment["content"]
            
            # 获取时长 - 优先使用实际音频时长
            duration = float(segment.get("estimated_duration", 0))
            if isinstance(segment_durations, list) and len(segment_durations) >= i:
                duration = float(segment_durations[i-1])  # 实际音频时长覆盖估算值
            
            logger.debug(f"处理第{i}段字幕，时长: {duration}秒")
            
            # 分割文本
            subtitle_texts = self.split_text_for_subtitle(
                content,
                subtitle_config["max_chars_per_line"],
                subtitle_config["max_lines"]
            )
            
            # 计算每行字幕时长
            subtitle_start_time = current_time
            line_durations = self._calculate_subtitle_durations(subtitle_texts, duration)
            
            for subtitle_text, subtitle_duration in zip(subtitle_texts, line_durations):
                try:
                    # 处理标点
                    display_text = re.sub(punctuation_pattern, "  ", subtitle_text)
                    display_text = re.sub(r" {3,}", "  ", display_text).rstrip()
                    
                    # 创建字幕剪辑
                    clips_to_add = self._create_subtitle_clips_internal(
                        display_text, subtitle_start_time, subtitle_duration,
                        subtitle_config, resolved_font, video_width, video_height
                    )
                    subtitle_clips.extend(clips_to_add)
                    
                    logger.debug(f"创建字幕: '{subtitle_text[:20]}...' 时间: {subtitle_start_time:.1f}-{subtitle_start_time+subtitle_duration:.1f}s")
                    subtitle_start_time += subtitle_duration
                    
                except Exception as e:
                    logger.warning(f"创建字幕失败: {str(e)}，跳过此字幕")
                    continue
            
            current_time += duration
        
        logger.info(f"字幕创建完成，共创建 {len(subtitle_clips)} 个字幕剪辑")
        return subtitle_clips
    
    def _calculate_mixed_length(self, text: str) -> float:
        """计算混合中英文本的等效长度"""
        import re
        import unicodedata
        # 中文按字计数（CJK统一表意文字）
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        # 英文按词计数（允许 don't / co-op 等带撇号或连字符）
        english_words = len(re.findall(r"[A-Za-z]+(?:['-][A-Za-z]+)*", text))
        # 数字按位计数
        numbers = len(re.findall(r'\d', text))
        # 其他外文字符（非ASCII字母、非CJK）作为字母按1计数
        ascii_alpha = re.compile(r"[A-Za-z]")
        cjk_pattern = re.compile(r"[\u4e00-\u9fff]")
        other_letters = 0
        for ch in text:
            if cjk_pattern.match(ch):
                continue
            if ascii_alpha.match(ch):
                continue
            if unicodedata.category(ch).startswith('L'):
                other_letters += 1
        # 标点不计入
        return chinese_chars * 1.0 + english_words * 1.5 + numbers * 1.0 + other_letters * 1.0
    
    def _calculate_subtitle_durations(self, subtitle_texts: List[str], total_duration: float) -> List[float]:
        """计算每行字幕的显示时长"""
        if len(subtitle_texts) == 0:
            return [total_duration]
        
        lengths = [max(1.0, self._calculate_mixed_length(t)) for t in subtitle_texts]
        total_len = sum(lengths)
        line_durations = []
        acc = 0.0
        
        for idx, L in enumerate(lengths):
            if idx < len(lengths) - 1:
                d = total_duration * (L / total_len)
                line_durations.append(d)
                acc += d
            else:
                line_durations.append(max(0.0, total_duration - acc))
        
        return line_durations
    
    def _create_subtitle_clips_internal(self, display_text: str, start_time: float, duration: float,
                                       subtitle_config: Dict, resolved_font: Optional[str], 
                                       video_width: int, video_height: int) -> List:
        """内部字幕剪辑创建函数"""
        clips_to_add = []
        position = subtitle_config["position"]
        margin_bottom = int(subtitle_config.get("margin_bottom", 0))
        anchor_x = position[0] if isinstance(position, tuple) else "center"
        
        # 创建主要文字剪辑
        main_clip = TextClip(
            text=display_text,
            font_size=subtitle_config["font_size"],
            color=subtitle_config["color"],
            font=resolved_font or subtitle_config["font_family"],
            stroke_color=subtitle_config["stroke_color"],
            stroke_width=subtitle_config["stroke_width"]
        )
        
        # 添加背景条（需要先计算，确定文字位置）
        bg_color = subtitle_config.get("background_color")
        bg_opacity = float(subtitle_config.get("background_opacity", 0))
        if bg_color and bg_opacity > 0.0:
            bg_height = int(
                subtitle_config["font_size"] * subtitle_config.get("max_lines", 2)
                + subtitle_config.get("line_spacing", 10) 
                + subtitle_config.get("background_vertical_padding", 10)
            )
            text_width = main_clip.w
            bg_padding = int(subtitle_config.get("background_horizontal_padding", 20))
            # 限制背景宽度不超过视频宽度的90%
            max_bg_width = int(video_width * 0.9)
            bg_width = min(text_width + bg_padding, max_bg_width)
            
            # 背景位置
            y_bg = max(0, video_height - margin_bottom - bg_height)
            bg_clip = ColorClip(size=(bg_width, bg_height), color=bg_color)
            if hasattr(bg_clip, "with_opacity"):
                bg_clip = bg_clip.with_opacity(bg_opacity)
            # 先设定时间，再设定位置，避免时间轴属性被覆盖
            bg_clip = bg_clip.with_start(start_time).with_duration(duration).with_position(("center", y_bg))
            
            # 文字在背景中垂直居中
            y_text_centered = y_bg + (bg_height - main_clip.h) // 2
            main_pos = (anchor_x, y_text_centered)
            clips_to_add.append(bg_clip)
        else:
            # 无背景时使用原来的位置计算
            if isinstance(position, tuple) and len(position) == 2 and position[1] == "bottom":
                baseline_safe_padding = int(subtitle_config.get("baseline_safe_padding", 4))
                y_text = max(0, video_height - margin_bottom - main_clip.h - baseline_safe_padding)
                main_pos = (anchor_x, y_text)
            else:
                main_pos = position
        
        # 先设定时间，再设定位置，避免时间轴属性被覆盖
        main_clip = main_clip.with_start(start_time).with_duration(duration).with_position(main_pos)
        
        # 添加阴影
        if subtitle_config.get("shadow_enabled", False):
            shadow_color = subtitle_config.get("shadow_color", "black")
            shadow_offset = subtitle_config.get("shadow_offset", (2, 2))
            shadow_x = main_pos[0] if isinstance(main_pos[0], int) else 0
            shadow_y = main_pos[1] if isinstance(main_pos[1], int) else 0
            
            try:
                shadow_pos = (shadow_x + shadow_offset[0], shadow_y + shadow_offset[1])
            except:
                shadow_pos = main_pos
            
            shadow_clip = TextClip(
                text=display_text,
                font_size=subtitle_config["font_size"],
                color=shadow_color,
                font=resolved_font or subtitle_config["font_family"]
            ).with_start(start_time).with_duration(duration).with_position(shadow_pos)
            
            clips_to_add.extend([shadow_clip, main_clip])
        else:
            clips_to_add.append(main_clip)
        
        return clips_to_add
    
    def split_text_for_subtitle(self, text: str, max_chars_per_line: int = 20, max_lines: int = 2) -> List[str]:
        """将长文本分割为适合字幕显示的短句"""
        if len(text) <= max_chars_per_line:
            return [text]
        
        # 第一层：按主要标点切分
        heavy_punctuation = ['。', '！', '？', '.', '!', '?', '，', ',', '；', ';', ":", "：", "——", " "]
        segments = []
        current_segment = ""
        
        for char in text:
            current_segment += char
            if char in heavy_punctuation:
                segments.append(current_segment.strip())
                current_segment = ""
        
        if current_segment.strip():
            segments.append(current_segment.strip())
        
        # 第二层：处理超长片段
        final_parts = []
        for segment in segments:
            if len(segment) <= max_chars_per_line:
                final_parts.append(segment)
            else:
                # 按逗号进一步切分
                comma_parts = []
                light_punctuation = ['、', ';', '；']
                current_part = ""
                
                for char in segment:
                    current_part += char
                    if char in light_punctuation and len(current_part) >= max_chars_per_line * 0.6:
                        comma_parts.append(current_part.strip())
                        current_part = ""
                
                if current_part.strip():
                    comma_parts.append(current_part.strip())
                
                # 第三层：硬切分
                for part in comma_parts:
                    if len(part) <= max_chars_per_line:
                        final_parts.append(part)
                    else:
                        final_parts.extend(self._split_text_evenly(part, max_chars_per_line))
        
        # 返回完整的行序列（显示层面仍按 max_lines 控制"同时显示"的行数）
        return final_parts
    
    def _split_text_evenly(self, text: str, max_chars_per_line: int) -> List[str]:
        """将文本均匀切分"""
        if len(text) <= max_chars_per_line:
            return [text]
        
        total_chars = len(text)
        num_segments = (total_chars + max_chars_per_line - 1) // max_chars_per_line
        
        base_length = total_chars // num_segments
        remainder = total_chars % num_segments
        
        result = []
        start = 0
        
        for i in range(num_segments):
            length = base_length + (1 if i < remainder else 0)
            end = start + length
            result.append(text[start:end])
            start = end
        
        return result
    
    def resolve_font_path(self, preferred: Optional[str]) -> Optional[str]:
        """解析字体路径"""
        if preferred and os.path.exists(preferred):
            return preferred
        
        # 常见中文字体路径
        common_fonts = [
            "/System/Library/Fonts/STHeiti Light.ttc",  # macOS
            "/System/Library/Fonts/PingFang.ttc",       # macOS
            "/Windows/Fonts/simhei.ttf",                # Windows
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # Linux
        ]
        
        for font_path in common_fonts:
            if os.path.exists(font_path):
                return font_path
        
        return None
    
    def _is_video_file(self, file_path: str) -> bool:
        """检测是否为视频文件"""
        file_extension = os.path.splitext(file_path)[1].lower()
        return file_extension in SUPPORTED_VIDEO_FORMATS
    
    def _has_video_materials(self, media_paths: List[str]) -> bool:
        """检测是否包含视频素材"""
        return any(self._is_video_file(path) for path in media_paths)
    
    def _create_video_segment(self, video_path: str, audio_clip, target_size: Tuple[int, int]) -> Any:
        """创建视频片段"""
        print(f"处理视频素材: {os.path.basename(video_path)}")
        
        # 加载视频文件
        video_clip = VideoFileClip(video_path)
        original_duration = video_clip.duration
        target_duration = audio_clip.duration
        
        print(f"  原视频时长: {original_duration:.2f}s，目标时长: {target_duration:.2f}s")
        
        # 移除原音频，调整尺寸
        video_clip = video_clip.without_audio()
        video_clip = self._resize_video(video_clip, target_size)
        
        if original_duration < target_duration:
            # 视频比音频短：拉伸到目标长度（保持现有逻辑）
            speed_factor = original_duration / target_duration
            print(f"  视频较短，拉伸系数: {speed_factor:.3f}")
            video_clip = video_clip.with_duration(target_duration)
        elif original_duration > target_duration:
            # 视频比音频长：从头开始裁剪到目标长度
            print(f"  视频较长，从头裁剪到 {target_duration:.2f}s")
            video_clip = video_clip.subclipped(0, target_duration)
        else:
            # 时长相等或极其接近，无需处理
            print(f"  视频时长与音频匹配，无需调整")
        
        return video_clip.with_audio(audio_clip)
    
    def _resize_video(self, video_clip, target_size: Tuple[int, int]) -> Any:
        """调整视频尺寸到指定尺寸"""
        target_w, target_h = target_size
        original_w, original_h = video_clip.size
        
        # 按比例缩放并裁剪
        scale_w = target_w / original_w
        scale_h = target_h / original_h
        
        if scale_w > scale_h:
            video_clip = video_clip.resized(width=target_w)
            if video_clip.h > target_h:
                y_start = (video_clip.h - target_h) // 2
                video_clip = video_clip.cropped(y1=y_start, y2=y_start + target_h)
        else:
            video_clip = video_clip.resized(height=target_h)
            if video_clip.w > target_w:
                x_start = (video_clip.w - target_w) // 2
                video_clip = video_clip.cropped(x1=x_start, x2=x_start + target_w)
        
        return video_clip
    
    def _parse_image_size(self, image_size: str) -> Tuple[int, int]:
        """解析图像尺寸字符串，如 "1024x1024" -> (1024, 1024)"""
        try:
            width_str, height_str = image_size.lower().split('x')
            width = int(width_str.strip())
            height = int(height_str.strip())
            return (width, height)
        except (ValueError, AttributeError) as e:
            logger.warning(f"无法解析图像尺寸 '{image_size}'，使用默认1280x720: {e}")
            return (1280, 720)
    
    def _resize_image(self, image_clip, target_size: Tuple[int, int]) -> Any:
        """调整图片尺寸到指定尺寸"""
        target_w, target_h = target_size
        original_w, original_h = image_clip.size
        
        # 如果原图尺寸已经匹配，直接返回
        if original_w == target_w and original_h == target_h:
            return image_clip
        
        # 按比例缩放并裁剪（与视频处理逻辑一致）
        scale_w = target_w / original_w
        scale_h = target_h / original_h
        
        if scale_w > scale_h:
            image_clip = image_clip.resized(width=target_w)
            if image_clip.h > target_h:
                y_start = (image_clip.h - target_h) // 2
                image_clip = image_clip.cropped(y1=y_start, y2=y_start + target_h)
        else:
            image_clip = image_clip.resized(height=target_h)
            if image_clip.w > target_w:
                x_start = (image_clip.w - target_w) // 2
                image_clip = image_clip.cropped(x1=x_start, x2=x_start + target_w)
        
        return image_clip
    
