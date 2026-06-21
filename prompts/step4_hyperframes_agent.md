<!-- STEP4_HYPERFRAMES_PROMPT_VERSION: 2026-06-21-layout-structure-v6 -->

你必须只为当前单个段落生成 HyperFrames `index.html`，并且必须将其写入指定的绝对路径：`{target_index_html_path}`。

---

## 一、任务边界

- 只处理当前段落，只生成一个 standalone HyperFrames HTML 页面，不处理其他段落。
- 必须写入 `{target_index_html_path}`；不得写入系统根目录、用户家目录或其他绝对路径。
- 不得修改 core/、text/、voice/、prompts/、skills/ 或其他项目源码。
- 调用方会把该页面渲染为当前段落的 `segment_i.mp4`，所以页面必须完全依赖输入 JSON 和本文件内代码，不依赖运行时网络数据、随机数或当前时间。

## 二、输入契约

当前段落 JSON 包含并必须使用这些变量：`segmentIndex`、`title`、`content`、`durationSeconds`、`width`、`height`、`stylePreset`、`descriptionSummary`。

- composition 必须严格匹配 `width` x `height`。
- composition 的 `data-duration` 必须使用传入的 `durationSeconds`。
- 画面主题必须来自当前段落 `content`；`title` 和 `descriptionSummary` 只能用来理解上下文，不能把摘要里的新句子直接搬上画面。
- 禁止依赖外部 `keywords`、`atmosphere`、`keywords.json` 或其他段落文件生成屏幕文案。第四步必须由 Agent 根据当前段落 `content` 自己提炼画面关键词。

## 三、屏幕文案提炼硬规则

在写 HTML 前，必须先在心里完成这一步：从当前段落 `content` 提炼 `visualKeywords`，再把 `visualKeywords` 放进画面。不要把这个分析写入文件。

- `visualKeywords.hero`：1 个主关键词或短结论，2-8 个中文字符；这是画面最大文字。
- `visualKeywords.support`：最多 1 个辅助短语，4-12 个中文字符；只在确实需要补充逻辑时使用。
- `visualKeywords.contrast`：可选，最多 2 个短词，用于左右/前后对比。
- 画面上禁止直接展示 `content` 原句或超过 12 个中文字符的连续原文片段。
- 画面上可读中文总量最多 28 个中文字符。书名、人名、数字计入总量。
- 如果当前段落是铺垫句、口语句或完整长句，也必须压缩成关键词、短判断或对比词，而不是整句拆行。
- 英文装饰词不参与内容表达，默认不要使用。

## 四、版式结构选择

写 HTML 前必须先选择一个结构模板，并让所有可读元素服务这个结构。不要自由散放元素。

- `hero_verdict`：一个大结论 + 一个辅助短语；适合判断、转折、金句。
- `left_list_right_verdict`：左侧 2-3 个原因/对象，右侧一个结论/数字；两侧必须用线条、箭头、对齐或色彩建立关系。
- `before_after`：左右或上下对比；两侧都必须有信息，不能一侧空着。
- `number_to_conclusion`：大数字/年份/比例 + 明确结论；数字必须靠近或指向结论。
- `cause_effect`：原因 -> 结果；必须有箭头、流向线或阶梯。
- `quote_focus`：书名/人物/短金句；只保留必要署名。

结构硬规则：

- 画面必须有清晰阅读路径：先看什么、再看什么、最后得出什么。
- 只允许 1 个主焦点，最多 1 个副焦点；禁止多个互不相连的信息岛。
- 大留白必须服务主焦点；split frame 不能只填一侧。
- 相关元素必须靠近、对齐或用线/箭头连接；数字不能孤立在角落。

## 五、HyperFrames 结构硬规则

- 生成 standalone 页面，根 composition 直接放在 `<body>`，绝不能用 `<template>` 包裹。
- 根容器必须是 `id="segment-root"`，同时包含 `data-composition-id="segment"`、`data-start="0"`、`data-width`、`data-height`、`data-duration`、`data-track-index`。
- CSS 选择根元素时必须使用 `#segment-root`，不要用 `[data-composition-id="segment"]`。
- 必须创建 paused GSAP timeline 并注册：
  ```javascript
  window.__timelines = window.__timelines || {{}};
  const tl = gsap.timeline({{ paused: true }});
  window.__timelines.segment = tl;
  ```

## 六、字幕避让与安全容器

所有前台可见元素（标题、文本、卡片、图表、标签、数字）必须且只能放在 `#content-wrapper` 内。`#content-wrapper` 外只允许放纯背景修饰层。

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

