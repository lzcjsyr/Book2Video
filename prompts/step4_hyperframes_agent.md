你必须只为当前单个段落生成 HyperFrames `index.html`，并写入当前工作目录。

---

## 一、系统与环境限制（硬性红线）

- **工作空间限制**：只能在当前工作目录下写出 `index.html`，不得修改 core/、text/、voice/ 或项目源码，不得处理当前段落以外的内容。
- **路径引用限制**：写出的文件必须使用当前工作目录下的相对路径 `index.html`，禁止写入 `/Users/user/...`、项目根目录或任何系统绝对路径。

## 二、HyperFrames 结构规范（HTML契约）

- **独立页面 (Standalone)**：必须生成 standalone (独立运行) 的 HyperFrames HTML 页面，绝对不能用 `<template>` 包裹根元素。
- **根容器要求**：包含一个 data-composition-id="segment" 的根 composition 容器，必须包含 `data-start="0"`。
- **参数绑定**：必须使用传入的 `durationSeconds` 作为 composition 的 `data-duration` 属性。
- **CSS选择器与ID**：根容器必须同时携带 `id="segment-root"`，编写 CSS 时必须使用 `#segment-root` 来选择根元素，不要使用 `[data-composition-id="segment"]` 等属性选择器。

## 三、文字与视觉排版规范（高可读性定制）

- **字体声明**：
  * 必须优先使用 HyperFrames 可映射的系统无衬线字体，例如 `Inter`、`Helvetica`、`Arial`。
  * 不要使用 `PingFang SC`、`Microsoft YaHei`、`Noto Sans SC` 等未声明 `@font-face` 且在系统上可能缺失的字体作为唯一声明（但可通过 fallback 机制保底：`font-family: 'Inter', 'Helvetica', 'Arial', sans-serif;`，由浏览器自动处理中文回退）。
- **极简文字与关键提炼 (Core Highlights Only)**：
  * **字要极少，字号要极大**：不要直接把长段落的内容直接搬到页面上（底部口播字幕会自动显示整句）。画面中必须精炼出核心关键词、关键数据指标、短语对比等，字数压缩率建议大于 60%。
  * 比如：把“N型硅料从每公斤300元跌到40元，跌幅超85%”精炼为“300元 ➔ 40元”以及“跌幅超85%”等关键标签，页面中只显示关键结论和高对比度大字。
  * **多用图标辅助表达**：鼓励使用简洁的 CSS 图标、SVG 矢量图或趋势指示符（如 `➔`, `▼`, `▲`）来辅助展示数据和趋势，让画面更具视觉丰富度和直观感。
- **分辨率自适应字号与间距**：
  严禁使用偏小字号，优先使用超大字体突出重点：
  
  * **当画布为 2560x1440 时**：
    - 主视觉大数字 / 百分比：280px - 420px (超大高亮)
    - 核心关键词 / 结论标签：130px - 200px (font-weight: 800)
    - 辅助说明短语：60px - 90px
    - 布局安全边距 (Margins/Padding)：160px - 240px
  
  * **当画布为 1920x1080 时**：
    - 主视觉大数字 / 百分比：210px - 315px
    - 核心关键词 / 结论标签：100px - 150px
    - 辅助说明短语：45px - 68px
    - 布局安全边距 (Margins/Padding)：120px - 180px
  
  * **当画布为 1280x720 时**：
    - 主视觉大数字 / 百分比：140px - 210px
    - 核心关键词 / 结论标签：65px - 100px
    - 辅助说明短语：30px - 45px
    - 布局安全边距 (Margins/Padding)：80px - 120px

- **底部字幕安全区（Subtitle Safe Area）**：
  * **画布最底部的 20% 空间**（Y 轴从 80% 到底部 100% 的区间，例如 1440px 高度下的底部 288px，或者 720px 高度下的底部 144px）**是绝对的零信息留白区**。
  * **严禁在该区域内出现任何可见元素**，包括但不限于：标题、卡片、图表、图标、段落正文、**脚注（Footnote/备注说明）以及任何底部的装饰线（Decorative Line）**。
  * **所有可见元素**的最下边界定位必须严格大于画布高度的 20%（例如：在 1440px 高度下，任何元素的 CSS 定位必须满足 **`bottom: 288px` 以上**；在 720px 下必须满足 **`bottom: 144px` 以上**）。
  * 该区域必须保持彻底的干净空白（仅允许纯背景色/背景渐变/微弱网格底纹自然延伸），以避免与后期叠加的口播字幕重合，确保排版信息绝不跨入字幕区域。
- **排版空间预算与布局平衡控制 (Layout Space & Balance)**：
  * **高度绝对红线**：所有可见元素堆叠的总高度（包含 padding, margin, font-size, line-height）**严禁超过画布总高度的 75%**，以留出顶边距和底部 20% 字幕区。
  * **横向分栏排版 (Split Columns)**：如果页面元素较多（例如既有标题、大数字，又有数张卡片和正文），**强烈建议使用左右/分栏布局**（例如左侧放置标题和大数字，右侧放置多张卡片和说明文字），这样可以极大缩减垂直占用高度，防止其溢出到底部字幕 safe area。
  * **防左倾/防挤压 (Horizontal Balance)**：页面布局在横向上必须饱满平衡。禁止出现所有文字、卡片、进度条均严重偏左，导致右侧出现大面积突兀空白的情况。卡片或进度条应合理铺满其容器的安全宽度，或者采用居中对齐、左右分栏、多列均分的形式，使版面视觉稳定大气。
- **内容呈现**：页面必须包含清晰可读的中文标题、关键指标或数据视觉。

## 四、动画与逻辑规范（GSAP 契约）

- **动画开发原则**：遵循“先静后动（Layout Before Animation）”原则，即先用 CSS 编写出元素在最清晰呈现时刻的静态最终布局，再用 `gsap.from()` 动画将其从隐藏或位移状态还原回来。
  - **重要警告**：使用 `gsap.from()` 动画时，**绝对不能**在 CSS 中对动画目标元素设置 `opacity: 0`！这会导致 `gsap.from` 将其从 `opacity: 0`（动画起点）还原到 CSS 的目标态 `opacity: 0`（动画终点），导致元素自始至终完全隐形（视频画面全白）。
  - **解决方案**：在 CSS 中不设置 `opacity` 或是设为默认的可见状态，让 GSAP 的 `from` 方法自动初始化并还原；如果为了避免初闪（FOUC）必须在 CSS 中使用 `opacity: 0`，则必须在 JS 中改用 `gsap.fromTo` 并显式声明终点（例如 `gsap.fromTo(target, {{ autoAlpha: 0 }}, {{ autoAlpha: 1 }})`）。
- **时间线注册**：必须创建并注册一个 paused 状态的 GSAP timeline 到全局，供渲染器外部寻迹：
  ```javascript
  window.__timelines = window.__timelines || {{}};
  const tl = gsap.timeline({{ paused: true }});
  window.__timelines.segment = tl;
  ```

---

## 五、输入参数与上下文

### 1. 内置 HyperFrames 规范与参考
{embedded_skill_bundle}

### 2. 风格预设
{style_preset}

### 3. 当前段落输入 JSON
{payload_json}

---

请根据以上所有规范与输入参数，生成最终的 `index.html`。
