"""
视频生成流程管理模块
实现完整的端到端视频制作流程，协调所有核心模块

主要功能:
- 全自动模式（run_auto）：一键完成从文档到视频的全流程
- 分步模式（run_step_1 到 run_step_6）：支持逐步执行和断点续制
- 调用 core.text 模块进行文本处理（总结、切分、关键词提取）
- 调用 core.media 模块进行多媒体生成（图像、语音）
- 调用 core.video_composer 进行视频合成
- 调用 core.document_processor 导出可编辑文档
"""

import os
import json
import datetime
from typing import Dict, Any, List, Optional
import warnings

from config import config, Config
from core.utils import load_json_file, logger
from core.document_processor import export_raw_to_docx
from core.document_reader import DocumentReader
from core.text import (
    intelligent_summarize,
    extract_keywords,
    generate_description_summary,
    process_raw_to_script,
    export_plain_text_segments,
)
from core.media import (
    generate_opening_image,
    generate_images_for_segments,
    generate_cover_images,
    synthesize_voice_for_segments,
)
from core.video_composer import VideoComposer
from core.services import text_to_audio_bytedance
from core.validators import auto_detect_server_from_model
from core.project_paths import ProjectPaths
from core.generation_config import VideoGenerationConfig, StepExecutionConfig


def _initialize_project(raw_data: Dict[str, Any], output_dir: str) -> tuple:
    """Create project folder structure and persist raw outputs."""
    current_time = datetime.datetime.now()
    time_suffix = current_time.strftime("%m%d_%H%M")
    raw_title = raw_data.get('title', 'untitled') or 'untitled'
    project_folder = f"{raw_title}_{time_suffix}"
    project_output_dir = os.path.join(output_dir, project_folder)

    # 使用 ProjectPaths 管理路径
    paths = ProjectPaths(project_output_dir)
    paths.ensure_dirs_exist()

    # 保存 raw.json
    with open(paths.raw_json(), 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)

    # 导出 raw.docx
    raw_docx_path = None
    try:
        export_raw_to_docx(raw_data, paths.raw_docx())
        raw_docx_path = paths.raw_docx()
    except Exception:
        pass

    return project_output_dir, paths.raw_json(), raw_docx_path


def _resolve_bgm_audio_path(bgm_filename: Optional[str], project_root: str) -> Optional[str]:
    """Locate BGM asset either via absolute path or music directory."""
    if not bgm_filename:
        return None
    if os.path.isabs(bgm_filename) and os.path.exists(bgm_filename):
        return bgm_filename
    candidate = os.path.join(project_root, "music", bgm_filename)
    if os.path.exists(candidate):
        return candidate
    return None


def _ensure_opening_narration(
    script_data: Optional[Dict[str, Any]],
    voice_dir: str,
    voice: str,
    opening_quote: bool,
    announce: bool = False,
    force_regenerate: bool = False,
    speech_rate: int = 0,
    loudness_rate: int = 0,
    emotion: str = "neutral",
    emotion_scale: int = 4,
    mute_cut_threshold: int = 400,
    mute_cut_min_silence_ms: int = 200,
    mute_cut_remain_ms: int = 100,
) -> Optional[str]:
    """Generate or reuse opening narration audio when required."""
    opening_golden_quote = (script_data or {}).get("golden_quote", "")
    if not (opening_quote and isinstance(opening_golden_quote, str) and opening_golden_quote.strip()):
        return None

    try:
        os.makedirs(voice_dir, exist_ok=True)
        opening_path = os.path.join(voice_dir, "opening.mp3")
        if force_regenerate and os.path.exists(opening_path):
            try:
                os.remove(opening_path)
            except Exception:
                if announce:
                    print("⚠️ 开场音频删除失败，尝试直接覆盖")

        if os.path.exists(opening_path):
            if announce:
                print(f"✅ 开场音频已存在: {opening_path}")
            return opening_path

        ok = text_to_audio_bytedance(
            opening_golden_quote,
            opening_path,
            voice=voice,
            encoding="mp3",
            speech_rate=speech_rate,
            loudness_rate=loudness_rate,
            emotion=emotion,
            emotion_scale=emotion_scale,
            mute_cut_threshold=mute_cut_threshold,
            mute_cut_min_silence_ms=mute_cut_min_silence_ms,
            mute_cut_remain_ms=mute_cut_remain_ms,
        )
        if ok:
            if announce:
                print(f"✅ 开场音频已生成: {opening_path}")
            return opening_path
        if announce:
            print("❌ 开场音频生成失败")
    except Exception:
        if announce:
            print("❌ 开场音频生成失败")
    return None


