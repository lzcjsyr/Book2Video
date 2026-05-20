# Direct Large-Block Reading Strategy

用这个 reference 执行“尽量直接读原文”的长文档方案。**正文阅读以 Bash 为主**，按固定行数切块连续读入上下文；Python 只用于统计规模、抽取 PDF/EPUB 和写入 JSON 台账。

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
wc -c "$EXTRACT"
```

确认：

- 总行数（写入台账 `source_total_lines`）
- 总字符数（写入台账 `source_total_chars`）
- 是否有目录、章节标题、页码线索

## 3. 制定读取计划

### 默认窗口

- **工具**：优先 `Bash`（`sed` / `awk`），不要用 `Read` 读正文大块。
- **目标块大小**：每个窗口 **23000 行**（`lines_per_window: 23000`）。
- **推进方式**：窗口首尾相接、连续覆盖全书，禁止跳读抽样。

示例：12 万行全书 → 计划 6 窗：`1-23000`、`23001-46000`、…、`115001-120000`（最后一窗不足 23000 行则读到文件末尾）。

### 硬规则

- “已读”只指该窗口全文已通过 **Bash 标准输出**完整进入当前上下文。
- 只写入临时文件、只看 `head`/`tail`、只读窗口开头，都不能算覆盖。
- 禁止在覆盖台账通过前写初稿、修订稿或 `raw.json`。
- `Read` 仅用于：skill、`references/`、小配置文件；**不要**用 `Read` 替代 Bash 读 `_extract.txt` 正文。

### 输出被截断时

若 Bash 输出被截断、只剩 head/tail、或无法基于该窗做具体总结：

1. 将当前窗 **减半**（23000 → 11500 → 5750 …），用更小行范围 **重读同一区间**；
2. 台账里该窗标记 `coverage_status: partial`，减半重读通过后再改为 `complete`；
3. 不要为了省事改用 `Read` 或跳读下一段。

### 读取命令（首选 Bash）

```bash
EXTRACT="output/<project>/text/_extract.txt"
START=1
END=23000
sed -n "${START},${END}p" "$EXTRACT" | awk '{print NR+('"$START"'-1) "\t" $0}'
```

下一窗：`START=23001`，`END=46000`，依此类推，直到 `START > 总行数`。

也可用纯 `sed`（无行号）：

```bash
sed -n '23001,46000p' "$EXTRACT"
```

### 读取计划示例

```json
{
  "source_file": "output/<project>/text/_extract.txt",
  "read_strategy": "bash_line_window",
  "lines_per_window": 23000,
  "unit": "line_range",
  "planned_windows": [
    {"start_line": 1, "end_line": 23000},
    {"start_line": 23001, "end_line": 46000},
    {"start_line": 46001, "end_line": 69000}
  ]
}
```

## 4. 建立覆盖台账

每读完一个 Bash 窗口，立即追加一条 `coverage_windows` 记录。台账不是摘要，而是证明哪些行已读过。

单窗结构：

```json
{
  "window_id": 1,
  "read_tool": "bash",
  "lines_per_window": 23000,
  "planned_range": "line 1-23000",
  "actual_read_range": "line 1-23000",
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
  "read_strategy": "bash_line_window",
  "lines_per_window": 23000,
  "planned_windows": [],
  "coverage_windows": [],
  "coverage_check": {
    "start_covered": true,
    "middle_covered": true,
    "end_covered": true,
    "line_coverage_ratio": 0.92,
    "all_windows_complete": true,
    "passed": true
  }
}
```

检查项：

- 是否用 Bash 连续读完所有计划窗口（默认每窗 23000 行，末窗可更短）。
- 是否覆盖开头、中段、结尾（首尾各约 5% 行，以及全书中间带）。
- 是否覆盖目录或主要章节。
- 是否所有窗口都是 `coverage_status: complete`；`partial` 不能进入写稿。
- 连续窗口合并后的行覆盖率是否 >= 85%。
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

- 即使减半到很小窗口，Bash 输出仍无法完整进入上下文。
- 文档超过可控规模，无法在一次 Agent 会话中可靠保持全书上下文。
- 章节多且论证复杂，连续 Bash 读法仍频繁遗漏。
- 用户要求可审计证据链、短引文、限制条件和回查文件。
