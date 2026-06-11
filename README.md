# 智能视频制作系统 (Book2Video)

**一键将 PDF、EPUB 等文档自动转换为带字幕、配音、配图的高质量短视频。**

---

## 🚀 快速上手

### 1. 系统要求

* Python 3.10+
* FFmpeg (视频处理必需，请确保系统已安装并添加到环境变量)

### 2. 安装步骤

```bash
# 1. 安装 Python 依赖
pip install -e .

# 2. 安装 Remotion 开场视频依赖（可选）
cd core/infra/remotion/app && npm ci && cd ../../../..
```

*提示：macOS 用户可直接运行 `./scripts/install_macos.sh`，Windows 用户运行 `powershell -ExecutionPolicy Bypass -File scripts/install_windows.ps1` 进行一键环境安装与测试。*

### 3. 配置密钥

复制 `.env.example` 为 `.env` 并填写你所需要用到的 API 密钥：

* **大模型服务** (如 MiMo, OpenRouter, SiliconFlow)
* **语音合成** (如 字节跳动 TTS)
* **图像/画面生成** (如 火山引擎, Google Cloud Vertex AI，或 HyperFrames 动态画面)

### 4. 运行制作

将待处理的文档（PDF、EPUB、DOCX、MOBI 等）放入 `input/` 文件夹下，然后运行：

```bash
python start.py
```

根据终端提示操作：选择**新建项目** -> **选择你的文档** -> 推荐新手选择**全自动模式**，即可一键完成制作。

---

## 💡 核心工作流

系统采用模块化设计，将长文档转化为短视频分为以下核心步骤：

* **步骤 1 内容生成**：AI 提炼文档核心内容为适合短视频的篇幅。
* **步骤 1.5 脚本分段**：智能分段并生成每段对应的口播文案。
* **步骤 2 要点提取**：分析语义，提取每段画面的视觉描述或关键词。
* **步骤 3 语音合成**：采用高品质 TTS 引擎生成拟真配音及 SRT 字幕，为画面生成提供精确时长。
* **步骤 4 画面生成**：生成静态段落图片，或根据音频时长渲染 HyperFrames 动态画面，并渲染精美开场视频。
* **步骤 5 视频合成**：混合开场视频、转场画面、配音、字幕及背景音乐，导出 MP4 视频。
* **步骤 6 封面生成**：自动生成适配社交媒体的竖版封面图。

---

## 🎛️ 使用模式

运行 `python start.py` 后可选择：

* **全自动模式（推荐）**：一键跑通所有流程，坐等视频产出。
* **分步处理模式**：每一步完成后，支持编辑中间生成的 Word 脚本（如 `raw.docx`、`script.docx`）或更换图片风格，精细化定制视频。
* **项目管理模式**：打开现有项目，从任意中断的步骤继续执行或重新制作特定部分。

### 第四步画面模式

`config.yaml` 的 `step4.visual_mode` 控制画面生成方式：

```yaml
step4:
  visual_mode: static_image       # 默认：生成 images/segment_i.png
  # visual_mode: hyperframes_agent # 动态：生成 images/segment_i.mp4
  # visual_mode: mixed             # 混合：按每段 visualizer 选择图片或 HyperFrames
  hyperframes_style_preset: data_driven
```

选择 `hyperframes_agent` 时，系统会先使用步骤 3 已生成的真实音频时长，再调用 Claude Agent 按项目内置 HyperFrames 规范生成动态 HTML 并渲染为分段视频。

选择 `mixed` 时，系统读取 `text/script.json` 中每段的 `visualizer` 字段：`image` 生成 `segment_i.png`，`hyper` 生成 `segment_i.mp4`。步骤 1.5 会默认把每段 `visualizer` 写为 `image`；需要动态画面的段落可手动改为 `hyper`。混合模式下两类段落会分组并行生成。

---

## 🗂️ 项目目录与模块说明

为了方便你进行定制开发、效果微调或查找对应资源，以下是根目录下各主要模块的功能与职责：

* 📂 **`core/`** — **系统核心代码库**。
* 📂 **`prompts/`** — **大模型提示词与风格模板**。包含视频生成过程中，总结段落、提取视觉关键词、润色口播文案所用的核心 Prompt 预设。如需调整文案生成风格或添加自定义艺术风格，在此修改。
* 📂 **`skills/`** — **自动化技能扩展**。`skills/step1/` 存放第一步写作 Agent skills；`skills/step4/` 存放第四步动态画面 skills，目前包括 `hyperframes/`、`hyperframes-cli/`、`gsap/` 和 `css-animations/`。
* 📂 **`scripts/`** — **系统管理脚本**。提供 macOS/Linux 以及 Windows 环境下一键环境安装、依赖检验以及完整功能诊断的脚本。
* 📂 **`input/`** — **待处理文档输入目录**。放入需要转为视频的 PDF、EPUB、DOCX 等原始电子书/文档。
* 📂 **`output/`** — **项目生成输出目录**。每一次视频制作都将在此按“项目名_时间戳”生成独立的文件夹，包含视频和全部中间缓存资源。
* 📂 **`music/`** — **背景音乐储备库**。存放合成视频时备选的 MP3 音频，可在配置文件中自由指定。
* 📄 **`start.py`** — **系统控制台主入口**。直接通过 `python start.py` 即可进入交互式流程引导。
* 📄 **`pyproject.toml`** — **Python 依赖包配置**。规范了全部核心依赖组件及版本信息。
* 📄 **`config.yaml`** — **系统运行全局配置文件**（复制自 `config.example.yaml`）。可调节每一步的视频分辨率、生图模式、音色语速以及模型选型等所有个性化配置。

---

## 📁 制作产出结构

视频制作完成后，在 `output/《你的文档标题》_MMDD_HHMM/` 目录下将产生以下结构，供随时审阅或二次重制：

* `final_video.mp4` — **最终合成的高清短视频文件**
* `images/` — 各分段配图及精美的 Remotion 开场动画（`opening.mp4`）
* `voice/` — 对应段落的高保真配音 MP3 及字幕文件（`字幕.srt`）
* `text/` — 中间过程中 AI 生成并导出的 Word 文案脚本与段落总结文件（可供编辑修正后实现精准二次重制）