def _invoke_opening_narration(
    script_data: Optional[Dict[str, Any]],
    voice_dir: str,
    voice: str,
    opening_quote: bool,
    *,
    announce: bool = False,
    force_regenerate: bool = False,
    speech_rate: int = 0,
    loudness_rate: int = 0,
    emotion: str = "neutral",
    emotion_scale: int = 4,
    mute_cut_threshold: int = 400,
    mute_cut_min_silence_ms: int = 200,
    mute_cut_remain_ms: int = 100,
) -> Optional[str]:
    """Call _ensure_opening_narration with graceful fallback for legacy mocks."""
    func = _ensure_opening_narration
    try:
        return func(
            script_data,
            voice_dir,
            voice,
            opening_quote,
            announce=announce,
            force_regenerate=force_regenerate,
            speech_rate=speech_rate,
            loudness_rate=loudness_rate,
            emotion=emotion,
            emotion_scale=emotion_scale,
            mute_cut_threshold=mute_cut_threshold,
            mute_cut_min_silence_ms=mute_cut_min_silence_ms,
            mute_cut_remain_ms=mute_cut_remain_ms,
        )
    except TypeError as exc:
        message = str(exc)
        if "unexpected keyword argument" in message and (
            "speech_rate" in message or "loudness_rate" in message
        ):
            return func(
                script_data,
                voice_dir,
                voice,
                opening_quote,
                announce=announce,
                force_regenerate=force_regenerate,
            )
        raise


def _resolve_description_source_text(
    project_output_dir: str,
    raw_data: Optional[Dict[str, Any]] = None,
    script_data: Optional[Dict[str, Any]] = None,
) -> str:
    """Prefer raw.docx edits when building description-mode summary input."""
    docx_path = os.path.join(project_output_dir, 'text', 'raw.docx')
    if os.path.exists(docx_path):
        try:
            from core.document_processor import parse_raw_from_docx

            parsed = parse_raw_from_docx(docx_path)
            content = (parsed.get('content') or '').strip()
            if content:
                return content
        except Exception as exc:
            logger.warning(f"解析raw.docx失败，改用备用内容: {exc}")

    if raw_data:
        content = (raw_data.get('content') or '').strip()
        if content:
            return content

    if script_data:
        segments = script_data.get('segments') or []
        merged = "\n".join(seg.get('content', '') for seg in segments).strip()
        if merged:
            return merged

    return ""


