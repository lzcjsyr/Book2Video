"""
Core services: unified entry points for model calls (migrated from genai_api).
"""

import os
import random
import json
import base64
import struct
import requests
from openai import OpenAI

from config import config
from core.utils import logger, APIError, retry_on_failure


def _create_wav_header(pcm_data_size, sample_rate=48000, channels=1, bits_per_sample=16):
    """创建 WAV 文件头（44 字节）"""
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8

    return struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + pcm_data_size,
        b'WAVE',
        b'fmt ',
        16,
        1,
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b'data',
        pcm_data_size
    )


def _remove_silence_from_pcm(pcm_data: bytes, sample_rate: int = 48000,
                            threshold: int = 400, min_silence_ms: int = 200,
                            remain_ms: int = 100) -> bytes:
    """
    从PCM音频中移除过长的静音段（内存处理）

    正确逻辑：
    1. 只切除连续静音 > min_silence_ms 的段落
    2. 在真正的静音段前后各保留 remain_ms
    3. 短暂的弱音不会被切除

    Args:
        pcm_data: PCM音频数据
        sample_rate: 采样率
        threshold: 静音判定阈值（音量低于此值视为静音）
        min_silence_ms: 最小静音长度（毫秒，只切除长于此值的静音）
        remain_ms: 切除后保留的静音时长（毫秒，在静音段前后各保留）
    """
    if not pcm_data or threshold <= 0:
        return pcm_data

    try:
        import numpy as np

        # 转为int16数组并计算音量
        audio = np.frombuffer(pcm_data, dtype=np.int16)
        volume = np.abs(audio)

        # 滑动窗口平滑（避免误切单个采样点）
        window = max(1, sample_rate // 100)  # 10ms窗口
        smoothed = np.convolve(volume, np.ones(window)/window, mode='same')

        # 标记静音点
        is_silence = smoothed <= threshold

        # 检测所有静音段的起止位置
        silence_bounds = np.diff(np.concatenate([[0], is_silence.astype(int), [0]]))
        silence_starts = np.where(silence_bounds == 1)[0]
        silence_ends = np.where(silence_bounds == -1)[0]

        if len(silence_starts) == 0:
            return pcm_data

        # 只处理长静音段
        min_silence_samples = int(sample_rate * min_silence_ms / 1000)
        remain_samples = int(sample_rate * remain_ms / 1000)

        # 构建保留区域（默认全部保留）
        keep_ranges = []
        last_end = 0

        for sil_start, sil_end in zip(silence_starts, silence_ends):
            silence_len = sil_end - sil_start

            if silence_len > min_silence_samples:
                # 长静音：保留语音段 + 静音前后各remain_ms
                keep_ranges.append((last_end, sil_start + remain_samples))
                last_end = sil_end - remain_samples
            # 短静音：不切除，自然包含在keep_ranges中

        # 添加最后一段到结尾
        keep_ranges.append((last_end, len(audio)))

        # 拼接所有保留段
        segments = [audio[start:end] for start, end in keep_ranges if end > start]

        if not segments:
            return pcm_data

        return np.concatenate(segments).tobytes()
    except Exception as e:
        logger.warning(f"静音切除失败: {e}")
        return pcm_data


@retry_on_failure(max_retries=2, delay=2.0)
def text_to_text(server, model, prompt, system_message="", max_tokens=4000, temperature=0.5, output_format="text"):
    logger.info(f"调用{server}的{model}模型生成文本，提示词长度: {len(prompt)}字符")
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ]
    try:
        if server == "openrouter":
            if not config.OPENROUTER_API_KEY:
                raise APIError("OPENROUTER_API_KEY未配置")
            api_key = config.OPENROUTER_API_KEY
            base_url = config.OPENROUTER_BASE_URL
        elif server == "siliconflow":
            if not config.SILICONFLOW_KEY:
                raise APIError("SILICONFLOW_KEY未配置")
            api_key = config.SILICONFLOW_KEY
            base_url = config.SILICONFLOW_BASE_URL
        else:
            raise ValueError(f"不支持的服务商: {server}，支持的服务商: {config.SUPPORTED_LLM_SERVERS}")

        client = OpenAI(api_key=api_key, base_url=base_url)
        request_params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "seed": random.randint(1, 1000000000)
        }

        response = client.chat.completions.create(**request_params)
        result = response.choices[0].message.content
        logger.info(f"{server} API调用成功，返回内容长度: {len(result)}字符")
        return result
    except Exception as e:
        logger.error(f"文本生成失败: {str(e)}")
        raise APIError(f"文本生成失败: {str(e)}")


