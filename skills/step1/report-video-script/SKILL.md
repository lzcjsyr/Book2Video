---
name: report-video-script
description: 将中短篇专业报告、公司财报、券商研报、招股书、宏观经济分析及含有较多表格和数据的PDF文档，转化为高品质、数据精准的中文视频号/抖音口播解说稿。只要用户提到“研报”、“财报”、“商业分析报告”或需要“解读数据”、“把报告/PDF做成短视频”，务必使用此 Skill。
---
# 数据密集型报告解说稿生成策略

这是一个专为**中短篇专业报告、公司财报、券商研报、行业白皮书等数据密集型材料**设计的视频文稿生成技能。它将繁杂的数据和表格转化为普通人听得懂、觉得有用的硬核解说视频。

本 Skill 是一个薄入口，负责把报告处理拆成几个可单独维护的模块：

- [reading-and-extraction.md](file:///Users/dielangli/Desktop/Coding/AIGC_Video/skills/step1/report-video-script/references/reading-and-extraction.md)：高精度文本/表格抽取（结合本地提取/外部预处理）、数据对照表初始化与窗口化阅读。
- [writing-standard.md](file:///Users/dielangli/Desktop/Coding/AIGC_Video/skills/step1/report-video-script/references/writing-standard.md)：研报解说稿的开头、逻辑推导、数据口语化标准和最终 JSON 输出契约。
- [revision-workflow.md](file:///Users/dielangli/Desktop/Coding/AIGC_Video/skills/step1/report-video-script/references/revision-workflow.md)：v1初稿、v2数据核对稿、Final终稿以及修改审计差分流程。

## 正文长度配置

这是本 Skill 中正文成稿长度的唯一真相来源。其他 Reference 不得重复写具体字数，只能引用本节。

```yaml
draft_min_chars: 1000
final_target_chars: 1200
```

- `_draft_v1.txt` 保存前必须达到 `draft_min_chars`。
- 后续所有正文稿原则上不得低于 `draft_min_chars`。
- 最终 raw JSON 的 `content` 目标长度按 `final_target_chars` 执行，`total_length` 写实际 `content` 字符数。

## 主流程

不要一轮直接输出。按以下步骤执行，以保证数据真实性与文稿传播力：

1. **提取与阅读**：先读 [reading-and-extraction.md](file:///Users/dielangli/Desktop/Coding/AIGC_Video/skills/step1/report-video-script/references/reading-and-extraction.md)。使用本地提取工具（如 PyMuPDF/fitz）解析 PDF 或直接读取已预先转换好的 Markdown 报告，划分 Bash 阅读窗口并 100% 读入。**建立数据对照表**以备后查。
2. **确定逻辑切入点**：静默提取报告核心问题（如行业危机、公司增长瓶颈、宏观异动），提取报告核心解释框架，并绑定一个跟受众高度相关的利益切入点（e.g. 这个数据对普通人意味着什么）。
3. **撰写初稿**：读 [writing-standard.md](file:///Users/dielangli/Desktop/Coding/AIGC_Video/skills/step1/report-video-script/references/writing-standard.md)，撰写达到 `draft_min_chars` 的 `_draft_v1.txt`，重点在于将冰冷的数据“翻译”为口语和逻辑因果。
4. **结构与数据校验修订**：读 [revision-workflow.md](file:///Users/dielangli/Desktop/Coding/AIGC_Video/skills/step1/report-video-script/references/revision-workflow.md)。第二稿 `_draft_v2_structure.txt` 确定后，直接保存为初步的 `_draft_final.txt`。提取其中所有数据生成台账 `_data_check_ledger.json`（初始为 `unchecked`）。之后对照原文校验，直接在 `_draft_final.txt` 上进行局部订正/删改（更新状态为 `verified`/`abandon`/`corrected`）。所有数据校验完成（无 `unchecked`）后，定稿 `_draft_final.txt` 并记录 `_revision_audit.json` 差分审计。
5. **打包输出 JSON**：依据 [writing-standard.md](file:///Users/dielangli/Desktop/Coding/AIGC_Video/skills/step1/report-video-script/references/writing-standard.md) 的最终 JSON 输出契约生成最终 JSON。

## 自检要求

提交最终 JSON 前，静默确认：

- 数据对照表已完整建立，文稿中出现的每一个百分比、金额、比率等数字都在对照表中有精确出处。
- **数据检验台账 `_data_check_ledger.json` 中所有条目的 `status` 均已更新（无 `unchecked`），完成数据闭环。**
- 开头在 100 字内给出了尖锐的问题或核心冲突，以及观众关心的利益承诺。
- 每约 250 字有一次逻辑推进，文笔口语化，删除了“本书提到”、“从上图可以看出”等 AI 总结词。
- 修订流程完备，每一轮的修改都在 `_revision_audit.json` 中有清晰的 before/after。