def run_auto(config: VideoGenerationConfig) -> Dict[str, Any]:
    """
    全自动视频生成流程
    
    Args:
        config: 视频生成配置对象
        
    Returns:
        Dict[str, Any]: 处理结果
    """
    start_time = datetime.datetime.now()
    project_root = os.path.dirname(os.path.dirname(__file__))

    # 1) 读取文档
    reader = DocumentReader()
    document_content, original_length = reader.read(config.input_file)

    # 2) 智能缩写（原始数据）- 使用步骤1的LLM配置
    raw_data = intelligent_summarize(
        config.llm_server_step1,
        config.llm_model_step1,
        document_content,
        config.target_length,
        config.num_segments
    )

    # 3) 创建输出目录结构
    project_output_dir, _, _ = _initialize_project(raw_data, config.output_dir)
    paths = ProjectPaths(project_output_dir)

    # 4) 步骤1.5：段落切分
    step15 = run_step_1_5(project_output_dir, config.num_segments, is_new_project=True, raw_data=raw_data, auto_mode=True)
    if not step15.get("success"):
        return {"success": False, "message": step15.get("message", "步骤1.5处理失败")}
    script_data = step15.get("script_data")
    script_path = step15.get("script_path")

    # 5) 生成第二阶段产物（关键词或描述）
    keywords_data: Optional[Dict[str, Any]] = None
    keywords_path: Optional[str] = None
    description_data: Optional[Dict[str, Any]] = None
    description_path: Optional[str] = None

    if config.images_method == 'description':
        description_source = _resolve_description_source_text(
            project_output_dir, raw_data=raw_data
        )
        description_data = generate_description_summary(
            config.llm_server_step2, config.llm_model_step2, description_source, max_chars=200
        )
        description_path = paths.mini_summary_json()
        with open(description_path, 'w', encoding='utf-8') as f:
            json.dump(description_data, f, ensure_ascii=False, indent=2)
    else:
        keywords_data = extract_keywords(config.llm_server_step2, config.llm_model_step2, script_data)
        keywords_path = paths.keywords_json()
        with open(keywords_path, 'w', encoding='utf-8') as f:
            json.dump(keywords_data, f, ensure_ascii=False, indent=2)

    # 6) 生成开场图像（可选）& 段落图像
    opening_image_path = generate_opening_image(
        config.image_server, config.image_model,
        config.opening_image_style, config.image_size,
        paths.images, config.opening_quote
    )
    image_result = generate_images_for_segments(
        config.image_server, config.image_model, script_data,
        config.image_style_preset, config.image_size, paths.images,
        images_method=config.images_method,
        keywords_data=keywords_data,
        description_data=description_data,
        llm_model=config.llm_model_step2,
        llm_server=config.llm_server_step2,
    )
    image_paths: List[str] = image_result.get('image_paths', [])
    failed_image_segments: List[int] = image_result.get('failed_segments', [])

    if failed_image_segments:
        failed_str = '、'.join(str(idx) for idx in failed_image_segments)
        return {
            'success': False,
            'message': f"第 {failed_str} 段图像生成失败，请调整提示或稍后重试。",
            'failed_image_segments': failed_image_segments,
            'needs_retry': True,
            'stage': 3,
            'image_paths': image_paths,
        }

    # 7) 语音合成（含SRT导出）
    voice_result = synthesize_voice_for_segments(
        config.tts_server,
        config.voice,
        script_data,
        paths.voice,
        speech_rate=config.speech_rate,
        loudness_rate=config.loudness_rate,
        emotion=config.emotion,
        emotion_scale=config.emotion_scale,
        mute_cut_remain_ms=config.mute_cut_remain_ms,
        mute_cut_threshold=config.mute_cut_threshold,
    )
    audio_paths = voice_result.get("audio_paths", [])

    # 8) BGM路径解析
    bgm_audio_path = _resolve_bgm_audio_path(config.bgm_filename, project_root)

    # 9) 开场金句口播（可选）
    opening_golden_quote = (script_data or {}).get("golden_quote", "")
    opening_narration_audio_path = _invoke_opening_narration(
        script_data,
        paths.voice,
        config.voice,
        config.opening_quote,
        speech_rate=config.speech_rate,
        loudness_rate=config.loudness_rate,
        emotion=config.emotion,
        emotion_scale=config.emotion_scale,
        mute_cut_remain_ms=config.mute_cut_remain_ms,
        mute_cut_threshold=config.mute_cut_threshold,
    )

    # 10) 视频合成
    composer = VideoComposer()
    final_video_path = composer.compose_video(
        image_paths, audio_paths, paths.final_video(),
        script_data=script_data, enable_subtitles=config.enable_subtitles,
        bgm_audio_path=bgm_audio_path,
        opening_image_path=opening_image_path,
        opening_golden_quote=opening_golden_quote,
        opening_narration_audio_path=opening_narration_audio_path,
        bgm_volume=float(getattr(config, "BGM_DEFAULT_VOLUME", 0.2)),
        narration_volume=float(getattr(config, "NARRATION_DEFAULT_VOLUME", 1.0)),
        image_size=config.get_effective_video_size(),
        opening_quote=config.opening_quote,
        project_root=project_output_dir,
    )

    # 11) 封面图像生成
    cover_result = None
    try:
        cover_result = _run_cover_generation(
            project_output_dir,
            config.get_effective_cover_size(),
            config.get_effective_cover_model(),
            config.cover_image_style,
            max(1, int(config.cover_image_count)),
            script_data,
            raw_data,
        )
    except Exception as e:
        logger.warning(f"封面生成失败: {e}")

    # 12) 汇总结果
    end_time = datetime.datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    compression_ratio = (1 - (script_data['total_length'] / original_length)) * 100 if original_length > 0 else 0.0

    result: Dict[str, Any] = {
        'success': True,
        'message': '视频制作完成',
        'execution_time': execution_time,
        'script': {
            'file_path': script_path,
            'total_length': script_data['total_length'],
            'segments_count': script_data['actual_segments'],
        },
        'images_method': config.images_method,
        'images': image_paths,
        'audio_files': audio_paths,
        'final_video': final_video_path,
        'cover_images': (cover_result or {}).get('cover_paths', []),
        'statistics': {
            'original_length': original_length,
            'compression_ratio': f"{compression_ratio:.1f}%",
            'total_processing_time': execution_time,
        },
        'project_output_dir': project_output_dir,
        'failed_image_segments': failed_image_segments,
    }

    if keywords_data and keywords_path:
        total_kw = sum(
            len(seg.get('keywords', [])) + len(seg.get('atmosphere', []))
            for seg in keywords_data.get('segments', [])
        )
        result['keywords'] = {
            'file_path': keywords_path,
            'total_keywords': total_kw,
            'avg_per_segment': total_kw / max(1, len(keywords_data.get('segments', [])))
            if keywords_data.get('segments') else 0,
        }

    if description_data and description_path:
        result['mini_summary'] = {
            'file_path': description_path,
            'summary_length': description_data.get('total_length', len(description_data.get('summary', ''))),
        }

    if cover_result:
        result['cover_generation'] = cover_result

    return result


