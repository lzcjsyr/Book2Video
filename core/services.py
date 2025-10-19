"""
Core services: unified entry points for model calls (migrated from genai_api).
"""

import os
import random
import json
import base64
import requests
from openai import OpenAI

from config import config
from core.utils import logger, APIError, retry_on_failure


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
    encoding="wav",
    speech_rate: int = 0,
    loudness_rate: int = 0,
    bit_rate: int = 128000,
    emotion: str = "neutral",
    emotion_scale: int = 4,
    mute_cut_remain_ms: int = 400,
    mute_cut_threshold: int = 100,
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
        bit_rate: 音频比特率 (64000-140000)
        emotion: 情感类型 (neutral, happy, sad等)
        emotion_scale: 情感强度 (1-5)
        mute_cut_remain_ms: 静音切除后保留的静音时长 (毫秒, 默认400)
        mute_cut_threshold: 静音切除阈值 (默认100)

    Returns:
        bool: 成功返回True
    """
    # ============ 1. 验证配置 ============
    if not config.BYTEDANCE_TTS_APPID or not config.BYTEDANCE_TTS_ACCESS_TOKEN:
        raise APIError("字节语音合成配置不完整，请检查BYTEDANCE_TTS_APPID和BYTEDANCE_TTS_ACCESS_TOKEN")
    
    APPID = config.BYTEDANCE_TTS_APPID
    ACCESS_TOKEN = config.BYTEDANCE_TTS_ACCESS_TOKEN
    RESOURCE_ID = config.RESOURCE_ID
    
    # ============ 2. 参数验证和规范化 ============
    speech_rate = max(-50, min(100, int(speech_rate or 0)))
    loudness_rate = max(-50, min(100, int(loudness_rate or 0)))
    bit_rate = max(64000, min(140000, int(bit_rate or 128000)))
    emotion = str(emotion or "neutral")
    emotion_scale = max(1, min(5, int(emotion_scale or 4)))
    
    logger.info(
        f"调用火山引擎TTS API - 资源: {RESOURCE_ID}, 音色: {voice}, "
        f"文本长度: {len(text)}字符, 语速: {speech_rate}, 音量: {loudness_rate}, "
        f"比特率: {bit_rate}, 情感: {emotion}({emotion_scale})"
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
        "format": "mp3",
        "sample_rate": 24000,
        "bit_rate": bit_rate,
        "emotion": emotion,
        "emotion_scale": emotion_scale,
        "speech_rate": speech_rate,
        "loudness_rate": loudness_rate
    }
    
    # 构建 additions 参数（额外配置）
    additions = {
        "silence_duration": 0,  # 句尾静音时长（毫秒）
        "mute_cut_remain_ms": mute_cut_remain_ms,  # 静音切除后保留的静音时长（毫秒）
        "mute_cut_threshold": mute_cut_threshold  # 静音切除阈值
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
        
        # ============ 6. 保存音频文件 ============
        from core.utils import ensure_directory_exists
        ensure_directory_exists(os.path.dirname(output_filename))
        
        # 先保存为临时 mp3 文件
        temp_mp3 = output_filename.rsplit('.', 1)[0] + '_temp.mp3'
        with open(temp_mp3, "wb") as f:
            f.write(audio_data)
        
        # 根据需要转换为 wav 格式
        if encoding.lower() == "wav" or output_filename.lower().endswith('.wav'):
            try:
                from moviepy.audio.io.AudioFileClip import AudioFileClip
                audio_clip = AudioFileClip(temp_mp3)
                audio_clip.write_audiofile(output_filename, codec='pcm_s16le', logger=None)
                audio_clip.close()
                os.remove(temp_mp3)
                logger.info(f"语音合成成功 - 文件大小: {len(audio_data)/1024:.1f} KB, 已保存为 WAV: {output_filename}")
            except Exception as e:
                logger.error(f"MP3转WAV失败: {str(e)}, 保留MP3格式")
                os.rename(temp_mp3, output_filename)
                logger.warning(f"语音合成成功 - 文件大小: {len(audio_data)/1024:.1f} KB, 已保存为 MP3: {output_filename}")
        else:
            os.rename(temp_mp3, output_filename)
            logger.info(f"语音合成成功 - 文件大小: {len(audio_data)/1024:.1f} KB, 已保存为 MP3: {output_filename}")
        
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