@retry_on_failure(max_retries=2, delay=2.0)
def text_to_image_doubao(prompt, size="1024x1024", model="doubao-seedream-3-0-t2i-250415"):
    if not config.SEEDREAM_API_KEY:
        raise APIError("SEEDREAM_API_KEY未配置，无法使用豆包图像生成服务")
    logger.info(f"使用豆包Seedream生成图像，模型: {model}，尺寸: {size}，提示词长度: {len(prompt)}字符")
    try:
        from volcenginesdkarkruntime import Ark
        client = Ark(
            base_url=config.ARK_BASE_URL,
            api_key=config.SEEDREAM_API_KEY,
        )

        # 根据模型名称判断API版本
        is_v4_model = "seedream-4" in model

        if is_v4_model:
            # V4模型：移除guidance_scale，添加新参数支持
            response = client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                response_format="url",
                watermark=False
            )
        else:
            # V3模型：保持原有参数
            response = client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                guidance_scale=7.5,
                watermark=False
            )

        if response and response.data:
            image_url = response.data[0].url
            logger.info(f"豆包图像生成成功，返回URL: {image_url[:50]}...")
            return image_url
        raise APIError("豆包图像生成API返回空响应")
    except ImportError:
        logger.error("未安装volcenginesdkarkruntime，请运行: pip install volcengine-python-sdk[ark]")
        raise APIError("缺少依赖包volcenginesdkarkruntime")
    except Exception as e:
        logger.error(f"豆包图像生成失败: {str(e)}")
        raise APIError(f"豆包图像生成失败: {str(e)}")


@retry_on_failure(max_retries=2, delay=2.0)
def text_to_image_siliconflow(prompt, size="1024x1024", model="Qwen/Qwen-Image"):
    if not config.SILICONFLOW_KEY:
        raise APIError("SILICONFLOW_KEY未配置，无法使用硅基流动图像生成服务")

    base_url = getattr(config, "SILICONFLOW_IMAGE_BASE_URL", "https://api.siliconflow.cn/v1/images/generations")
    headers = {
        "Authorization": f"Bearer {config.SILICONFLOW_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "prompt": prompt
    }
    if size:
        payload["size"] = size

    logger.info(f"使用硅基流动生成图像，模型: {model}，尺寸: {size}，提示词长度: {len(prompt)}字符")

    try:
        response = requests.post(base_url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"硅基流动图像生成请求失败: {str(e)}")
        raise APIError(f"硅基流动图像生成失败: {str(e)}")

    items = data.get("data") if isinstance(data, dict) else None
    if not items:
        raise APIError("硅基流动图像生成API返回空响应")

    item = items[0] if isinstance(items, list) else None
    if not isinstance(item, dict):
        raise APIError("硅基流动图像生成API返回格式不正确")

    if item.get("url"):
        return {"type": "url", "data": item["url"]}
    if item.get("b64_json"):
        return {"type": "b64", "data": item["b64_json"]}

    raise APIError("硅基流动图像生成API返回缺少可用的图像数据")


