# Direct Large-Block Reading Strategy

用这个 reference 执行“尽量直接读原文”的长文档方案。**正文阅读以 Bash 为主**，按固定字符预算切块连续读入上下文；Python 只用于统计规模、抽取 PDF/EPUB 和写入 JSON 台账。

## 1. 准备抽取文本

如果输入是 PDF、EPUB、MOBI、AZW3 或 DOCX，先用本地工具抽取成 UTF-8 文本。不要直接 `Read` 大型 PDF。

推荐保存路径：

```text
output/<project>/text/_extract.txt
```

如果输入本身已是 `.md` / `.txt`，也要复制或规范化到上述路径，后续所有正文读取都针对该文件。

## 2. 估算规模

先用 **Bash** 统计规模（不要用 `Read` 扫全文）：

```bash
EXTRACT="output/<project>/text/_extract.txt"
wc -l "$EXTRACT"
wc -m "$EXTRACT"
```

确认：

- 总行数（写入台账 `source_total_lines`）
- 总字符数（写入台账 `source_total_chars`，使用 `wc -m`，不是 `wc -c` 字节数）
- 是否有目录、章节标题、页码线索

## 2.5. 覆盖率分档

根据 `source_total_chars` 选择覆盖策略，并写入台账 `coverage_policy` 与 `required_coverage_ratio`：

- `source_total_chars <= 150000`：必须 **100% 全文读完**，`required_coverage_ratio: 1.0`。
- `150000 < source_total_chars <= 200000`：至少覆盖 **80%**，`required_coverage_ratio: 0.8`。
- `source_total_chars > 200000`：至少覆盖 **50%**，`required_coverage_ratio: 0.5`。

超过 20 万字符时，50% 是最低覆盖率，不是只读前半本的许可。必须把覆盖窗口均匀分布到全书开头、中段、结尾和主要章节，优先保证能完整理解：

- 全书真正回答的问题
- 核心概念和主要论证链
- 关键人物、事件、案例或数据
- 作者的结论、边界和写作意图
- 各主要章节之间的关系

如果无法形成对全书轮廓和核心思想的完整理解，即使字符覆盖率达到 50%，也不能让 `coverage_check.passed=true`。

## 3. 制定读取计划

### 默认窗口

- **工具**：优先 `Bash`（`sed` / `awk`），不要用 `Read` 读正文大块。
- **目标块大小**：每个窗口 **不超过 23000 字符**（`chars_per_window: 23000`）。
- **推进方式**：窗口首尾相接、连续覆盖全书，尽量避免跳读抽样。
- **定位方式**：用行号范围定位窗口，但窗口大小由字符数决定。每个窗口的 Bash 标准输出必须低于字符预算。
- **单位一致**：`source_total_chars`、`planned_chars`、`char_coverage_ratio` 必须全部按字符数计算；使用 `wc -m` 或等价字符计数，禁止用 `wc -c` 字节数计算窗口和覆盖率。

示例：46 万字符全书 -> 约 21 窗，每窗按连续行范围读取，但先用 `awk` 估算每窗字符数，确保单窗输出不超过 23000 字符。最后一窗不足 23000 字符则读到文件末尾。

### 硬规则

- Bash 命令执行成功不等于读完；只有该窗口正文完整进入当前上下文，才能记为 `complete`。
- “已读”只指该窗口全文已通过 **Bash 标准输出**完整进入当前上下文，且没有出现 `<persisted-output>`、`Output too large`、`Full output saved to` 等大输出落盘提示。
- 只写入临时文件、只看 `head`/`tail`、只读窗口开头、只拿到 tool-results 文件路径，都不能算覆盖。
- 禁止在覆盖台账通过前写初稿、修订稿或 `raw.json`。
- `Read` 仅用于：skill、`references/`、小配置文件；**不要**用 `Read` 替代 Bash 读 `_extract.txt` 正文。

### 输出被截断或落盘时

若 Bash 输出被截断、落盘为 `<persisted-output>`、只剩 head/tail、或无法基于该窗做具体总结：

1. 将当前窗字符预算 **减半**（23000 -> 11500 -> 5750 ...），用更小行范围 **重读同一区间**；
2. 台账里原窗口标记 `coverage_status: partial`，减半重读通过后用多个 `complete` 子窗口覆盖同一区间；
3. 不要为了省事改用 `Read`、直接读取 tool-results 文件或跳读下一段。

### 制定字符窗口

先用 Bash 生成连续窗口计划。下面示例按 UTF-8 字符数近似控制每窗不超过 23000 字符，并保留行号范围：

```bash
EXTRACT="output/<project>/text/_extract.txt"
MAX_CHARS=23000
awk -v max="$MAX_CHARS" '
  BEGIN { start=1; chars=0 }
  {
    line_chars = length($0) + 1
    if (chars > 0 && chars + line_chars > max) {
      printf "%d\t%d\t%d\n", start, NR-1, chars
      start = NR
      chars = 0
    }
    chars += line_chars
  }
  END {
    if (chars > 0) printf "%d\t%d\t%d\n", start, NR, chars
  }
' "$EXTRACT"
```

