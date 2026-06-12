"""
智能视频制作系统 - 中文提示词加载模块
动态从根目录 /prompts 文件夹读取 Markdown (.md) 提示词模板和 YAML (.yaml) 风格预设
"""

import os
import yaml

def _get_project_root() -> str:
    """获取项目根目录路径，不依赖 package 嵌套深度。"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def _load_prompt_file(filename: str) -> str:
    root = _get_project_root()
    path = os.path.join(root, "prompts", filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"提示词模板文件未找到: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _load_yaml_file(filename: str) -> dict:
    root = _get_project_root()
    path = os.path.join(root, "prompts", filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"预设风格配置文件未找到: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

# ================================================================================
# 动态加载提示词模板
# ================================================================================
STEP1_AGENT_PROMPT_TEMPLATE = _load_prompt_file("step1_agent.md")
STEP1_5_SEGMENT_PROMPT_TEMPLATE = _load_prompt_file("step1_5_segment.md")
keywords_extraction_prompt = _load_prompt_file("step2_keywords.md")
description_summary_system_prompt = _load_prompt_file("step2_summary.md")
STEP4_IMAGE_PROMPT_SAFETY_TEMPLATE = _load_prompt_file("step4_safety.md")
STEP4_IMAGE_DESCRIPTION_PROMPT_TEMPLATE = _load_prompt_file("step4_description.md")
STEP4_HYPERFRAMES_AGENT_PROMPT_TEMPLATE = _load_prompt_file("step4_hyperframes_agent.md")
IMAGE_PROMPT_SAFETY_TEMPLATE = STEP4_IMAGE_PROMPT_SAFETY_TEMPLATE
IMAGE_DESCRIPTION_PROMPT_TEMPLATE = STEP4_IMAGE_DESCRIPTION_PROMPT_TEMPLATE
COVER_IMAGE_PROMPT_TEMPLATE = _load_prompt_file("step6_cover.md")

# ================================================================================
# 动态加载图像与封面预设风格
# ================================================================================
STEP4_IMAGE_STYLE_PRESETS = _load_yaml_file("step4_styles.yaml")
IMAGE_STYLE_PRESETS = STEP4_IMAGE_STYLE_PRESETS
COVER_IMAGE_STYLE_PRESETS = _load_yaml_file("step6_styles.yaml")

# ================================================================================
# 提示词构造函数
# ================================================================================
def build_step1_agent_prompt(
    input_file: str,
    output_json: str,
    text_dir: str,
    skill_path: str,
    extra_requirements: str = "",
) -> str:
    """构建 Claude Agent 步骤1 生成原始文稿所需的系统提示词。"""
    extra_requirements = (extra_requirements or "").strip() or "无"
    return STEP1_AGENT_PROMPT_TEMPLATE.format(
        input_file=input_file,
        output_json=output_json,
        text_dir=text_dir,
        skill_path=skill_path,
        extra_requirements=extra_requirements,
    )

# ================================================================================
# 导出配置
# ================================================================================
__all__ = [
    'STEP1_AGENT_PROMPT_TEMPLATE',
    'STEP1_5_SEGMENT_PROMPT_TEMPLATE',
    'build_step1_agent_prompt',
    'keywords_extraction_prompt',
    'description_summary_system_prompt',
    'IMAGE_DESCRIPTION_PROMPT_TEMPLATE',
    'IMAGE_PROMPT_SAFETY_TEMPLATE',
    'IMAGE_STYLE_PRESETS',
    'STEP4_IMAGE_DESCRIPTION_PROMPT_TEMPLATE',
    'STEP4_IMAGE_PROMPT_SAFETY_TEMPLATE',
    'STEP4_IMAGE_STYLE_PRESETS',
    'STEP4_HYPERFRAMES_AGENT_PROMPT_TEMPLATE',
    'COVER_IMAGE_STYLE_PRESETS',
    'COVER_IMAGE_PROMPT_TEMPLATE'
]