__all__ = [
    "run_auto",
    "run_step_1",
    "run_step_1_5",
    "run_step_2",
    "run_step_3",
    "run_step_4",
    "run_step_5",
    "run_step_6",
]


# -------------------- Step-wise pipeline (for CLI step mode) --------------------

def run_step_1(
    input_file: str,
    output_dir: str,
    llm_server: str,
    llm_model: str,
    target_length: int,
    num_segments: int,
) -> Dict[str, Any]:
    reader = DocumentReader()
    document_content, _ = reader.read(input_file)
    raw_data = intelligent_summarize(llm_server, llm_model, document_content, target_length, num_segments)

    project_output_dir, raw_json_path, raw_docx_path = _initialize_project(raw_data, output_dir)

    return {
        "success": True,
        "project_output_dir": project_output_dir,
        "raw": {"raw_json_path": raw_json_path, "raw_docx_path": raw_docx_path, "total_length": raw_data.get('total_length', 0)},
    }


def run_step_1_5(project_output_dir: str, num_segments: int, is_new_project: bool = False, raw_data: Optional[Dict[str, Any]] = None, auto_mode: bool = False) -> Dict[str, Any]:
    """
    统一处理步骤1.5：段落切分
    
    Args:
        project_output_dir: 项目输出目录
        num_segments: 目标分段数
        is_new_project: 是否为新建项目
        raw_data: 原始数据（新建项目时提供）
        
    Returns:
        Dict[str, Any]: 处理结果，包含成功状态和相关信息
    """
    from core.utils import load_json_file, logger
    from core.document_processor import parse_raw_from_docx, export_script_to_docx
    
    try:
        print("正在处理原始内容为脚本...")
        
        # 使用 ProjectPaths 管理路径
        paths = ProjectPaths(project_output_dir)
        raw_json_path = paths.raw_json()
        raw_docx_path = paths.raw_docx()
        script_path = paths.script_json()
        script_docx_path = paths.script_docx()
        
        # 获取原始数据
        if is_new_project and raw_data is not None:
            # 新建项目：使用提供的raw_data
            logger.info(f"新建项目：使用提供的raw数据")
            current_raw_data = raw_data
        else:
            # 现有项目：从文件加载
            if not os.path.exists(raw_json_path):
                # 没有raw.json但有raw.docx，创建一个默认的raw.json
                current_raw_data = {"title": "手动创建项目", "golden_quote": "", "content": "", "target_segments": num_segments}
            else:
                print(f"加载raw数据: {raw_json_path}")
                current_raw_data = load_json_file(raw_json_path)
                if current_raw_data is None:
                    return {"success": False, "message": f"无法加载 raw.json 文件: {raw_json_path}"}
                # 优先使用config.py传入的num_segments参数，而不是raw.json中的旧值
                old_segments = current_raw_data.get("target_segments")
                if old_segments and old_segments != num_segments:
                    print(f"检测到分段数变更: {old_segments} → {num_segments}")
                print(f"当前分段数: {num_segments}")
        
        # 尝试从编辑后的DOCX文件解析数据
        updated_raw_data = current_raw_data
        if os.path.exists(raw_docx_path):
            try:
                parsed_data = parse_raw_from_docx(raw_docx_path)
                if parsed_data is not None:
                    print("已从编辑后的DOCX文件解析内容")
                    updated_raw_data = parsed_data
                    
                    # 更新元数据但保留原始信息，使用传入的num_segments参数
                    updated_raw_data.update({
                        "target_segments": num_segments,
                        "created_time": current_raw_data.get("created_time"),
                        "model_info": current_raw_data.get("model_info", {}),
                        "total_length": len(updated_raw_data.get("content", ""))
                    })
                    
                    # 更新raw.json文件
                    with open(raw_json_path, 'w', encoding='utf-8') as f:
                        json.dump(updated_raw_data, f, ensure_ascii=False, indent=2)
                    print(f"已更新原始JSON: {raw_json_path}")
                else:
                    print("⚠️  DOCX解析返回None，使用原始数据")
            except Exception as e:
                print(f"⚠️  解析DOCX失败，使用原始数据: {e}")
        
        # 检查最终数据
        if updated_raw_data is None:
            return {"success": False, "message": "处理raw数据失败：数据为空"}
        
        # 用户选择切分模式（仅在交互模式下）
        split_mode = "auto"  # 默认自动切分
        if not auto_mode:  # 只有非全自动模式才显示选择界面
            try:
                from cli.ui_helpers import prompt_choice
                choice = prompt_choice("请选择文本切分方式", ["手动切分(根据换行符)", "自动切分(智能均分)"], default_index=1)
                if choice and choice.startswith("手动"):
                    split_mode = "manual"
            except:
                pass  # 如果无法显示选择界面，使用默认值

        # 处理为分段脚本数据，使用config.py传入的num_segments
        script_data = process_raw_to_script(updated_raw_data, num_segments, split_mode)
        
        # 保存script.json
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)
        print(f"分段脚本已保存到: {script_path}")
        
        # 生成可阅读的script.docx
        try:
            export_script_to_docx(script_data, script_docx_path)
            print(f"阅读版DOCX已保存到: {script_docx_path}")
        except Exception as e:
            print(f"⚠️  生成script.docx失败: {e}")
        
        # 生成纯文本分段文件（使用与SRT相同的文本切分逻辑）
        try:
            # 从config获取字幕配置中的max_chars_per_line参数
            max_chars_per_line = config.SUBTITLE_MAX_CHARS_PER_LINE
            txt_path = export_plain_text_segments(script_data, paths.text, max_chars_per_line)
            print(f"✅ 纯文本分段文件已保存到: {txt_path}")
        except Exception as e:
            print(f"⚠️  生成纯文本分段文件失败: {e}")
            logger.warning(f"生成纯文本分段文件失败: {e}")
        
        logger.info(f"步骤1.5处理完成: {script_path}")
        return {
            "success": True,
            "script_data": script_data,
            "script_path": script_path,
            "message": "步骤1.5处理完成"
        }
        
    except Exception as e:
        logger.error(f"步骤1.5处理失败: {str(e)}")
        return {"success": False, "message": f"步骤1.5处理失败: {str(e)}"}


