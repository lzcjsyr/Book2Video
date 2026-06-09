# 数据校验修订流程

为了确保研报解说稿件在具备传播力的同时拥有 100% 的行业严谨度，本 Skill 采用可复盘的“数据校验修订流程”，通过分阶段的结构优化与数据核实，最大限度规避 AI 创作中的逻辑偏误与事实错误。

在最终 JSON 的同级目录下，按顺序必须生成以下工作文件：
```text
_draft_v1.txt
_draft_v2_structure.txt
_draft_final.txt
_data_check_ledger.json
_revision_audit.json
```

---

## 第一轮：初稿创作 (`_draft_v1.txt`)
- **关注点**：将数据对照表中的核心事实转化为连贯的口语解说。构建起 Cause -> Effect（因果）的硬核逻辑线。
- **字数门槛**：保存前必须达到 [SKILL.md](file:///Users/dielangli/Desktop/Coding/AIGC_Video/skills/step1/report-video-script/SKILL.md) 规定的 `draft_min_chars`。如果不达标，必须在当前阶段扩写，绝不能推迟到后续修订。

---

## 第二轮：结构调整与口语化修订 (`_draft_v2_structure.txt`)
在进行数据校验之前，必须先理顺解说稿的**宏观结构**与**口播节奏**。如果在数据校验后再做结构调整或口语润色，极易因句子重组引入新的数据偏误。

### 修订清单：
1. **开头钩子**：开头在 100 字内是否给出了尖锐的问题或核心冲突，以及观众关心的利益承诺？
2. **逻辑因果链**：核心论点和数据之间的因果链条（Cause -> Effect）是否顺畅？
3. **口语化与去 AI 味**：删除“总而言之”、“如图所示”等AI常用书面总结词。将长难句拆为适合口播的 25 字以内短单句。
4. **冻结结构与措辞**：本轮完成后，文本的所有逻辑、字数、句式口播形式均已定稿（冻结），并作为第三轮核对的基准。

---

## 第三轮：终稿数据核查与局部订正 (`_draft_final.txt`)
这是本 Skill 的**终极安全闸门**。为了绝对避免因 AI 重新生成而引入新的数据错误，必须**先输出终稿文件，然后直接在终稿上对着数据逐一校对和局部修改**。

### 数据检验台账工作流：
1. **生成初步终稿 (`_draft_final.txt`)**：
   直接将第二稿 `_draft_v2_structure.txt` 输出为 `_draft_final.txt` 作为待校验的终稿。
2. **初始化台账 (`_data_check_ledger.json`)**：
   提取刚刚生成的 `_draft_final.txt` 中出现的**所有数据点**（包括金额、百分比、增长率、排名等），写入 `_data_check_ledger.json`。所有数据条目的初始状态均为 `"unchecked"`。
   其 JSON 结构如下：
   ```json
   {
     "data_points": [
       {
         "data": "净利润达到1000万",
         "status": "unchecked",
         "corrected_value": null,
         "source_quote": "在原文中对应的原句或图表数据"
       }
     ]
   }
   ```
3. **对照原文，直接修改终稿并更新状态**：
   去原文/数据表中逐一校验台账中的数据，并直接对 `_draft_final.txt` 进行局部修改（如删除或改正数据），同时将台账中的 `status` 变更为以下状态之一：
   * `"verified"`：核准数据 100% 正确且与原文吻合，无需修改文稿。
   * `"abandon"`：若原文中找不到该数据/属虚构，**直接修改 `_draft_final.txt` 删改或替换此表述**，台账状态标为 `"abandon"`。
   * `"corrected"`：若数据有误，**直接修改 `_draft_final.txt` 将其更正**，在台账 `corrected_value` 中写入改正后的值，状态标为 `"corrected"`。
4. **完成校验**：
   当且仅当台账中所有数据的 status 均已处理完毕（不含有任何 `"unchecked"`）时，整个核验流程结束，此时的 `_draft_final.txt` 即为最终确认的解说稿。

---

## 第四轮：记录审计报告 (`_revision_audit.json`)

完成三轮工作后，将相邻版本间的修改记录在 audit 中。

### Audit JSON 契约

```json
{
  "revision_basis": {
    "meaningful_difference": true,
    "draft_paths": {
      "v1": "_draft_v1.txt",
      "v2_structure": "_draft_v2_structure.txt",
      "final": "_draft_final.txt"
    },
    "diff_summary": "优化文章结构与口语化节奏，并通过 _data_check_ledger.json 对终稿数据进行了逐一校验与局部订正"
  },
  "revision_rounds": [
    {
      "round": "structure_and_oral",
      "purpose": "优化文章开头钩子、去除书面词并重组因果逻辑链",
      "input_path": "_draft_v1.txt",
      "output_path": "_draft_v2_structure.txt",
      "meaningful_difference": true,
      "changes": [
        {
          "before": "本报告首先介绍了行业背景，如图表所示，这代表了公司毛利收窄的状况。总的来说...",
          "after": "为什么行业龙头今年利润腰斩？这代表了公司的毛利直接被砍掉了一大截。这意味着...",
          "reason": "将枯燥的背景介绍改为强悬念开头，删除AI常用书面语，改用短句"
        }
      ]
    },
    {
      "round": "data_check",
      "purpose": "根据 _data_check_ledger.json 对照数据参考表，逐字核对数据、趋势与单位并直接修改终稿",
      "input_path": "_draft_v2_structure.txt",
      "output_path": "_draft_final.txt",
      "meaningful_difference": true,
      "changes": [
        {
          "before": "净利润达到1000万，同比增长了5%",
          "after": "净利润达到1000万美元，同比降幅收窄了5个百分点",
          "reason": "纠正了财务单位错误（漏写美元）以及对降幅收窄趋势的口播表达"
        }
      ]
    }
  ],
  "final_checks": {
    "content_length": 2510,
    "json_valid": true,
    "all_numbers_verified": true,
    "forbidden_expressions_found": []
  }
}
```

---

## 最终 JSON 打包规范

当 `_draft_final.txt` 定稿后，使用 Python 脚本或可靠工具进行 JSON 打包，**禁止手动组装 JSON** 以免产生逸出字符故障。

生成 `raw.json`（或根据项目约定的文件名，如 `script.json`），用 Python 的 `json.loads` 加载验证其语法，确保能顺利进入后续的配音或配图流程。
