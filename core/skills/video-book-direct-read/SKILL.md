---
name: video-book-direct-read
description: 用 Bash 按每窗不超过 23000 字符连续读取长书全文，建立覆盖台账并自检通过后，再生成中文视频号读书解说稿。
---

# 长资料直接大块读稿策略

这个 skill 是一个薄入口，负责把长文档处理拆成几个可单独维护的模块：

- `references/reading-strategy.md`：Bash 按每窗不超过 23000 字符连续读取、覆盖台账格式、落盘路径、失败条件。
- `references/writing-standard.md`：视频号读书解说稿的具体文稿要求和最终 raw JSON 字段格式。
- `references/revision-workflow.md`：逐轮初稿、忠实性稿、结构稿、口语稿、终稿和差异审计的可复盘落盘流程。

## 使用顺序

1. 先读 `references/reading-strategy.md`，抽取文本、制定 Bash 读取计划（默认每窗 **不超过 23000 字符**）、用 `sed`/`awk` 连续读取 `{extract_path}`、建立并保存覆盖台账到 `{coverage_ledger_path}`。
2. 覆盖检查通过后，再读 `references/writing-standard.md`：15 万字符以内必须全部读完；15-20 万字符至少覆盖 80%；超过 20 万字符至少覆盖 50%，且必须均匀覆盖全书并理解全书轮廓和核心思想。
3. 读 `references/revision-workflow.md`，按要求保存每轮改写文件，再基于相邻版本的真实差异写修订审计。
4. 输出前回看 `references/writing-standard.md` 的“最终 JSON 输出契约”，确保最终 JSON 可被 `json.loads` 解析。

## 运行原则

- 先覆盖，再写稿。没有覆盖台账，不要进入初稿或最终 JSON。
- 覆盖台账用于证明“读到了哪些区域”，不是普通摘要；写稿前你必须自己核对 `_coverage_ledger.json` 是否真实、完整。
- 最终 JSON 前必须产生 `_draft_v1.txt`、`_draft_v2_faithfulness.txt`、`_draft_v3_structure.txt`、`_draft_v4_oral_style.txt`、`_draft_final.txt`、`_revision_audit.json`，且 audit 必须基于相邻版本差异。
- 不要把局部段落误说成全书观点。
- 正文只用 Bash 读，默认每窗不超过 23000 字符；截断时减半重读，不要改用 `Read` 或跳读抽样。
- 覆盖率按全文字符数分档：`source_total_chars <= 150000` 必须 100% 覆盖；`150000 < source_total_chars <= 200000` 必须覆盖至少 80%；`source_total_chars > 200000` 必须覆盖至少 50%，且不能只读前半部分或局部热点，必须均匀覆盖开头、中段、结尾和主要章节，形成对全书轮廓与核心思想的完整理解。
- 最终输出只应是项目可用的 raw JSON，除非用户要求展示过程。

## 最终自检

提交最终 JSON 前，静默确认：

- 已按全文字符数分档达到覆盖率要求，覆盖开头、中段、结尾和主要章节，且台账中 `coverage_check.passed=true` 与事实一致。
- 每个重要判断能回忆到对应读取窗口。
- 文稿符合 `writing-standard.md` 的开头、节奏、文风、禁用表达和修订要求。
- 修订过程已按 `revision-workflow.md` 逐轮落盘，终稿来自 `_draft_final.txt`，audit 能对应每一轮的真实差异。
- JSON 符合 `writing-standard.md` 的最终 JSON 输出契约。