def run_step_2(
    llm_server: str,
    llm_model: str,
    project_output_dir: str,
    script_path: str = None,
    images_method: str = "keywords",
) -> Dict[str, Any]:
    # 使用 ProjectPaths 管理路径
    paths = ProjectPaths(project_output_dir)
    
    # 加载脚本数据（注意：如果频繁调用，考虑添加缓存机制）
    script_data = load_json_file(script_path) if script_path else load_json_file(paths.script_json())
    if script_data is None:
        return {"success": False, "message": "未找到脚本数据，请先完成步骤1.5"}

    images_method = images_method or getattr(config, "SUPPORTED_IMAGE_METHODS", ["keywords"])[0]

    if images_method == "description":
        raw_data = load_json_file(paths.raw_json()) if os.path.exists(paths.raw_json()) else None
        description_source = _resolve_description_source_text(
            project_output_dir, raw_data=raw_data, script_data=script_data
        )
        description_data = generate_description_summary(
            llm_server, llm_model, description_source or "", max_chars=200
        )
        description_path = paths.mini_summary_json()
        with open(description_path, 'w', encoding='utf-8') as f:
            json.dump(description_data, f, ensure_ascii=False, indent=2)
        return {"success": True, "mini_summary_path": description_path}

    keywords_data = extract_keywords(llm_server, llm_model, script_data)
    keywords_path = paths.keywords_json()
    with open(keywords_path, 'w', encoding='utf-8') as f:
        json.dump(keywords_data, f, ensure_ascii=False, indent=2)
    return {"success": True, "keywords_path": keywords_path}


