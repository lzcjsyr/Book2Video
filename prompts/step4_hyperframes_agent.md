<!-- STEP4_HYPERFRAMES_PROMPT_VERSION: 2026-06-21-layout-structure-v6 -->

你必须只为当前单个段落生成 HyperFrames `index.html`，并且必须写入指定绝对路径：`{target_index_html_path}`。

---

## 一、执行顺序

必须按顺序完成：

1. 先按“官方 HyperFrames skill 路径上下文”判断并读取相关 skills。不能只看 frontmatter，也不能凭经验生成。
2. 只基于当前段落 `content` 提炼 `visualKeywords` 与上屏文字预算。
3. 选择 1 个版式结构模板，规划阅读路径、视觉层级和动作关系。
4. 写入 standalone HyperFrames `index.html`。
5. 先做代码自检，再生成截图并读图做视觉自检。
6. 任一检查失败，必须修改 `index.html` 并重新完成相关检查。

不要跳步，不要把检查失败解释为“可以接受”后结束。

---

## 二、任务边界

- 只处理当前段落，只生成一个 standalone HyperFrames HTML 页面，不处理其他段落。
- 必须写入 `{target_index_html_path}`；不得写入系统根目录、用户家目录或其他绝对路径。
- 不得修改 core/、text/、voice/、prompts/、skills/ 或其他项目源码。
- 页面必须完全依赖输入 JSON 和本文件内代码，不依赖运行时网络数据、随机数或当前时间。
- 当前段落 JSON 包含并必须使用：`segmentIndex`、`title`、`content`、`durationSeconds`、`width`、`height`、`stylePreset`、`descriptionSummary`。
- composition 必须严格匹配 `width` x `height`；`data-duration` 必须使用传入的 `durationSeconds`。
- 画面主题必须来自当前段落 `content`；`title` 和 `descriptionSummary` 只能用于理解上下文，不能把摘要里的新句子直接搬上画面。
- 禁止依赖外部 `keywords`、`atmosphere`、`keywords.json` 或其他段落文件生成屏幕文案。

---

## 三、硬门禁

以下任一项失败，都必须先修复，不得结束任务。

### A. 文案门禁

- 写 HTML 前，必须先从当前段落 `content` 提炼 `visualKeywords`，并把 `visualKeywords` 放进画面。
- `visualKeywords.hero`：1 个主关键词或短结论，2-8 个中文字符；这是画面最大文字。
- `visualKeywords.support`：最多 1 个辅助短语，4-12 个中文字符。
- `visualKeywords.contrast`：可选，最多 2 个短词，用于左右/前后对比。
- 画面上可读中文总量最多 28 个中文字符。书名、人名、数字计入总量。
- 禁止直接展示 `content` 原句或超过 12 个中文字符的连续原文片段；`quote_focus` 也不能整句引用。
- 铺垫句、口语句、完整长句必须压缩成关键词、短判断或对比词。
- 英文装饰词不参与内容表达，默认不要使用。

### B. HyperFrames 门禁

- 根 composition 直接放在 `<body>`，绝不能用 `<template>` 包裹。
- 根容器必须是 `id="segment-root"`，同时包含 `data-composition-id="segment"`、`data-start="0"`、`data-width`、`data-height`、`data-duration`、`data-track-index`。
- CSS 选择根元素必须使用 `#segment-root`，不要用 `[data-composition-id="segment"]`。
- 必须创建 paused GSAP timeline 并注册：
  ```javascript
  window.__timelines = window.__timelines || {{}};
  const tl = gsap.timeline({{ paused: true }});
  window.__timelines.segment = tl;
  ```
- 动画必须可 seek、可重复渲染；禁止 `Date.now()`、`Math.random()`、交互事件、hover、scroll、网络请求、`fetch`、`setTimeout`、`repeat: -1`、`data-end`、`data-layer`。

### C. 字幕避让

所有前台可见元素必须且只能放在 `#content-wrapper` 内。`#content-wrapper` 外只允许放纯背景修饰层。

禁止在 `#content-wrapper` 外放任何可读文本，包括角标、页码、timecode、SEG、BOOK REVIEW、章节号、来源、小号标签。

`#content-wrapper` 必须使用以下安全样式，强制让出底部 20% 字幕区：

```css
#content-wrapper {{
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 80%;
  padding: 100px 160px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
}}
```

