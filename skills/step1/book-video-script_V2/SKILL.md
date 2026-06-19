---
name: book-video-script-cody
description: |
  将长书、长文档、PDF、EPUB、读书资料、思想经典、社科著作、商业书或研究型长文转成更有传播感的中文视频号/抖音读书口播稿，并输出项目可用的 raw JSON。只要用户提到“读书解说”“拆书稿”“视频号口播”“把这本书做成短视频”“长文档转视频脚本”“生成标题/封面/金句/raw JSON”，都应使用此 skill。
---
# 长书读书视频脚本增强版

这个 skill 可审计长资料读取、覆盖台账、一次修订审计和 raw JSON 输出：

- 先判断内容是否有悬念、知识量和共鸣，而不是直接按章节总结。
- 先定一个观众关心的锋利角度，再写口播稿。
- 用读书视频原型组织材料，避免写成读书报告。
- 让知识像聊天中自然拿出来，而不是课堂讲义。
- 用四层质检把禁用表达、节奏、内容支撑和活人感逐层修掉。

这个 skill 的目标是让读书口播稿更像一个读透资料、懂普通人处境的人在认真讲一件值得知道的事。

## 文件分工

- `references/reading-strategy.md`：长资料抽取、Bash 字符窗口读取、覆盖台账和覆盖闸门。
- `references/writing-standard.md`：读书视频脚本的角度判断、叙事原型、文稿要求和最终 JSON 契约。
- `references/revision-workflow.md`：角度 brief、初稿、一次终稿修订和修订审计落盘流程。
- `references/script-quality-checklist.md`：借鉴四层质检后改造出的读书口播稿内置检查清单。

## 正文长度配置

这是本 skill 中正文成稿长度的唯一真相来源。其他 reference 不得重复写具体字数，只能引用本节。

```yaml
draft_min_chars: 3000
final_target_chars: 3200
```

- `_draft_v1.txt` 保存前必须达到 `draft_min_chars`。
- 后续所有正文稿原则上不得低于 `draft_min_chars`。
- 最终 raw JSON 的 `content` 目标长度按 `final_target_chars` 执行，`total_length` 写实际 `content` 字符数。

## 主流程

不要一轮直接输出。按「理解资料 -> 定角度 -> 选原型 -> 写初稿 -> 终稿修订并质检 -> 包装 JSON」执行：

1. **资料理解**：先读 `references/reading-strategy.md`。抽取文本、制定 Bash 字符窗口计划、建立并更新覆盖台账。
2. **覆盖闸门**：覆盖检查通过前，不得写角度 brief、初稿、修订稿或最终 JSON。
3. **角度 brief**：读 `references/writing-standard.md`，静默完成 HKR 判断，选定读书视频原型，保存 `_angle_brief.json`。
4. **初稿写作**：基于 `_angle_brief.json` 和 `writing-standard.md` 生成达到 `draft_min_chars` 的 `_draft_v1.txt`。
5. **终稿修订**：读 `references/revision-workflow.md` 和 `references/script-quality-checklist.md`，从 `_draft_v1.txt` 一次修订到 `_draft_final.txt`；修订中内置完成 L1-L4 检查，若 L1 或 L2 不通过，不得包装最终 JSON。
6. **包装输出**：从 `_draft_final.txt` 生成标题、封面文案、金句和最终 raw JSON；除非用户要求展示过程，最终只输出项目可用的 raw JSON，并确保可被 `json.loads` 解析。

## 自检要求

提交最终 JSON 前，静默确认：

- 覆盖台账中 `coverage_check.passed=true` 与事实一致，覆盖率达到分档要求，且覆盖开头、中段、结尾和主要章节。
- `_angle_brief.json` 已说明核心问题、观众关系、反常识点、读书视频原型、证据边界和评论争议点。
- 文稿没有按章节平推，没有写成“本书讲了什么”的读书报告。
- 每约 250 字有一次认知推进，并高频回扣主线。
- 重要观点都有来自资料的人、事、场景、制度、实验、数据或原文论证支撑。
- 终稿修订中已按四层质检完成内置检查，L1/L2 必须通过，L3/L4 没有未处理的关键问题；检查摘要已写入 `_revision_audit.json`。
- 修订过程已按 `revision-workflow.md` 落盘，终稿来自 `_draft_final.txt`，audit 能对应初稿到终稿的真实差异。
- JSON 符合 `writing-standard.md` 的最终 JSON 输出契约。