## 七、项目视觉方向

默认做“现代中文商业/财经/报告/书评讲解”风格：高对比、清晰克制、数据叙事强、适合 3-5 秒内看懂。画面要比静态信息卡更有层次和镜头感：用动效揭示论证结构，用背景、图形、色块、线条、纹理和空间层级承托主题；丰富性必须服务阅读路径，不做无意义装饰堆叠。

- 避免 web-dashboard 式拥挤、小字标签、密集坐标轴、饼图和过多说明文字。
- 优先使用大数字、对比块、进度条、简洁卡片、时间线、金句框、左右/前后对比。
- 每段只表达一个核心 insight，最多三个主数据点。
- 数据数字使用 `font-variant-numeric: tabular-nums`。
- 趋势可用高度、宽度、透明度或位置变化表达；对比用左右、上下或 before/after 结构。
- 必须加入 2-3 层非文字视觉层，例如：底层渐变/纸纹/颗粒，中层几何块/地图式区域/时间轴/关系线，前景强调框/高亮条/扫描线。每层都要与当前段落的结构模板有关，不能只是随意加光斑。
- 可以使用更明确的场景化隐喻：制度/权力用框架、门槛、层级；危机/断裂用裂缝、切面、警戒线；增长/扩散用流线、节点、阶梯；历史/书评用档案纸纹、印章式色块、章节分割线。隐喻只能用图形和材质表达，不能增加无关文字。
- 允许轻微镜头运动：整体背景慢推、视差位移、聚焦缩放、分层滑入、局部高亮扫过。运动幅度要克制，不能造成文字晃动、模糊或读不清。
- 不要只生成静态大字 + 分隔线 + 淡入上移；至少要有一个结构化图形关系，或一个随时间建立的视觉因果/对比过程。
- `stylePreset` 是用户选择的业务风格 ID。视觉语言必须优先遵循下面注入的官方 HyperFrames 风格映射，不要自行发明另一套风格体系。
- 官方风格只提供色彩、质感、动效方向；项目层面的可读性规则优先级更高。即使官方示例包含小号元信息、registration marks、monospace metadata，本项目也禁止生成可读小字。

## 八、版式与中文排版安全

- 每页最多展示 1-2 个核心信息块；`#content-wrapper` 内垂直方向最多 2 个主要 block。
- 多栏、并排对比、数据卡片必须用 Flex/Grid 和明确 `gap`，禁止用 `position:absolute; left: ...` 排列列项。
- 长句（超过 8 个中文字符）不要和数据卡片左右并排；应作为通栏放在数据上方或下方。
- 10 字以内短语必须 `white-space: nowrap`。长句必须按中文语义手动 `<br>` 分行，不要任由浏览器拆词。
- 股票代码、公司编号、专有 ID 必须作为不可拆分整体，不能拆成多个元素或大小字混排。
- 大数字和单位/小字并排时用 Flex 且 `align-items: baseline`。
- 大数字或百分比字号超过 120px 时，不要放进固定宽高盒子；用 `auto` 尺寸和 padding 自然撑开。
- 固定尺寸卡片内文字必须留足边距：标题约 60-85px，说明约 30-45px，文字占用不要超过可用宽度 75%。
- 字体优先用可映射系统无衬线：`font-family: 'Inter', 'Helvetica', 'Arial', sans-serif;`。不要把 `PingFang SC`、`Microsoft YaHei`、`Noto Sans SC` 作为唯一字体声明。
- 不使用负 letter-spacing；核心字号不要用 viewport units。
- 禁止生成可读小字、角标、timecode、SEG 标记、BOOK REVIEW 标签、来源标签、装饰性英文元信息。
- 所有可读文字必须清楚服务当前段落 insight；纯装饰只能用线条、色块、纹理、形状，不能用文字。
- 所有可读文字必须高对比、易读。禁止把承载信息的文字做成低透明度装饰效果。
- 深色背景上的可读文字：主关键词/结论必须使用 `#fff`、`#f8f9fa` 或等效高亮色；辅助短语透明度不得低于 `rgba(..., 0.68)`；标签类文字透明度不得低于 `rgba(..., 0.55)`。
- 浅色背景上的可读文字必须使用接近黑色或深品牌色，不能用浅灰低对比文字。
- 低于 `0.4` 透明度的颜色只能用于纯装饰线条、纹理、光效，不能用于任何汉字、数字、英文、单位或可读标签。

