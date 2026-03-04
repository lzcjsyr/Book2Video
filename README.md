# 智能视频制作系统

**将任何文档自动转换为专业短视频解说**

一键将PDF、EPUB等文档智能转换为带字幕、配音、配图的高质量短视频，专为知识类内容创作设计。

## 🚀 快速上手

### 系统要求

- **Python 3.13+**（推荐）
- **FFmpeg**（视频处理必需）
- 支持 macOS、Windows、Linux

### 第一步：安装配置

```bash
# 1. 安装 FFmpeg（视频合成必需的系统工具）
# macOS
brew install ffmpeg

# Windows (使用 Chocolatey)
choco install ffmpeg
# 或从 https://ffmpeg.org/download.html 下载

# Linux (Ubuntu/Debian)
sudo apt install ffmpeg

# 验证安装
ffmpeg -version

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 配置API密钥（复制并编辑 .env 文件）
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥

```

### 第二步：准备文档

```bash
# 将要制作视频的文档放入 input 文件夹
# 支持格式：PDF、EPUB、MOBI、DOCX等
cp "你的文档.pdf" input/
```

### 第三步：开始制作

```bash
# 启动系统
python -m cli

# 然后按提示操作：
# 1. 选择"新建项目"
# 2. 选择你的文档文件
# 3. 选择"全自动模式"（推荐新手）
# 等待5-15分钟，视频制作完成！
```

### 输出结果

制作完成后，在 `output/项目名称_时间/` 文件夹中查看：

- `final_video.mp4` - 最终视频文件
- `images/` - 生成的配图
- `voice/` - 语音文件和字幕
- `text/` - 文本内容（可编辑重制）

## 💡 核心工作流程

系统采用**7步智能流程**，将长篇文档转换为短视频：

### 步骤1：智能总结 - 文档压缩

- **输入**：任意长度的文档文件（PDF、EPUB、DOCX等）
- **处理**：AI模型智能提取核心内容并压缩为适合视频的篇幅（默认2000字）
- **输出**：标题、开场金句、压缩正文
- **可编辑**：`raw.docx` 可手动编辑后重新切分

### 步骤1.5：脚本分段 - 段落切分

- **输入**：总结后的文本内容
- **处理**：支持手动切分（按换行符）或自动切分（智能均分为指定段数）
- **输出**：带时长预估的分段脚本（默认25段）
- **可编辑**：`script.docx` 可调整分段和文本后重新生成

### 步骤2：要点提取 - 视觉关键词

- **输入**：分段脚本数据
- **处理**：为每段提取视觉关键词和氛围词（keywords模式）或生成描述摘要（description模式）
- **输出**：`keywords.json` 或 `mini_summary.json`

### 步骤3：图像生成 - AI配图

- **输入**：脚本 + 关键词/描述数据
- **处理**：AI图像生成模型为每段创建匹配的配图，支持多种风格预设
- **输出**：开场图片 + 各段配图（PNG格式）
- **支持**：指定段落重新生成、切换风格

### 步骤4：语音合成 - TTS配音

- **输入**：分段脚本文本
- **处理**：调用TTS引擎合成语音，支持语速、音量调节
- **输出**：各段语音文件 + SRT字幕文件
- **支持**：多种音色选择、指定段落重新生成

### 步骤5：视频合成 - 最终导出

- **输入**：图像、语音、字幕、背景音乐
- **处理**：MoviePy合成视频，添加字幕特效和背景音乐
- **输出**：高质量mp4视频文件

### 步骤6：封面生成 - 宣传素材

- **输入**：项目标题和内容信息
- **处理**：AI生成竖版封面图，适用于社交媒体分享
- **输出**：高清封面图片（可生成多张备选）
- **特点**：独立步骤，可随时生成，不影响视频制作流程

## 🎛️ 使用模式

### 模式一：全自动模式（推荐新手）

```bash
python -m cli
# 选择"全自动模式" → 一键完成所有步骤
```

### 模式二：分步处理模式（推荐定制）

```bash
python -m cli
# 选择"分步处理" → 每步完成可编辑再继续
```

**分步模式优势：**

- 步骤1后：可编辑 `raw.docx` 调整总结内容
- 步骤1.5后：可编辑 `script.docx` 调整分段和文本
- 步骤2后：可重新生成关键词或切换配图模式
- 步骤3后：可重跑图像生成尝试不同风格或重新生成指定段落
- 步骤4后：可重跑语音合成尝试不同音色或调整语速
- 步骤5后：可调整参数重新合成视频
- 步骤6：可随时生成封面图，支持多张备选

