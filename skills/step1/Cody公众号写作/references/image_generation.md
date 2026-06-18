# HTML 生图指南：手机端高可读性卡片设计规范

在微信公众号等移动端（手机屏幕）阅读场景中，长篇的纯文字极易造成视觉疲劳。通过 HTML 编写极简高质感卡片并进行截屏生图，其核心目的是**突出关键逻辑、呈现核心金句、展示强烈对比，从而瞬间抓住读者眼球**。

本指南提供了一套明确的量化指标和 HTML/CSS 设计模板，以确保 AI 能够精准执行「字数极少、字体极大、逻辑极清」的原则，交付极具高级感和视觉震撼力的图片。

**图片密度规则**：文章配图按 **400字/张** 的比例规划。一篇 2500 字的文章应配约 6 张图，3000 字配 7-8 张。写作前先预估总字数，除以 400 向上取整，得出应产出图片数量，再在草稿中标记每张图的插入节点。

---

## 1. 核心量化指标（硬性红线）

为了防止 AI 生成信息密集、排版混乱、或是在手机屏幕上缩小后根本看不清的图片，必须严格遵守以下量化规则：

| 维度 | 硬性指标规范 | 备注说明 |
| :--- | :--- | :--- |
| **画布比例** | **16:9 横图**，固定分辨率建议为 **`960px * 540px`** | 适配手机窄屏的横向通栏展示，保持一致的视觉节奏。 |
| **总字数上限** | 全卡片所有字符（含水印、标签）**严格限制在 35 个汉字以内** | 超过 35 个字立刻按「信息过载」判定为不合规。 |
| **主标题/金句字数**| 核心主文案首选 **10-18 个汉字**（最长不得超过 20 个字） | 一句话必须能在 1 秒内读完。 |
| **文本总行数** | **最多 3 行**（包括标题和副标题/说明） | 严禁出现段落排版，只允许出现单句或短语。 |
| **字号分级** | **主标题/金句**：`56px - 72px`（`3.5rem - 4.5rem`），加粗<br>**副标题/说明**：`36px - 44px`（`2.25rem - 2.75rem`）<br>**品牌/水印/标签**：`24px - 28px`（`1.5rem - 1.75rem`） | 绝对禁止使用任何小于 `24px` 的字号，以防缩小后不可读。 |
| **卡片内边距** | 卡片内部 padding **40px - 50px**，卡片在画布内的外边距控制在 **20px - 30px** | 卡片应占据画布的主体面积，边框和留白占比不超过 15%。 |
| **行高与间距** | 行高限制在 **`1.4 - 1.6`** | 保证大字在折行时绝对不重叠，文本四周留出呼吸感。 |

> **设计原则**：卡片内容区（文字所在的区域）应占据画布面积的 70% 以上。边框、装饰元素、品牌标签等非内容元素合计不应超过 30% 的视觉权重。上一次的卡片设计（840px 卡在 960px 画布中、padding 60px 80px）边框和留白占比过高，新版必须压缩。

---

## 2. 视觉美学规范

Cody 叩底的品牌调性是**专业、前沿、带有一点科技感的活人表达**。因此生图设计统一采用**暗黑极简主义（Dark Minimalism）**与**霓虹渐变（Neon Gradients）**的结合。

*   **背景色 (Backgrounds)**：使用高质感的深蓝黑（如 `#090D16`）或纯炭黑（如 `#0E0E10`），不建议使用纯白色，除非是极简学术风对比卡片。
*   **强调色 (Highlights)**：使用高饱和度、高对比度的渐变色作为视觉焦点（如文字渐变或边框微光）：
    *   *紫粉渐变*：`linear-gradient(135deg, #A855F7, #EC4899)` (极佳的现代科技感)
    *   *青绿渐变*：`linear-gradient(135deg, #00F2FE, #4FACFE)` (清新利落)
    *   *日落橙黄*：`linear-gradient(135deg, #FF6B00, #FFA800)` (温暖且极具警示感)
*   **质感元素 (Elements)**：使用微弱的半透明边框（如 `border: 1px solid rgba(255, 255, 255, 0.08)`）和微妙的阴影，制造卡片悬浮和微弱的毛玻璃感。圆弧不要太大（`border-radius: 12px - 16px`），避免占据过多视觉面积。
*   **系统字体 (Fonts)**：统一使用系统原生无衬线字体，无需外链字体：
    `font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;`

---

## 3. 四大经典 HTML 布局模板

### 模板 1：核心金句卡片（Quote Card）

