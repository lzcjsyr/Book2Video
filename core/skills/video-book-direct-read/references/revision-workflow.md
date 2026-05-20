# Observable Revision Workflow

目标：让多轮改写可复盘。每轮都要读入上一轮完整稿件，再基于它继续改；结构和表达是重点。

所有文件保存到最终 raw JSON 同一目录。

## Required files

按顺序生成：

```text
_draft_v1.txt
_draft_v2_faithfulness.txt
_draft_v3_structure.txt
_draft_v4_oral_style.txt
_draft_final.txt
_revision_audit.json
```

不要跳过任何一轮，不要直接从初稿生成最终 JSON。每轮都先读对应的 `input_path`，不要凭记忆改。每一轮可以用多次 Agent/tool 调用完成，不要求一轮输出一次性改完。

中间 txt 是工作稿，可以有换行，也可以逐步编辑；等该轮文本定稿后，再把相邻版本差异写进 audit。

## Revision rounds

1. `v1 -> v2_faithfulness`
   只改忠实性：
   - 标出没有原文支撑、归因不清、过度拔高的句子。
   - 修正人物、时间、因果、概念和数字。
   - 补必要事实、边界或反例。

2. `v2_faithfulness -> v3_structure`
   重点改结构节奏：
   - 重写开头第一句话和前 100 字，先给问题、冲突、价值或场景。
   - 把最值得听的内容前置，不平均分配篇幅。
   - 清掉弱铺垫、传记流水账、重复背景和空泛表达。
   - 调整主线和信息顺序，让观众一直觉得后面还有一层可听。
   - 每约 250 字检查一次认知推进：问题、反常识、场景、现实对照、反转或代价。

3. `v3_structure -> v4_oral_style`
   重点改口语化表达：
   - 把抽象判断落到具体人、事、制度、选择、风险或代价。
   - 把书面句改成口播句，拆掉拗口长句和名词堆叠。
   - 补两处「被说中」的现实表达。
   - 补自然评论触发点，来自分歧、经验对照或价值张力。
   - 打磨金句，让它观点鲜明、好记，但不牺牲准确性。

4. `v4_oral_style -> final`
   只做格式确认：
   - 检查 3000-4200 字、无 Markdown、无小标题、无禁用表达。
   - 清理异常转义和多余空白。
   - 若 v4 已合格，final 可以等于 v4。

## Revision audit

`_revision_audit.json` 只能基于相邻版本的真实差异来写。

结构保持精简：

```json
{
  "revision_basis": {
    "meaningful_difference": true,
    "draft_paths": {
      "v1": "_draft_v1.txt",
      "v2_faithfulness": "_draft_v2_faithfulness.txt",
      "v3_structure": "_draft_v3_structure.txt",
      "v4_oral_style": "_draft_v4_oral_style.txt",
      "final": "_draft_final.txt"
    },
    "diff_summary": "四轮修订后的核心变化"
  },
  "revision_rounds": [
    {
      "round": "faithfulness|structure|oral_style|format",
      "purpose": "本轮目的",
      "input_path": "输入文件",
      "output_path": "输出文件",
      "meaningful_difference": true,
      "changes": [
        {"before": "原句", "after": "新句", "reason": "修改原因"}
      ]
    }
  ],
  "final_checks": {
    "content_length": 0,
    "json_valid": false,
    "forbidden_expressions_found": []
  }
}
```

要求：

- 忠实性、结构、口语三轮，每轮至少列出 2 条能在相邻版本中找到的 `before/after`。
- 结构轮至少 1 条来自开头第一句话或前 100 字，至少 1 条来自删除、移动或压缩弱结构。
- 口语轮至少 2 条来自具体表达变化，不要只补概念。
- 格式轮如果无改动，写 `meaningful_difference: false` 和空 `changes`，不要硬编差异。
- 不能只写“已优化”“已检查”“符合要求”。

## Package JSON

最后用 `_draft_final.txt` 生成 raw JSON。优先用 Python `json.dump` 写入并用 `json.load` 验证。`content` 可去掉 final draft 的换行和多余空白，但不能改正文措辞。