### 模式三：项目管理模式

```bash
python -m cli
# 选择"打开现有项目" → 继续未完成的项目或重制特定步骤
```

## ⚙️ 关键参数配置

在 `core/config.py` 顶部的用户配置区域直接修改参数值。**参数已按7步工作流程组织**，清晰对应各步骤：

```python
# ==================== 全局配置 ====================
OPENING_QUOTE = True                                   # 开场金句开关（影响步骤3+5）

# ==================== 📝 步骤1：智能总结 ====================
LLM_SERVER_STEP1 = "siliconflow"                         # 步骤1 LLM供应商
LLM_MODEL_STEP1 = "moonshotai/Kimi-K2-Instruct-0905"   # 步骤1 LLM模型
TARGET_LENGTH = 2000                                    # 目标字数 (500-5000)
LLM_TEMPERATURE_SCRIPT = 0.7                            # 生成随机性 (0-1)

# ==================== ✂️ 步骤1.5：脚本分段 ====================
NUM_SEGMENTS = 25                                       # 视频分段数量 (5-50)

# ==================== 🔍 步骤2：要点提取 ====================
LLM_SERVER_STEP2 = "siliconflow"                         # 步骤2 LLM供应商
LLM_MODEL_STEP2 = "moonshotai/Kimi-K2-Instruct-0905"   # 步骤2 LLM模型
IMAGES_METHOD = "description"                          # 配图方式: keywords/description
LLM_TEMPERATURE_KEYWORDS = 0.5                          # 提取随机性 (0-1)

# ==================== 🎨 步骤3：图像生成 ====================
IMAGE_SERVER = "doubao"                                 # 图像生成供应商: doubao/siliconflow/google
IMAGE_SIZE = "2560x1440"                               # 图像尺寸 (16:9 横屏)
IMAGE_MODEL = "doubao-seedream-4-0-250828"             # 图像生成模型
IMAGE_STYLE_PRESET = "style01"                         # 段落图像风格
OPENING_IMAGE_STYLE = "des01"                          # 开场图像风格
MAX_CONCURRENT_IMAGE_GENERATION = 3                    # 并发数

# ==================== 🎙️ 步骤4：语音合成 ====================
VOICE = "zh_male_yuanboxiaoshu_moon_bigtts"            # 语音音色
SPEED_RATIO = 1.2                                      # 语速调节 (0.8-2.0)
LOUDNESS_RATIO = 1.0                                   # 音量调节 (0.5-2.0)
MAX_CONCURRENT_VOICE_SYNTHESIS = 5                     # 并发数

# ==================== 🎬 步骤5：视频合成 ====================
VIDEO_SIZE = "1280x720"                                # 视频导出尺寸
ENABLE_SUBTITLES = True                                # 是否启用字幕
BGM_FILENAME = "Far Away.mp3"                          # 背景音乐文件名
BGM_DEFAULT_VOLUME = 0.18                              # BGM音量
NARRATION_DEFAULT_VOLUME = 2.0                         # 口播音量
# 更多视频参数: 字幕样式、时间效果、音频闪避等（见 core/config.py）

# ==================== 🖼️ 步骤6：封面生成 ====================
COVER_IMAGE_SIZE = "2250x3000"                         # 封面尺寸 (竖版3:4)
COVER_IMAGE_SERVER = "doubao"                           # 封面供应商: doubao/siliconflow/google
COVER_IMAGE_MODEL = "doubao-seedream-4-0-250828"       # 封面模型
COVER_IMAGE_STYLE = "cover01"                          # 封面风格
COVER_IMAGE_COUNT = 1                                  # 生成数量
```

> 💡 **提示**：参数按工作流程组织，每个步骤的参数一目了然。修改时只需关注对应步骤即可。

## 🎨 视频尺寸选择

| 尺寸      | 比例 | 适用场景         |
| --------- | ---- | ---------------- |
| 1280x720  | 16:9 | YouTube、B站横屏 |
| 720x1280  | 9:16 | 抖音、快手竖屏   |
| 1024x1024 | 1:1  | 微信视频号       |
| 864x1152  | 3:4  | 小红书竖屏       |

## 🎭 图像风格预设