def run_step_3(
    image_server: str,
    image_model: str,
    image_size: str,
    image_style_preset: str,
    project_output_dir: str,
    opening_image_style: str,
    images_method: str = "keywords",
    opening_quote: bool = True,
    target_segments: Optional[List[int]] = None,
    regenerate_opening: bool = True,
    llm_model: Optional[str] = None,
    llm_server: Optional[str] = None,
) -> Dict[str, Any]:
    # 使用 ProjectPaths 管理路径
    paths = ProjectPaths(project_output_dir)
    paths.ensure_dirs_exist()

    script_data = load_json_file(paths.script_json())
    if script_data is None:
        return {"success": False, "message": "未找到脚本数据，请先完成步骤1.5"}

    segments = script_data.get('segments', [])
    total_segments = len(segments)
    if total_segments == 0:
        return {"success": False, "message": "脚本中缺少段落内容"}

    selected_segments: Optional[List[int]] = None
    if target_segments is not None:
        raw_targets = list(target_segments)
        parsed_targets: List[int] = []
        for value in raw_targets:
            try:
                parsed_targets.append(int(value))
            except (TypeError, ValueError):
                continue
        selected_segments = sorted({idx for idx in parsed_targets if 1 <= idx <= total_segments})
        if raw_targets and not selected_segments:
            return {
                "success": False,
                "message": f"段落选择无效，请输入 1-{total_segments} 之间的数字",
            }

    images_method = images_method or getattr(config, "SUPPORTED_IMAGE_METHODS", ["keywords"])[0]

    if llm_model and not llm_server:
        llm_server = auto_detect_server_from_model(llm_model, "llm")

    keywords_data = None
    description_data = None
    if images_method == 'description':
        description_data = load_json_file(paths.mini_summary_json())
        if description_data is None:
            return {"success": False, "message": "未找到描述小结，请先执行步骤2生成描述"}
    else:
        keywords_data = load_json_file(paths.keywords_json())
        if keywords_data is None:
            return {"success": False, "message": "未找到关键词数据，请先执行步骤2生成关键词"}

    opening_image_path = None
    opening_image_file = paths.opening_image()
    opening_previously_exists = os.path.exists(opening_image_file)
    opening_regenerated = False
    if opening_quote:
        need_refresh = regenerate_opening or not opening_previously_exists
        if need_refresh:
            opening_image_path = generate_opening_image(
                image_server, image_model, opening_image_style, image_size, paths.images, opening_quote
            )
            opening_regenerated = bool(opening_image_path)
        elif opening_previously_exists:
            opening_image_path = opening_image_file
            print(f"保持现有开场图像: {opening_image_path}")

    should_generate_segments = selected_segments is None or len(selected_segments) > 0

    if should_generate_segments:
        generation_targets = None if selected_segments is None else selected_segments
        image_result = generate_images_for_segments(
            image_server,
            image_model,
            script_data,
            image_style_preset,
            image_size,
            paths.images,
            images_method=images_method,
            keywords_data=keywords_data,
            description_data=description_data,
            target_segments=generation_targets,
            llm_model=llm_model,
            llm_server=llm_server,
        )
    else:
        image_paths = []
        for idx in range(1, total_segments + 1):
            segment_path = paths.segment_image(idx)
            image_paths.append(segment_path if os.path.exists(segment_path) else "")
        image_result = {
            'image_paths': image_paths,
            'failed_segments': [],
            'processed_segments': [],
        }

    failed_segments = image_result.get('failed_segments', [])

    if failed_segments:
        failed_str = '、'.join(str(idx) for idx in failed_segments)
        return {
            'success': False,
            'message': f"第 {failed_str} 段图像生成失败，请调整提示或稍后重试。",
            'failed_segments': failed_segments,
            'image_paths': image_result.get('image_paths', []),
            'opening_image_path': opening_image_path,
        }

    processed_segments = image_result.get('processed_segments', [])
    if selected_segments is None:
        message = "段落图像生成完成"
        if opening_regenerated:
            message += "，开场图像已更新"
    elif processed_segments:
        seg_text = '、'.join(str(idx) for idx in processed_segments)
        message = f"已生成第 {seg_text} 段图像"
        if opening_regenerated:
            message += " 并刷新开场图像"
    else:
        message = "未生成新的段落图像"
        if opening_regenerated:
            message = "已重新生成开场图像"

    result_payload = {
        'success': True,
        'opening_image_path': opening_image_path,
        'processed_segments': processed_segments,
        'message': message,
    }
    for key, value in image_result.items():
        if key != 'processed_segments':
            result_payload[key] = value
    return result_payload


