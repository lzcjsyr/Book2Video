你必须只为当前单个段落生成 HyperFrames `index.html`，并写入当前工作目录。

硬性限制：

- 不得修改 core/、text/、voice/ 或项目源码。
- 不得写出当前工作目录以外的文件。
- 文件路径必须使用当前工作目录下的相对路径 `index.html`，禁止写入 `/Users/user/...`、项目根目录或任何绝对路径。
- 不得处理其他段落。
- 必须生成 standalone HyperFrames HTML，不能用 template 包裹根 composition。
- 必须使用传入的 durationSeconds 作为 composition 的 data-duration。
- 根 composition 必须包含 `data-start="0"`。
- 根 composition 必须同时带 `id="segment-root"`，CSS 只使用 `#segment-root` 选择根元素，不要使用 `[data-composition-id="segment"]` 选择器。
- 字体必须优先使用 HyperFrames 可映射字体，例如 `Inter`、`Helvetica`、`Arial`；不要使用 `PingFang SC`、`Microsoft YaHei`、`Noto Sans SC` 等未声明 `@font-face` 的字体。

内置 HyperFrames 规范：
{embedded_skill_bundle}

风格预设：{style_preset}

段落输入 JSON：
{payload_json}

请生成 `index.html`。页面必须包含：

- 一个 data-composition-id="segment" 的根 composition
- data-start="0"、data-width、data-height、data-duration、data-track-index
- id="segment-root"，并用 #segment-root 写根元素 CSS
- 可读中文标题/内容/数据视觉
- GSAP paused timeline 并注册到 window.__timelines.segment
