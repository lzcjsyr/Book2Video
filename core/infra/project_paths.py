"""
项目路径管理器 - 集中管理所有项目相关的文件路径
避免在多个地方重复构建路径逻辑
"""

import os
from typing import Optional


class ProjectPaths:
    """项目路径管理器，统一管理项目文件结构"""
    
    def __init__(self, project_dir: str):
        """
        初始化项目路径管理器
        
        Args:
            project_dir: 项目根目录路径
        """
        self.root = project_dir
        self.text = os.path.join(project_dir, "text")
        self.images = os.path.join(project_dir, "images")
        self.voice = os.path.join(project_dir, "voice")
    
    # ==================== Text 目录相关路径 ====================
    
    def raw_json(self) -> str:
        """原始数据JSON文件路径"""
        return os.path.join(self.text, "raw.json")
    
    def raw_docx(self) -> str:
        """原始数据可编辑DOCX文件路径"""
        return os.path.join(self.text, "raw.docx")
    
    def script_json(self) -> str:
        """脚本JSON文件路径"""
        return os.path.join(self.text, "script.json")
    
    def script_docx(self) -> str:
        """脚本可阅读DOCX文件路径"""
        return os.path.join(self.text, "script.docx")
    
    def keywords_json(self) -> str:
        """关键词JSON文件路径"""
        return os.path.join(self.text, "keywords.json")
    
    def mini_summary_json(self) -> str:
        """描述模式小结JSON文件路径"""
        return os.path.join(self.text, "mini_summary.json")
    
    # ==================== Images 目录相关路径 ====================
    
    def opening_image(self) -> str:
        """开场素材路径（自动检测图片或视频格式）"""
        # 按优先级检查：视频格式优先，然后是图片格式
        for ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.png', '.jpg']:
            path = os.path.join(self.images, f"opening{ext}")
            if os.path.exists(path):
                return path
        # 默认返回 PNG 路径（向后兼容）
        return os.path.join(self.images, "opening.png")
    
    def segment_image(self, index: int) -> str:
        """
        段落图片路径
        
        Args:
            index: 段落索引（从1开始）
        """
        return os.path.join(self.images, f"segment_{index}.png")
    
    def cover_image(self, suffix: str) -> str:
        """
        封面图片路径
        
        Args:
            suffix: 文件名后缀（如时间戳）
        """
        return os.path.join(self.root, f"cover_{suffix}.png")
    
    # ==================== Voice 目录相关路径 ====================
    
    def opening_audio(self) -> str:
        """开场音频路径"""
        return os.path.join(self.voice, "opening.mp3")
    
    def segment_audio(self, index: int, extension: str = "mp3") -> str:
        """
        段落音频路径

        Args:
            index: 段落索引（从1开始）
            extension: 文件扩展名（mp3 或 wav）
        """
        return os.path.join(self.voice, f"voice_{index}.{extension}")
    
    def srt_subtitles(self) -> str:
        """
        SRT字幕文件路径
        """
        return os.path.join(self.voice, "字幕.srt")
    
    # ==================== 其他文件路径 ====================
    
    def final_video(self) -> str:
        """最终视频文件路径"""
        return os.path.join(self.root, "final_video.mp4")
    
    # ==================== 工具方法 ====================
    
    def ensure_dirs_exist(self) -> None:
        """确保所有必要的子目录都存在"""
        os.makedirs(self.text, exist_ok=True)
        os.makedirs(self.images, exist_ok=True)
        os.makedirs(self.voice, exist_ok=True)
    
    def segment_image_exists(self, index: int) -> bool:
        """检查指定段落的图片是否存在"""
        return os.path.exists(self.segment_image(index))
    
    def segment_audio_exists(self, index: int) -> Optional[str]:
        """
        检查指定段落的音频是否存在，返回存在的文件路径
        
        Returns:
            str: 存在的音频文件路径（wav 或 mp3）
            None: 音频文件不存在
        """
        wav_path = self.segment_audio(index, "wav")
        if os.path.exists(wav_path):
            return wav_path
        
        mp3_path = self.segment_audio(index, "mp3")
        if os.path.exists(mp3_path):
            return mp3_path
        
        return None


__all__ = ['ProjectPaths']

