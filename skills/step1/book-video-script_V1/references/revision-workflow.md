# Observable Revision Workflow

目标：让改稿过程可复盘。每轮都读入上一轮完整稿件，基于真实差异继续改；不要直接从初稿跳到最终 JSON。

所有文件保存到最终 raw JSON 同一目录，按顺序生成：

```text
_draft_v1.txt
_draft_v2_structure.txt
_draft_final.txt
_revision_audit.json
```

## Core Rules

- 每轮开始前先读对应的 `input_path`，不要凭记忆改。
- 进入结构稿和终稿时，先复制上一稿作为当前稿起点，再在副本上局部 `Edit`；除非结构主线完全错误，不得直接重写整篇。
- 每轮可多次 Agent/tool 调用，但最终必须落盘到对应文件。
- 所有正文稿原则上不得低于入口 `SKILL.md` 的 `draft_min_chars`；不足就修当前稿。
- 中间 txt 和最终 raw JSON 的 `content` 都保留自然段落换行；只清理行首行尾空白和多余连续空行。
- 每轮定稿后再写 audit；audit 只能记录相邻版本的真实差异。

## Rounds

### 1. `_draft_v1.txt`

第一稿的目标：按 `writing-standard.md` 写出完整初稿，忠于资料，覆盖核心人物、事件、概念和结论边界，并达到 `draft_min_chars`。第一稿不负责把结构和表达打磨到最终状态。

如果有可用的Subagent，这就是最重要的启动时间点。

### 2. `v1 -> v2_structure`

先复制上一稿为 `_draft_v2_structure.txt`，再只解决结构和节奏：

- 重写或修正开头，让问题、冲突和价值承诺更清楚。
- 把最值得听的内容前置，不平均分配篇幅。
- 清掉弱铺垫、传记流水账、重复背景、制度清单和空泛表达。
- 调整主线和信息顺序，让每约 250 字都有问题、反常识、场景、现实对照、反转或代价。

### 3. `v2_structure -> final`

先复制上一稿为 `_draft_final.txt`，再综合定稿：

- 把抽象判断落到具体人、事、制度、选择、风险或代价。
- 把书面句改成口播句，拆掉拗口长句和名词堆叠。
- 补自然评论触发点和两处「被说中」的现实表达。

## Edit Discipline

若当前轮不达标，继续在当前稿副本上做局部 Edit，每次只替换一个清晰语义块，并在关键修改后复查字数和本轮目标。只有上一稿的核心主线明显错误，且局部修改无法补救时，才允许整篇重写；重写后必须重新检查字数、忠实性和本轮目标。

## Revision Audit

`_revision_audit.json` 保持精简：

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

要求：结构轮和终稿轮各至少列出 3 条能在相邻版本中找到的 `before/after`。结构轮必须覆盖开头或前 100 字、弱结构压缩/移动、主线或节奏调整；终稿轮必须覆盖口语化、具体场景/评论点/金句/「被说中」表达、忠实性/禁用表达/长度/格式检查。若某轮没有实质差异，不能声称完成；继续改稿。不要只写“已优化”“已检查”“符合要求”。

## Package JSON

最后用 `_draft_final.txt` 生成 raw JSON。优先用 Python `json.dump` 写入并用 `json.load` 验证。`content` 保留终稿自然段落换行，可清理行首行尾空白和多余连续空行，但不能改正文措辞。
