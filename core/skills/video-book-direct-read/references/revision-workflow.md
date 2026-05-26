# Observable Revision Workflow

目标：让多轮改写可复盘。每轮都要读入上一轮完整稿件，再基于它继续改；结构和表达是重点。

所有文件保存到最终 raw JSON 同一目录。

## Required files

按顺序生成：

```text
_draft_v1.txt
_draft_v2_structure.txt
_draft_final.txt
_revision_audit.json
```

不要跳过任何一轮，不要直接从初稿生成最终 JSON。每轮都先读对应的 `input_path`，不要凭记忆改。每一轮可以用多次 Agent/tool 调用完成，不要求一轮输出一次性改完。

每轮修订前，先回看 `writing-standard.md` 中对应章节，不要凭记忆套标准：初稿自查看忠实性，结构稿看开头、结构和节奏，终稿看传播感、文风和最终 JSON 契约。

`_draft_v1.txt` 必须在保存前达到 3000 字以上。后续所有正文稿原则上不得低于 3000 字；若当前稿不足，继续扩写当前稿，不要把补长度留到后续修订或 final。

中间 txt 是工作稿，可以有换行，也可以逐步编辑；等该轮文本定稿后，再把相邻版本差异写进 audit。

## Per-round self-check and local Edit

每一轮稿件保存后，必须先自查再进入下一轮。自查至少检查：是否忠于资料、是否保留上一版的关键信息、是否低于 3000 字、是否出现结构断裂或明显书面腔。

开头是单独闸门：每轮自查都要检查前 100 字是否同时具备问题/冲突和价值承诺。若不具备，必须先用局部 `Edit` 修开头，不得把问题留到下一轮或 final。

若当前轮不达标，优先对当前稿做 1-3 次局部 `Edit`，不要直接进入下一轮，也不要无理由整篇重写。`Edit` 通过唯一 `old_string` 定位，不依赖行号；每次只替换一个清晰语义块，例如开头段、结尾段、某个不准确判断或一段口语化表达。`Edit` 后必须复查文件。

允许整篇重写的情况：结构主线明显错误、上一版无法修补、或需要重排大部分内容。整篇重写后仍必须自查。

## Revision rounds

1. `_draft_v1.txt` 保存后先自查忠实性
   - 标出没有原文支撑、归因不清、过度拔高的句子。
   - 修正人物、时间、因果、概念和数字。
   - 补必要事实、边界或反例。
   - 不合格时先对 `_draft_v1.txt` 做局部 `Edit`，再进入结构稿。

2. `v1 -> v2_structure`
   重点改结构节奏：
   - 先专项重写开头第一句话和前 100 字，必须给出问题/冲突和价值承诺；开头不合格时，先继续局部 `Edit` 开头，再处理全文结构。
   - 把最值得听的内容前置，不平均分配篇幅。
   - 清掉弱铺垫、传记流水账、重复背景和空泛表达。
   - 调整主线和信息顺序，让观众一直觉得后面还有一层可听。
   - 每约 250 字检查一次认知推进：问题、反常识、场景、现实对照、反转或代价。

3. `v2_structure -> final`
   综合定稿：
   - 把抽象判断落到具体人、事、制度、选择、风险或代价。
   - 把书面句改成口播句，拆掉拗口长句和名词堆叠。
   - 补两处「被说中」的现实表达。
   - 补自然评论触发点，来自分歧、经验对照或价值张力。
   - 打磨金句，让它观点鲜明、好记，但不牺牲准确性。
   - 检查 约3200 字、无 Markdown、无小标题、无禁用表达。
   - 清理异常转义和多余空白。

## Revision audit

`_revision_audit.json` 只能基于相邻版本的真实差异来写。

结构保持精简：

```json
{
  "revision_basis": {
    "meaningful_difference": true,
    "draft_paths": {
      "v1": "_draft_v1.txt",
      "v2_structure": "_draft_v2_structure.txt",
      "final": "_draft_final.txt"
    },
    "diff_summary": "两轮修订后的核心变化"
  },
  "revision_rounds": [
    {
      "round": "structure|final",
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

- 结构轮至少列出 3 条能在 `v1 -> v2_structure` 中找到的 `before/after`：至少 1 条来自开头第一句话或前 100 字，并说明问题/冲突和价值承诺如何变清楚；至少 1 条来自删除、移动或压缩弱结构。
- 终稿轮至少列出 3 条能在 `v2_structure -> final` 中找到的 `before/after`：至少 1 条来自口语化，至少 1 条来自具体场景、评论点、金句或「被说中」表达，至少 1 条来自忠实性、禁用表达、长度或格式检查。
- 若某轮局部 `Edit` 后仍无实质差异，不能声称完成该轮，必须继续改稿；不要硬编差异。
- 不能只写“已优化”“已检查”“符合要求”。

## Package JSON

最后用 `_draft_final.txt` 生成 raw JSON。优先用 Python `json.dump` 写入并用 `json.load` 验证。`content` 可去掉 final draft 的换行和多余空白，但不能改正文措辞。