### D. 可读性门禁

- 最小字号：2560x1440 任何可读文字不得小于 60px、主关键词/结论 >=150px；1920x1080 >=45px / >=112px；1280x720 >=34px / >=75px。
- 深色背景上，主关键词/结论必须使用 `#fff`、`#f8f9fa` 或等效高亮色；辅助短语透明度不得低于 `rgba(..., 0.68)`；标签类文字透明度不得低于 `rgba(..., 0.55)`。
- 低于 `0.4` 透明度的颜色只能用于纯装饰线条、纹理、光效，不能用于任何汉字、数字、英文、单位或可读标签。
- 不使用负 letter-spacing；核心字号不要用 viewport units。

---

## 四、版式结构选择

必须选择且声明 1 个结构模板：`hero_verdict`、`left_list_right_verdict`、`before_after`、`number_to_conclusion`、`cause_effect`、`quote_focus`。

结构必须形成清晰阅读路径；只允许 1 个主焦点，最多 1 个副焦点；禁止信息岛、孤立数字、空半屏；相关元素必须靠近、对齐或用线/箭头连接。

---

## 五、视觉与动画要求

- 视觉风格优先遵循读取到的官方 HyperFrames skills 和下方官方风格映射；项目层面的字数、字号、透明度、字幕避让和禁用小字规则优先级更高。
- 每段只表达一个核心 insight，最多三个主数据点。
- 必须加入 2-3 层非文字视觉层，并且每层服务当前结构模板和阅读路径。
- 至少要有一个结构化图形关系，或一个随时间建立的视觉因果/对比过程；不要只生成静态大字 + 分隔线 + 淡入上移。
- 核心文字在可读时刻必须稳定、清楚；轻微镜头运动只能作用于背景层、图形层或整体舞台。

---

## 六、生成后自检

写出 `index.html` 后，必须先做代码层面检查，再生成截图；发现问题必须先修正 HTML，再继续。

### A. 代码自检

1. 运行 `npx --yes hyperframes@0.6.115 validate --json` 和 `npx --yes hyperframes@0.6.115 inspect --json --samples 15`。
3. 列出所有可读文字的 `文本 / font-size / opacity`；任一可读文字低于当前分辨率最小字号或透明度阈值，必须修复。
4. 逐项核对根尺寸、data-duration、data-start、data-track-index、禁止原句长文本、禁止小字角标；复核不存在 `Math.random`、`Date.now`、`fetch`、`setTimeout`、`repeat: -1`、真实 `<template>`、`data-end`、`data-layer`。
5. 确认所有可读文字在 `#content-wrapper` 内。

### B. 视觉自检

6. 代码自检通过后，运行 `npx --yes hyperframes@0.6.115 snapshot --frames 5`。
7. 查看 `snapshots/` 中的 PNG 关键帧，并复核：是否能明确看出所选结构模板；阅读路径是否一眼清楚，主焦点和副焦点是否明确；布局是否有遮挡、贴边、偏角落、孤立数字、空半屏或无关系的信息岛；可读文字是否足够大、足够亮；是否有 2-3 层非文字视觉层；底部 20% 字幕区是否保持干净；最后一帧是否保留稳定停留或干净退出，不能是意外黑场。
8. 如果任一检查不合格，必须修改 HTML，修复后必须重新完成代码自检、重新运行 `snapshot --frames 5` 并再次读图确认。

### C. 最终回复

最终回复必须包含以下结构化摘要，便于调用方审计：

```json
{{
  "selectedTemplate": "hero_verdict | left_list_right_verdict | before_after | number_to_conclusion | cause_effect | quote_focus",
  "visualKeywords": {{
    "hero": "",
    "support": "",
    "contrast": []
  }},
  "readableText": [],
  "readableChineseCharCount": 0,
  "durationMatched": true,
  "sizeMatched": true,
  "validateOk": true,
  "inspectOk": true,
  "snapshotReviewed": true,
  "staticAuditPassed": true,
  "knownIssues": []
}}
```

---

## 七、上下文

### 1. 官方 HyperFrames skill 路径上下文
{skill_path_context}

### 2. 官方风格映射
{style_context}

### 3. 当前段落输入 JSON
{payload_json}

---

请根据以上所有规范与输入参数，生成最终的 `index.html`。
