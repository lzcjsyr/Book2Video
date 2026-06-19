# Observable Revision Workflow

目标：让改稿过程可复盘，同时避免过重流程。这个 skill 只保留一次正式修订：先写完整初稿，再从初稿修到终稿，并在这一次修订里完成结构、口播、传播点和四层质检。

所有文件保存到最终 raw JSON 同一目录，按顺序生成：

```text
_angle_brief.json
_draft_v1.txt
_draft_final.txt
_revision_audit.json
```

## Core Rules

- 进入写稿前必须已经通过 `reading-strategy.md` 的覆盖闸门。
- 写 `_angle_brief.json` 前先读 `writing-standard.md` 的“角度判断”和“读书视频原型”。
- 写 `_draft_final.txt` 前必须读完整 `_draft_v1.txt`，不要凭记忆改。
- 终稿修订时，先复制 `_draft_v1.txt` 为 `_draft_final.txt`，再在副本上局部修改；只有初稿主线明显错误且局部修改无法补救时，才允许整篇重写。
- 所有正文稿原则上不得低于入口 `SKILL.md` 的 `draft_min_chars`；不足就修当前稿。
- 中间 txt 和最终 raw JSON 的 `content` 都保留自然段落换行；只清理行首行尾空白和多余连续空行。
- 修订完成后写 `_revision_audit.json`；audit 只能记录从初稿到终稿的真实差异。

## Rounds

### 0. `_angle_brief.json`

角度 brief 的目标：把 Cody 式“先判断选题质量，再写文章”的方法转成可执行的读书视频决策。

必须包含：

- `core_question`：资料真正回答的一个核心问题。
- `viewer_relevance`：这个问题为什么和普通观众有关。
- `hook`：开头可用的冲突、反常识或现实困惑。
- `knowledge_gain`：观众听完获得的新框架。
- `resonance_points`：至少两个“被说中”的现实处境。
- `script_archetype`：从 `writing-standard.md` 中选一个主原型。
- `main_thread`：全文回扣的一句话主线。
- `evidence_boundary`：资料确定说了什么、没说什么、哪些不能夸大。
- `comment_tensions`：三个真实讨论点。

如果 HKR 中 K 不成立，不能写稿；说明资料或覆盖理解不足，回到阅读或让用户补材料。如果 H/R 都弱，可以写但必须优先调整切口。

### 1. `_draft_v1.txt`

第一稿的目标：按 `_angle_brief.json` 和 `writing-standard.md` 写出完整初稿，忠于资料，覆盖核心人物、事件、概念、机制和结论边界，并达到 `draft_min_chars`。

第一稿不负责把结构和表达打磨到最终状态，但必须避免明显读书报告腔：

- 不按章节平推。
- 不用“本书讲述了”“作者认为”作为主推进方式。
- 开头 100 字内必须有冲突和观众收益。
- 每个重要判断都能回到资料证据。

### 2. `v1 -> final`

先复制 `_draft_v1.txt` 为 `_draft_final.txt`，再在一次修订中同时完成结构、口播、传播点和质检修复。

修订重点：

- 重写或修正开头，让问题、冲突和价值承诺更清楚。
- 把最值得听的内容前置，不平均分配篇幅。
- 清掉弱铺垫、传记流水账、章节平推、重复背景、概念堆叠和空泛表达。
- 按 `_angle_brief.json` 的 `main_thread` 加强回扣句。
- 调整信息顺序，让每约 250 字都有问题、反常识、场景、现实对照、反转或代价。
- 如果有多个案例或观点，改成逐一展示，按弱到强、浅到深排列。
- 把抽象判断落到具体人、事、制度、选择、风险或代价。
- 把书面句改成口播句，拆掉拗口长句和名词堆叠。
- 补自然评论触发点和两处“被说中”的现实表达。
- 补至少一句来自资料矛盾的金句。
- 检查结尾是否回扣开头问题或意象，有余味但不课程化。
- 按 `script-quality-checklist.md` 完成 L1-L4 内置检查；L1/L2 不通过时继续修 `_draft_final.txt`，不得包装最终 JSON。

## Edit Discipline

若终稿不达标，继续在 `_draft_final.txt` 上做局部 Edit，每次只替换一个清晰语义块，并在关键修改后复查字数和本轮目标。只有初稿的核心主线明显错误，且局部修改无法补救时，才允许整篇重写；重写后必须重新检查字数、忠实性和质检结果。

## Revision Audit

`_revision_audit.json` 保持精简：

```json
{
  "revision_basis": {
    "meaningful_difference": true,
    "draft_paths": {
      "angle_brief": "_angle_brief.json",
      "v1": "_draft_v1.txt",
      "final": "_draft_final.txt"
    },
    "diff_summary": "初稿到终稿的核心变化"
  },
  "revision_rounds": [
    {
      "round": "final",
      "purpose": "一次终稿修订，完成结构、口播、传播点和质检修复",
      "input_path": "_draft_v1.txt",
      "output_path": "_draft_final.txt",
      "meaningful_difference": true,
      "changes": [
        {"before": "原句", "after": "新句", "reason": "修改原因"}
      ]
    }
  ],
  "quality_check_summary": {
    "l1_hard_rules_passed": false,
    "l2_oral_structure_passed": false,
    "l3_content_quality_passed": false,
    "l4_human_feel_passed": false,
    "remaining_issues": []
  },
  "final_checks": {
    "content_length": 0,
    "json_valid": false,
    "forbidden_expressions_found": []
  }
}
```

要求：

- `changes` 至少列出 5 条能在初稿和终稿中找到的 `before/after`。
- 必须覆盖开头或前 100 字、弱结构压缩/移动、主线或节奏调整、口语化、具体场景/评论点/金句/“被说中”表达、忠实性/禁用表达/长度/格式检查。
- `quality_check_summary` 记录四层质检结果。L1/L2 必须为 `true` 才能进入 JSON 包装；L3/L4 若为 `false`，必须在 `remaining_issues` 中说明为什么仍可交付，通常应继续修稿。
- 若没有实质差异，不能声称完成；继续改稿。
- 不要只写“已优化”“已检查”“符合要求”。

## Package JSON

最后用 `_draft_final.txt` 生成 raw JSON。优先用 Python `json.dump` 写入并用 `json.load` 验证。`content` 保留终稿自然段落换行，可清理行首行尾空白和多余连续空行，但不能改正文措辞。