| 风格代码 | 风格名称 | 视觉特点               |
| -------- | -------- | ---------------------- |
| style01  | 概念极简 | 简洁现代，突出重点     |
| style02  | 俯视古典 | 经典构图，文艺气质     |
| style05  | 综合平衡 | 适用性广，推荐默认     |
| style08  | 科技未来 | 科幻感强，适合技术内容 |

## 📁 必需的API密钥

在 `.env` 文件中配置以下密钥：

```env
# LLM服务（至少配置一个）
OPENROUTER_API_KEY=your_key      # 推荐，模型选择多
SILICONFLOW_KEY=your_key         # 备选方案

# 图像生成（至少配置一个）
SEEDREAM_API_KEY=your_key        # 豆包图像生成
SILICONFLOW_KEY=your_key         # 硅基流动图像生成
GOOGLE_CLOUD_API_KEY=your_key    # Google Vertex AI 生图（单一配置）
# Google图像并发上限（可选，默认2，仅 image_server=google 生效）
# GOOGLE_MAX_CONCURRENT_IMAGE_GENERATION=2

# 语音合成（必需）
BYTEDANCE_TTS_APPID=your_appid   # 豆包语音
BYTEDANCE_TTS_ACCESS_TOKEN=your_token
```

## 🛠️ 高级功能

### 独立工具

```bash
# 文档统计分析
python tools/check_text_stats.py

# 单独测试媒体生成
python tools/gen_single_media.py
```

### 项目管理

- **断点续制**：意外中断可从任意步骤继续
- **重制优化**：可重新执行特定步骤优化效果
- **批量处理**：同时处理多个文档项目
- **文件编辑**：支持编辑中间产物后重新处理

## 🧱 Core代码结构（重构后）

`core` 采用“业务流程 + 分层”结构，稳定入口保持不变：

- `core/pipeline.py`：统一流程入口（兼容层，保留原有函数签名）
- `core/config.py`：用户配置入口
- `core/prompts.py`：提示词与风格预设单一来源
- `core/generation_config.py`：生成参数数据结构

内部实现按层组织：

- `core/application/`：编排层（workflow/service/step_runner/steps）
- `core/domain/`：业务能力（document/script/media/video）
- `core/infra/`：外部适配（ai/storage/jobs/security）
- `core/shared/`：通用能力（logger/errors/retry/file/json）

详细说明见 `core/ARCHITECTURE.md`。

## 🏗️ 输出文件结构

```
output/
└── 《你的文档标题》_MMDD_HHMM/
    ├── final_video.mp4          # 🎬 最终视频
    ├── images/
    │   ├── opening.png          # 开场图片
    │   └── segment_1.png        # 各段配图
    ├── voice/
    │   ├── opening.wav          # 开场语音
    │   ├── voice_1.wav          # 各段语音
    │   └── 项目名_subtitles.srt  # 字幕文件
    └── text/
        ├── raw.json/.docx       # 总结内容（可编辑）
        ├── script.json/.docx    # 分段脚本（可编辑）
        └── keywords.json        # 关键词数据
```

## ❓ 常见问题

**Q: 视频制作需要多长时间？**
A: 通常5-15分钟，取决于文档长度和API响应速度。

**Q: 支持哪些文档格式？**
A: PDF、EPUB、MOBI、DOCX、TXT等主流格式。

**Q: 可以自定义背景音乐吗？**
A: 可以，将mp3文件放入 `music/` 文件夹，在参数中指定文件名。

**Q: 如何调整视频内容？**
A: 使用分步模式，每步生成的docx文件都可编辑后重新处理。

**Q: API费用大概多少？**
A: 主要取决于图片数量，制作一个5分钟视频的总成本约7元人民币。

## 🔧 故障排除

1. **FFmpeg 未安装**：
   - 错误信息：`未找到FFmpeg，无法执行口播变速`
   - 解决方案：按照上述说明安装 FFmpeg 并验证 `ffmpeg -version` 可用

2. **检查依赖与路径**：确认已安装依赖，项目根目录存在 `core/config.py`、`core/`、`cli/`。

3. **日志查看**：`cli/cli.log` 或控制台输出

4. **网络问题**：确保API服务可访问

5. **依赖问题**：重新运行 `pip install -r requirements.txt`

---

**开始你的智能视频创作之旅！** 🚀

将知识转化为视频，让AI为你的内容赋能。