### 读取命令（首选 Bash）

按窗口计划逐窗读取，确保每窗 `planned_chars` 不超过 `chars_per_window`：

```bash
EXTRACT="output/<project>/text/_extract.txt"
START=1
END=180
sed -n "${START},${END}p" "$EXTRACT" | awk '{print NR+('"$START"'-1) "\t" $0}'
```

下一窗使用计划中的下一组 `START` / `END`，依此类推，直到 `START > 总行数`。

### 读取计划示例

```json
{
  "source_file": "output/<project>/text/_extract.txt",
  "read_strategy": "bash_char_budget_window",
  "chars_per_window": 23000,
  "unit": "line_range_with_char_budget",
  "planned_windows": [
    {"start_line": 1, "end_line": 180, "planned_chars": 22840},
    {"start_line": 181, "end_line": 354, "planned_chars": 22910},
    {"start_line": 355, "end_line": 520, "planned_chars": 22130}
  ]
}
```

## 4. 建立覆盖台账

读取正文前，先创建 `_coverage_ledger.json` 初始台账，写入 source 信息、覆盖策略、`planned_windows`、空的 `coverage_windows`，并设置 `coverage_check.passed=false`。

每读完一个 Bash 窗口，立即落盘更新 `_coverage_ledger.json`，追加一条 `coverage_windows` 记录并刷新当前覆盖率。不要等全部窗口读完后一次性写台账；最终台账不得漏掉已读窗口，也不得把未记录窗口计入覆盖率。

台账不是摘要，而是证明哪些行和字符预算窗口已读过。

单窗结构：

```json
{
  "window_id": 1,
  "read_tool": "bash",
  "chars_per_window": 23000,
  "planned_range": "line 1-180",
  "actual_read_range": "line 1-180",
  "planned_chars": 22840,
  "coverage_status": "complete",
  "section_hint": "序章/第一章",
  "main_points_seen": ["这一窗口的核心信息"],
  "important_examples_seen": ["关键例子或事件"],
  "relation_to_whole_book": "它如何影响全书主线",
  "uncertainties": ["需要后文验证的点"]
}
```

## 5. 覆盖检查与落盘

写稿前必须完成覆盖检查，并把完整台账保存到：

```text
output/<project>/text/_coverage_ledger.json
```

推荐顶层结构：

```json
{
  "source_file": "output/<project>/text/_extract.txt",
  "source_total_lines": 120000,
  "source_total_chars": 4800000,
  "read_strategy": "bash_char_budget_window",
  "chars_per_window": 23000,
  "coverage_policy": "source_total_chars > 200000: evenly distributed coverage, minimum 50%",
  "required_coverage_ratio": 0.5,
  "planned_windows": [],
  "coverage_windows": [],
  "coverage_check": {
    "start_covered": true,
    "middle_covered": true,
    "end_covered": true,
    "major_sections_covered": true,
    "whole_book_outline_understood": true,
    "core_ideas_understood": true,
    "coverage_evenly_distributed": true,
    "line_coverage_ratio": 0.55,
    "char_coverage_ratio": 0.52,
    "all_windows_complete": true,
    "passed": true
  }
}
```

检查项：

- 是否用 Bash 连续读完所有计划窗口（默认每窗不超过 23000 字符，末窗可更短）。
- 不要把 Bash 执行成功、生成了 tool-results 文件或扫到了行号，当成阅读完成。
- 是否每窗都完整进入上下文，且没有出现 `<persisted-output>`、`Output too large` 或只返回 preview 的情况。
- 是否按 `source_total_chars` 选择正确覆盖率分档：15 万字符以内 100%；15-20 万字符至少 80%；超过 20 万字符至少 50%。
- 是否覆盖开头、中段、结尾（首尾各约 5% 行/字符，以及全书中间带）。
- 是否覆盖目录或主要章节。
- 对超过 20 万字符的长书，覆盖是否均匀分布在全书范围内，而不是只读前半部分、只读结尾或只读最容易处理的局部。
- 是否已经形成对全书轮廓、核心思想、主要论证链和关键章节关系的完整理解。
- 是否所有窗口都是 `coverage_status: complete`；`partial` 不能进入写稿。
- 连续窗口合并后的行覆盖率和字符覆盖率是否达到当前分档要求。
- 是否只读了最容易读的局部。

只有 `coverage_check.passed=true` 且上述条件都满足，才能进入 `writing-standard.md` 的写稿流程。

## 6. 全书理解

覆盖通过后，基于覆盖台账和已读原文形成内部理解：

- 作品真正回答的问题
- 主要论证主线
- 最值得视频化的冲突点
- 必须包含的关键事实、例子或概念
- 不应夸大的边界

除非用户要求，不要输出这一步。

## 7. 失败和切换条件

遇到以下情况，停止直接读法并建议切换：

- 即使减半到很小字符窗口，Bash 输出仍无法完整进入上下文。
- 文档超过可控规模，无法在一次 Agent 会话中可靠保持全书上下文。
- 章节多且论证复杂，连续 Bash 读法仍频繁遗漏。
- 用户要求可审计证据链、短引文、限制条件和回查文件。