*   **适用场景**：文章高潮处的逻辑升华、标志性结论、打动人心的内心独白。
*   **设计要点**：巨型文字水平垂直居中，背景辅以半透明质感，左上/右上放置半透明引号装饰。装饰性元素（引号）控制在 100px 以内，不抢占文字的视觉焦点。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      width: 960px;
      height: 540px;
      background-color: #090D16;
      font-family: system-ui, -apple-system, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      overflow: hidden;
      position: relative;
    }
    .card {
      width: 920px;
      height: 500px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      padding: 40px 50px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      position: relative;
    }
    .quote-mark {
      position: absolute;
      font-size: 100px;
      font-family: Georgia, serif;
      color: rgba(255, 255, 255, 0.04);
      line-height: 1;
    }
    .quote-left { top: 10px; left: 30px; }
    .highlight-text {
      font-size: 60px;
      font-weight: 800;
      line-height: 1.45;
      text-align: center;
      background: linear-gradient(135deg, #A855F7, #EC4899);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 16px;
    }
    .brand-tag {
      font-size: 24px;
      color: rgba(255, 255, 255, 0.35);
      letter-spacing: 2px;
      font-weight: 500;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="quote-mark quote-left">「</div>
    <!-- 核心限制：主金句不得超过20字，总行数不超过2行 -->
    <div class="highlight-text">真诚是唯一的捷径<br>可以不写，但绝不骗人</div>
    <div class="brand-tag">/ Cody 叩底</div>
  </div>
</body>
</html>
```

---

### 模板 2：逻辑/行为对比卡片（Contrast Card）

*   **适用场景**：展现错误/平庸行为与正确行为的强烈对比；阐述 AI 带来的数量级效率变化；过去 vs 现在。
*   **设计要点**：左右分栏，左侧代表「过去/低效/负面」（暗沉色调），右侧代表「未来/高效/正面」（明亮霓虹色调），中间用过渡箭头暗示变化趋势。每栏内容不少于 4 字不超过 12 字。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      width: 960px;
      height: 540px;
      background-color: #0E0E10;
      font-family: system-ui, -apple-system, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      overflow: hidden;
    }
    .card {
      width: 920px;
      height: 500px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0 20px;
    }
    .col {
      width: 380px;
      height: 340px;
      border-radius: 14px;
      padding: 30px 24px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
    }
    .col-left {
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .col-right {
      background: rgba(168, 85, 247, 0.04);
      border: 2px solid #A855F7;
      box-shadow: 0 0 25px rgba(168, 85, 247, 0.12);
    }
    .label {
      font-size: 24px;
      font-weight: 600;
      letter-spacing: 1px;
      margin-bottom: 24px;
    }
    .col-left .label { color: rgba(255, 255, 255, 0.25); }
    .col-right .label { color: #A855F7; }
    .content {
      font-size: 38px;
      font-weight: 700;
      line-height: 1.4;
      text-align: center;
    }
    .col-left .content { color: rgba(255, 255, 255, 0.55); }
    .col-right .content { color: #FFFFFF; }
    .divider {
      font-size: 42px;
      color: rgba(255, 255, 255, 0.15);
      font-weight: 300;
      margin: 0 10px;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="col col-left">
      <div class="label">过去</div>
      <div class="content">刷雪球<br>等一条消息</div>
    </div>
    <div class="divider">→</div>
    <div class="col col-right">
      <div class="label">现在</div>
      <div class="content">80+维度<br>实时分析</div>
    </div>
  </div>
</body>
</html>
```

---

### 模板 3：核心数据/指标卡片（Metric Card）

*   **适用场景**：抛出一个令人警醒或颠覆认知的数据指标，形成强烈的冲击波。
*   **设计要点**：左侧是极其巨大且带有微发光阴影的百分比/数字（视觉第一落脚点），右侧是短小精悍的结论解释。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      width: 960px;
      height: 540px;
      background-color: #090D16;
      font-family: system-ui, -apple-system, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      overflow: hidden;
    }
    .card {
      width: 920px;
      height: 460px;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0 30px;
      gap: 50px;
    }
    .metric-value {
      font-size: 150px;
      font-weight: 900;
      letter-spacing: -2px;
      background: linear-gradient(135deg, #00F2FE, #4FACFE);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      filter: drop-shadow(0 10px 20px rgba(0, 242, 254, 0.25));
      line-height: 1;
    }
    .metric-desc {
      display: flex;
      flex-direction: column;
      justify-content: center;
    }
    .metric-desc .title {
      font-size: 40px;
      font-weight: 800;
      color: #FFFFFF;
      line-height: 1.4;
      margin-bottom: 12px;
    }
    .metric-desc .sub {
      font-size: 24px;
      color: rgba(255, 255, 255, 0.35);
      letter-spacing: 1px;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="metric-value">84%</div>
    <div class="metric-desc">
      <div class="title">全球依然有 84% 的人<br>从未用过 AI 工具</div>
      <div class="sub">/ 真正的差值，才刚刚开始</div>
    </div>
  </div>
</body>
</html>
```

---

### 模板 4：场景变化卡片（Scenario Transformation Card）

*   **适用场景**：展示使用工具/方法前后的具体操作变化。不是抽象对比，而是把一个操作链条「拆出来」让读者看到：过去你要做 A→B→C 三步，现在一句话就搞定。
*   **设计要点**：上半部展示「过去怎么做」（灰色暗调，多步骤文字，带删除线或暗淡效果），下半部展示「现在怎么做」（霓虹高亮，一句话）。中间用一条渐变分割线。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      width: 960px;
      height: 540px;
      background-color: #090D16;
      font-family: system-ui, -apple-system, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      overflow: hidden;
    }
    .card {
      width: 920px;
      height: 480px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      padding: 30px 50px;
    }
    .section {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .before {
      color: rgba(255, 255, 255, 0.35);
      font-size: 34px;
      font-weight: 600;
      text-align: center;
      line-height: 1.5;
    }
    .before-label {
      font-size: 22px;
      color: rgba(255, 255, 255, 0.2);
      letter-spacing: 2px;
      margin-bottom: 10px;
      text-align: center;
    }
    .divider-line {
      height: 2px;
      background: linear-gradient(90deg, rgba(255,255,255,0.03), rgba(168,85,247,0.4), rgba(236,72,153,0.4), rgba(255,255,255,0.03));
      margin: 16px 0;
    }
    .after-label {
      font-size: 22px;
      color: #A855F7;
      letter-spacing: 2px;
      margin-bottom: 10px;
      text-align: center;
    }
    .after {
      font-size: 38px;
      font-weight: 800;
      text-align: center;
      line-height: 1.4;
      background: linear-gradient(135deg, #A855F7, #EC4899);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="section">
      <div>
        <div class="before-label">过去</div>
        <div class="before">开三个软件来回切<br>手动整理半小时</div>
      </div>
    </div>
    <div class="divider-line"></div>
    <div class="section">
      <div>
        <div class="after-label">现在</div>
        <div class="after">一句话，30秒出结果</div>
      </div>
    </div>
  </div>
</body>
</html>
```

---

## 5. 图片数量规划与插入策略

### 规划公式

```
图片数量 = ceil(预估总字数 / 400)
```

| 文章字数 | 应配图片数 | 推荐卡片类型分布 |
|---------|-----------|----------------|
| 2000字 | 5张 | 对比2 + 金句1 + 场景1 + 指标1 |
| 2500字 | 6-7张 | 对比2 + 金句1 + 场景2 + 指标1-2 |
| 3000字 | 7-8张 | 对比2-3 + 金句1-2 + 场景2-3 + 指标1 |
| 3500字 | 9张 | 对比3 + 金句2 + 场景2 + 指标2 |

### 插入节奏

- 开头 200-400字后插入第一张图（痛点/反差）
- 每个核心板块结束后插入对应的逻辑卡片
- 板块之间如果跨越超过 500 字无图片，中间插入过渡卡片（金句或场景）
- 高潮/结论前最后一张图应是最有冲击力的（指标型或金句型）

---

## 6. AI 落地生图执行流程

AI 代理在执行公众号写作任务并决定插入图片时，应当遵循以下步骤：

1.  **预规划**：在动笔前，根据目标字数（默认 2500-3000 字）计算所需图片数（≈ 6-8 张），在草稿大纲中标出每张图的插入位置和类型。
2.  **选题与判断**：在写作过程中，识别出对应的逻辑节点（观点反转、场景对比、金句总结、关键数据、操作链条变化）。
3.  **设计 HTML 文稿**：
    *   根据节点类型选择上述四个模板之一（金句、对比、数据、场景变化）。
    *   填入对应的文案。**严格执行字数核对（总字数不超过 35 字，主句不超过 20 字）**。
    *   字号必须不低于 24px。
    *   将 HTML 代码临时写入到 `<workspace>/scratch/temp_card_N.html`（N 为序号）。
4.  **渲染与截屏**：
    *   使用 Puppeteer/Playwright 等浏览器截屏工具对每个 `temp_card_N.html` 进行截屏。
    *   截屏的分辨率必须严格设置为 `960px` 宽，`540px` 高，确保完美的 16:9 画幅。
    *   保存截屏图片为 `png` 格式（建议命名为 `images/cody_visual_N.png`）。
5.  **插入正文**：在 markdown 正文对应的逻辑行，直接插入 markdown 图片标记，例如：
    `![过去开三个软件来回切，现在一句话30秒](images/cody_visual_1.png)`
6.  **密度复核**：全文写完后，统计实际图片数 vs 理论所需数。如果差距超过 1 张，补充或删减。
7.  **清理临时文件**：清理 `scratch/` 下所有 `temp_card_*.html` 文件。