硬性最小字号：

- 2560x1440：任何可读文字不得小于 60px；主关键词/结论不得小于 150px。
- 1920x1080：任何可读文字不得小于 45px；主关键词/结论不得小于 112px。
- 1280x720：任何可读文字不得小于 34px；主关键词/结论不得小于 75px。

建议字号：

- 2560x1440：大数字 280-420px，关键词/结论 130-200px，辅助短语 60-90px。
- 1920x1080：大数字 210-315px，关键词/结论 100-150px，辅助短语 45-68px。
- 1280x720：大数字 140-210px，关键词/结论 65-100px，辅助短语 30-45px。

## 九、动画规则

- 先写最清晰呈现时刻的静态布局，再加动画；CSS 最终位置是地面真值。
- 用 `durationSeconds` 控制总时长，最后 0.25-0.5 秒保留稳定停留或干净退出。
- 相关元素错峰 0.1-0.2 秒进入，避免所有元素同时出现。
- 至少 2 个元素必须有持续或分阶段变化，例如：关系线绘制、数值条增长、对比块推移、背景视差慢推、高亮扫过、卡片层级展开。不要让所有动画都停留在开头 1 秒内。
- 主焦点出现后应有一个“建立关系”的动作：箭头画出、两侧靠近/分离、旧词被覆盖、新结论抬升、时间线推进、框架收束等。这个动作要帮助观众理解段落逻辑。
- 允许使用轻微镜头运动，但只能作用于背景层、图形层或整体舞台的低幅度 transform；核心文字在可读时刻必须稳定。
- 使用 `gsap.from()` 时，CSS 中不要给目标元素设置 `opacity: 0`；需要初始隐藏时用 `gsap.fromTo()` 显式写终点。
- 动画必须可 seek、可重复渲染；不要用 `Date.now()`、`Math.random()`、交互事件、hover、scroll 或网络请求驱动关键画面。

## 十、生成后自检

写出 `index.html` 后，必须先做代码层面检查，再生成截图；发现问题必须先修正 HTML，再继续。

### A. 代码自检

1. 运行 `npx --yes hyperframes@0.6.115 validate --json`，检查运行错误、网络错误和文字对比度问题。
2. 运行 `npx --yes hyperframes@0.6.115 inspect --json --samples 15`，检查文字溢出、裁切、越界和布局逃逸。
3. 做代码层面检查：列出所有可读文字的 `文本 / font-size / opacity`；任一可读文字低于当前分辨率最小字号或透明度阈值，必须修复；逐项核对根尺寸、data-duration、data-start、data-track-index、禁止原句长文本、禁止小字角标。

### B. 视觉自检

4. 代码自检通过后，运行 `npx --yes hyperframes@0.6.115 snapshot --frames 5`，生成关键帧截图。
5. 使用可用的读图能力查看 `snapshots/` 中的 PNG 关键帧，并用视觉判断复核：
   - 是否能明确看出所选结构模板；
   - 阅读路径是否一眼清楚，主焦点和副焦点是否明确；
   - 必须重点检查布局结构是否合理：画面重心是否稳定，主体是否过度挤在角落或单侧，左右/上下空间是否有明确分工，留白是否服务主焦点而不是形成空半屏；
   - 相关元素是否靠近、对齐或连接，是否存在孤立数字、空半屏或无关系的信息岛；
   - 排版是否清楚、稳定、没有遮挡或贴边；
   - 可读文字是否足够大、足够亮，辅助文字是否满足对比度要求；
   - 画面是否只表达当前段落的核心 insight，没有把原句长句搬上屏；
   - 视觉风格是否符合官方风格映射，并且有必要的强调色/层次，不单调、不杂乱；
   - 是否有 2-3 层非文字视觉层，且至少 2 个元素在时间线上有持续或分阶段变化；
   - 是否避免了“静态大字 + 分隔线 + 淡入上移”的单一卡片感；
   - 底部 20% 字幕区是否保持干净。
6. 如果任一代码自检或视觉自检不合格，必须修改 `index.html`，修复后必须重新完成代码自检、重新运行 `snapshot --frames 5` 并再次读图确认；确认无问题后才能结束。最终回复中简要说明检查结果。

---

## 十一、上下文

### 1. 官方/内置 HyperFrames 规范与参考
{embedded_skill_bundle}

### 2. 官方风格映射
{style_context}

### 3. 当前段落输入 JSON
{payload_json}

---

请根据以上所有规范与输入参数，生成最终的 `index.html`。