@retry_on_failure(max_retries=2, delay=1.0)
def text_to_audio_bytedance(
    text,
    output_filename,
    voice="zh_male_yuanboxiaoshu_moon_bigtts",
    encoding="mp3",
    speech_rate: int = 0,
    loudness_rate: int = 0,
    emotion: str = "neutral",
    emotion_scale: int = 4,
    mute_cut_threshold: int = 400,
    mute_cut_min_silence_ms: int = 200,
    mute_cut_remain_ms: int = 100,
):
    """
    使用火山引擎TTS API进行语音合成（HTTP 单向流式接口）

    Args:
        text: 要合成的文本
        output_filename: 输出文件路径（.wav格式）
        voice: 音色ID
        encoding: 输出编码格式（保留参数，实际输出为wav）
        speech_rate: 语速 (-50到100, 0=正常, 100=2倍速, -50=0.5倍速)
        loudness_rate: 音量 (-50到100, 0=正常, 100=2倍音量, -50=0.5倍音量)
        emotion: 情感类型 (neutral, happy, sad等)
        emotion_scale: 情感强度 (1-5)
        mute_cut_remain_ms: 静音切除后保留的静音时长 (毫秒, 默认400)
        mute_cut_threshold: 静音切除阈值 (默认100)

    Returns:
        bool: 成功返回True
    """
    # ============ 1. 验证配置 ============
    if not config.BYTEDANCE_TTS_APPID or not config.BYTEDANCE_TTS_ACCESS_TOKEN:
        raise APIError("豆包语音配置不完整，请检查BYTEDANCE_TTS_APPID和BYTEDANCE_TTS_ACCESS_TOKEN")
    
    APPID = config.BYTEDANCE_TTS_APPID
    ACCESS_TOKEN = config.BYTEDANCE_TTS_ACCESS_TOKEN
    RESOURCE_ID = config.RESOURCE_ID
    
    # ============ 2. 参数验证和规范化 ============
    speech_rate = max(-50, min(100, int(speech_rate or 0)))
    loudness_rate = max(-50, min(100, int(loudness_rate or 0)))
    emotion = str(emotion or "neutral")
    emotion_scale = max(1, min(5, int(emotion_scale or 4)))

    logger.info(
        f"调用火山引擎TTS API - 资源: {RESOURCE_ID}, 音色: {voice}, "
        f"文本长度: {len(text)}字符, 语速: {speech_rate}, 音量: {loudness_rate}, "
        f"情感: {emotion}({emotion_scale})"
    )
    
    # ============ 3. 构建请求参数 ============
    url = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
    
    headers = {
        "X-Api-App-Id": APPID,
        "X-Api-Access-Key": ACCESS_TOKEN,
        "X-Api-Resource-Id": RESOURCE_ID,
        "Content-Type": "application/json"
    }
    
    # 构建 audio_params（音频参数）
    audio_params = {
        "format": "pcm",
        "sample_rate": 48000,
        "emotion": emotion,
        "emotion_scale": emotion_scale,
        "speech_rate": speech_rate,
        "loudness_rate": loudness_rate
    }
    
    # 构建 additions 参数（额外配置）
    additions = {
        "silence_duration": 0,  # 句尾静音时长（毫秒）
    }
    
    # 完整的请求体结构
    payload = {
        "user": {
            "uid": "aigc_video_user"
        },
        "req_params": {
            "text": text,
            "speaker": voice,
            "audio_params": audio_params,
            "additions": json.dumps(additions)  # additions 需要序列化为 JSON 字符串
        }
    }
    
    # ============ 4. 发起 HTTP 流式请求 ============
    session = requests.Session()
    try:
        response = session.post(url, headers=headers, json=payload, stream=True, timeout=30)
        
        # 检查响应状态
        if response.status_code != 200:
            error_text = response.text
            logger.error(f"TTS API请求失败 - 状态码: {response.status_code}, 错误: {error_text}")
            raise APIError(f"TTS API请求失败: {error_text}")
        
        # 记录请求日志ID（用于排查问题）
        logid = response.headers.get('X-Tt-Logid', 'N/A')
        logger.debug(f"TTS 请求成功 - X-Tt-Logid: {logid}")
        
        # ============ 5. 接收音频流数据 ============
        audio_data = bytearray()
        
        for chunk in response.iter_lines(decode_unicode=True):
            if not chunk:
                continue
            
            try:
                data = json.loads(chunk)
            except json.JSONDecodeError:
                logger.warning(f"无法解析响应数据: {chunk[:100]}")
                continue
            
            # 正常音频数据
            if data.get("code", 0) == 0 and "data" in data and data["data"]:
                audio_data.extend(base64.b64decode(data["data"]))
                continue
            
            # 结束标记
            if data.get("code", 0) == 20000000:
                break
            
            # 错误响应
            if data.get("code", 0) > 0:
                error_msg = data.get("message", "未知错误")
                logger.error(f"TTS API返回错误: code={data.get('code')}, message={error_msg}")
                raise APIError(f"TTS API错误: {error_msg}")
        
        if not audio_data:
            raise APIError("未接收到音频数据")

        # ============ 6. 本地静音切除 ============
        original_size = len(audio_data)
        if mute_cut_threshold > 0:
            audio_data = _remove_silence_from_pcm(
                bytes(audio_data), 48000, mute_cut_threshold,
                mute_cut_min_silence_ms, mute_cut_remain_ms
            )
            reduction = (1 - len(audio_data) / original_size) * 100 if original_size > 0 else 0
            logger.info(f"静音切除: {original_size/1024:.1f}KB → {len(audio_data)/1024:.1f}KB (-{reduction:.1f}%)")

        # ============ 7. 保存音频文件 ============
        from core.utils import ensure_directory_exists
        ensure_directory_exists(os.path.dirname(output_filename))

        # 添加 WAV header 并保存为 WAV 文件
        wav_header = _create_wav_header(len(audio_data), sample_rate=48000)
        with open(output_filename, "wb") as f:
            f.write(wav_header)
            f.write(audio_data)

        logger.info(f"语音合成成功 - 文件: {(len(audio_data) + 44)/1024:.1f} KB, 已保存: {output_filename}")

        return True
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"语音合成失败: {str(e)}")
        raise APIError(f"语音合成失败: {str(e)}")
    finally:
        response.close()
        session.close()


__all__ = [
    'text_to_text',
    'text_to_image_doubao',
    'text_to_image_siliconflow',
    'text_to_audio_bytedance',
]