def run_step_4(
    tts_server: str,
    voice: str,
    project_output_dir: str,
    opening_quote: bool = True,
    target_segments: Optional[List[int]] = None,
    regenerate_opening: bool = True,
    speech_rate: int = 0,
    loudness_rate: int = 0,
    emotion: str = "neutral",
    emotion_scale: int = 4,
    mute_cut_threshold: int = 400,
    mute_cut_min_silence_ms: int = 200,
    mute_cut_remain_ms: int = 100,
) -> Dict[str, Any]:
    # 使用 ProjectPaths 管理路径
    paths = ProjectPaths(project_output_dir)
    paths.ensure_dirs_exist()

    script_data = load_json_file(paths.script_json())
    if script_data is None:
        return {"success": False, "message": "未找到脚本数据，请先完成步骤1.5"}

    segments = script_data.get('segments', [])
    total_segments = len(segments)
    if total_segments == 0:
        return {"success": False, "message": "脚本中缺少段落内容"}

    selected_segments: Optional[List[int]] = None
    if target_segments is not None:
        raw_targets = list(target_segments)
        parsed_targets: List[int] = []
        for value in raw_targets:
            try:
                parsed_targets.append(int(value))
            except (TypeError, ValueError):
                continue
        selected_segments = sorted({idx for idx in parsed_targets if 1 <= idx <= total_segments})
        if raw_targets and not selected_segments:
            return {
                "success": False,
                "message": f"段落选择无效，请输入 1-{total_segments} 之间的数字",
            }

    generation_targets = None if selected_segments is None else selected_segments
    voice_result = synthesize_voice_for_segments(
        tts_server,
        voice,
        script_data,
        paths.voice,
        target_segments=generation_targets,
        speech_rate=speech_rate,
        loudness_rate=loudness_rate,
        emotion=emotion,
        emotion_scale=emotion_scale,
        mute_cut_threshold=mute_cut_threshold,
        mute_cut_min_silence_ms=mute_cut_min_silence_ms,
        mute_cut_remain_ms=mute_cut_remain_ms,
    )
    audio_paths = voice_result.get("audio_paths", [])
    missing_segments = voice_result.get("missing_segments", [])

    opening_audio_file = paths.opening_audio()
    opening_previously_exists = os.path.exists(opening_audio_file)
    narration_path = _invoke_opening_narration(
        script_data,
        paths.voice,
        voice,
        opening_quote,
        announce=True,
        force_regenerate=regenerate_opening,
        speech_rate=speech_rate,
        loudness_rate=loudness_rate,
        emotion=emotion,
        emotion_scale=emotion_scale,
        mute_cut_threshold=mute_cut_threshold,
        mute_cut_min_silence_ms=mute_cut_min_silence_ms,
        mute_cut_remain_ms=mute_cut_remain_ms,
    )

    opening_refreshed = bool(
        opening_quote and narration_path and (regenerate_opening or not opening_previously_exists)
    )

    processed_segments = (
        list(range(1, total_segments + 1)) if selected_segments is None else list(selected_segments)
    )
    if selected_segments is None:
        message = "段落语音生成完成"
        if opening_refreshed:
            message += "，开场金句音频已更新"
    elif processed_segments:
        seg_text = '、'.join(str(idx) for idx in processed_segments)
        message = f"已生成第 {seg_text} 段语音"
        if opening_refreshed:
            message += " 并刷新开场金句音频"
    else:
        message = "未生成新的段落语音"
        if opening_refreshed:
            message = "已重新生成开场金句音频"

    return {
        "success": True,
        "audio_paths": audio_paths,
        "processed_segments": processed_segments,
        "missing_segments": missing_segments,
        "message": message,
    }


def run_step_5(
    project_output_dir: str,
    image_size: str,
    enable_subtitles: bool,
    bgm_filename: str,
    voice: str,
    opening_quote: bool = True,
    speech_rate: int = 0,
    loudness_rate: int = 0,
    emotion: str = "neutral",
    emotion_scale: int = 4,
    mute_cut_threshold: int = 400,
    mute_cut_min_silence_ms: int = 200,
    mute_cut_remain_ms: int = 100,
) -> Dict[str, Any]:
    project_root = os.path.dirname(os.path.dirname(__file__))
    
    # 使用 ProjectPaths 管理路径
    paths = ProjectPaths(project_output_dir)

    # 前置检查：确保必要文件存在
    if not os.path.exists(paths.script_json()):
        return {"success": False, "message": "脚本文件不存在，请先完成步骤1.5"}

    script_data = load_json_file(paths.script_json())
    if not script_data:
        return {"success": False, "message": "脚本文件加载失败"}

    # 检查图像文件
    expected_segments = script_data.get('actual_segments', 0)
    image_count = 0
    for i in range(1, expected_segments + 1):
        if paths.segment_image_exists(i):
            image_count += 1
        else:
            # 检查视频文件
            for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.m4v']:
                vid_path = os.path.join(paths.images, f"segment_{i}{ext}")
                if os.path.exists(vid_path):
                    image_count += 1
                    break

    # 检查音频文件
    audio_count = 0
    for i in range(1, expected_segments + 1):
        if paths.segment_audio_exists(i):
            audio_count += 1

    if image_count == 0:
        return {"success": False, "message": "未找到图像文件，请先完成步骤3"}
    if audio_count == 0:
        return {"success": False, "message": "未找到音频文件，请先完成步骤4"}
    if image_count != expected_segments:
        return {"success": False, "message": f"图像文件不完整，需要{expected_segments}个，找到{image_count}个"}
    if audio_count != expected_segments:
        return {"success": False, "message": f"音频文件不完整，需要{expected_segments}个，找到{audio_count}个"}

    # Resolve ordered assets (支持图片和视频文件)
    image_paths = []
    for i in range(1, script_data.get('actual_segments', 0) + 1):
        # 检查图片文件
        img_path = paths.segment_image(i)
        if os.path.exists(img_path):
            image_paths.append(img_path)
            continue
        # 检查视频文件
        for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.m4v']:
            vid_path = os.path.join(paths.images, f"segment_{i}{ext}")
            if os.path.exists(vid_path):
                image_paths.append(vid_path)
                break
    
    audio_paths = []
    for i in range(1, script_data.get('actual_segments', 0) + 1):
        audio_path = paths.segment_audio_exists(i)
        if audio_path:
            audio_paths.append(audio_path)

    # BGM
    bgm_audio_path = _resolve_bgm_audio_path(bgm_filename, project_root)

    # Opening assets
    opening_image_candidate = paths.opening_image() if os.path.exists(paths.opening_image()) else None
    opening_golden_quote = (script_data or {}).get("golden_quote", "")
    opening_narration_audio_path = _invoke_opening_narration(
        script_data,
        paths.voice,
        voice,
        opening_quote,
        speech_rate=speech_rate,
        loudness_rate=loudness_rate,
        emotion=emotion,
        emotion_scale=emotion_scale,
        mute_cut_threshold=mute_cut_threshold,
        mute_cut_min_silence_ms=mute_cut_min_silence_ms,
        mute_cut_remain_ms=mute_cut_remain_ms,
    )

    composer = VideoComposer()
    final_video_path = composer.compose_video(
        image_paths, audio_paths, paths.final_video(),
        script_data=script_data, enable_subtitles=enable_subtitles,
        bgm_audio_path=bgm_audio_path,
        opening_image_path=opening_image_candidate,
        opening_golden_quote=opening_golden_quote,
        opening_narration_audio_path=opening_narration_audio_path,
        bgm_volume=float(getattr(config, "BGM_DEFAULT_VOLUME", 0.2)),
        narration_volume=float(getattr(config, "NARRATION_DEFAULT_VOLUME", 1.0)),
        image_size=image_size,
        opening_quote=opening_quote,
        project_root=project_output_dir,
    )

    return {"success": True, "final_video": final_video_path}


def run_step_6(
    project_output_dir: str,
    cover_image_size: str,
    cover_image_model: str,
    cover_image_style: str,
    cover_image_count: int,
) -> Dict[str, Any]:
    # 使用 ProjectPaths 管理路径
    paths = ProjectPaths(project_output_dir)
    
    if not os.path.exists(paths.raw_json()):
        return {"success": False, "message": "缺少 raw.json，请先完成步骤1"}

    raw_data = load_json_file(paths.raw_json())
    if raw_data is None:
        return {"success": False, "message": "raw.json 加载失败"}

    script_data = load_json_file(paths.script_json()) if os.path.exists(paths.script_json()) else None

    try:
        cover_result = _run_cover_generation(
            project_output_dir,
            cover_image_size,
            cover_image_model,
            cover_image_style,
            cover_image_count,
            script_data,
            raw_data,
        )
        return {"success": True, **cover_result}
    except Exception as e:
        return {"success": False, "message": str(e)}


__all__ += [
    "run_step_1",
    "run_step_1_5",
    "run_step_2",
    "run_step_3",
    "run_step_4",
    "run_step_5",
]


def _run_cover_generation(
    project_output_dir: str,
    cover_image_size: Optional[str],
    cover_image_model: Optional[str],
    cover_image_style: Optional[str],
    cover_image_count: int,
    script_data: Optional[Dict[str, Any]],
    raw_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if not script_data and not raw_data:
        raise ValueError("缺少脚本或原始数据")

    base = script_data or raw_data or {}
    video_title = base.get("title") or "未命名视频"
    content_title = base.get("content_title") or video_title
    cover_subtitle = base.get("cover_subtitle") or ""

    cover_image_size = cover_image_size or config.DEFAULT_IMAGE_SIZE
    cover_image_model = cover_image_model or config.RECOMMENDED_MODELS["image"].get("doubao", ["doubao-seedream-4-0-250828"])[0]
    cover_image_style = cover_image_style or "cover01"

    image_server = auto_detect_server_from_model(cover_image_model, "image")
    try:
        Config.validate_parameters(
            target_length=config.MIN_TARGET_LENGTH,
            num_segments=config.MIN_NUM_SEGMENTS,
            llm_server=config.SUPPORTED_LLM_SERVERS[0],
            image_server=image_server,
            tts_server=config.SUPPORTED_TTS_SERVERS[0],
            image_model=cover_image_model,
            image_size=cover_image_size,
        )
    except Exception as e:
        raise ValueError(f"封面参数校验失败: {e}")

    return generate_cover_images(
        project_output_dir,
        image_server,
        cover_image_model,
        cover_image_size,
        cover_image_style,
        max(1, int(cover_image_count or 1)),
        video_title,
        content_title,
        cover_subtitle,
    )


__all__.append("run_step_6")
