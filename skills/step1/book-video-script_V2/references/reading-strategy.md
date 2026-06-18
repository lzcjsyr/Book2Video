# Direct Large-Block Reading Strategy

用于长书、长文档“尽量直接读原文”。长正文用 Bash 统计、搜索和按字符预算分窗读入上下文；小文件和阶段产物用 Read 精确读取；Python 只用于抽取文本、统计规模和维护 JSON 台账。

这个文件只解决“是否真的读到了足够资料”。读书视频的角度、结构和文风在 `writing-standard.md` 与 `script-quality-checklist.md` 中处理。

## 0. 工具分工

- 长正文：用 Bash 处理，包括规模统计、窗口计划、分窗读取和关键词搜索。
- 小文件：用 Read 处理，包括 skill、references、配置、覆盖台账、角度 brief、修订记录、阶段稿和最终 JSON。
- 不要用 `Read` 扫全文，也不要用一次性 Bash 大输出读完整本书。
- 无论用 Bash 还是 Read，只有内容真正进入当前上下文，才算已读。

## 1. 抽取与统计

先把 PDF、EPUB、MOBI、AZW3、DOCX 等输入抽取为 UTF-8 文本；如果输入本身是 `.md` / `.txt`，也复制或规范化为统一正文文本。后续正文读取只针对抽取文本。

用 Bash 统计规模，不要用 `Read` 扫全文：

```bash
EXTRACT="output/<project>/text/_extract.txt"
wc -l "$EXTRACT"
wc -m "$EXTRACT"
```

记录 `source_total_lines`、`source_total_chars`。字符数用 `wc -m`，不要用 `wc -c` 字节数。

## 2. 覆盖率分档

根据 `source_total_chars` 写入 `coverage_policy` 与 `required_coverage_ratio`：

- `source_total_chars <= 150000`：必须全文读完，`required_coverage_ratio: 1.0`。
- `150000 < source_total_chars <= 200000`：至少覆盖 80%，`required_coverage_ratio: 0.8`。
- `source_total_chars > 200000`：至少覆盖 50%，`required_coverage_ratio: 0.5`。

超过 20 万字符时，50% 是最低覆盖率，不是只读前半本的许可。覆盖窗口必须分布到开头、中段、结尾和主要章节。即使字符覆盖达标，只要没有形成对全书问题、主线、核心概念、关键事实和结论边界的完整理解，也不能让 `coverage_check.passed=true`。

## 3. 分窗读取

硬规则：

- 长正文优先用 Bash（`sed` / `awk`）按窗口读取；Read 用于小文件和阶段稿，不用于扫整本抽取文本。
- 每窗不超过 **23000 字符**，写入 `chars_per_window: 23000`。
- 窗口按行号定位，但窗口大小按字符数控制；`source_total_chars`、`planned_chars`、`char_coverage_ratio` 都按字符数计算。
- “已读”只指窗口正文完整进入当前上下文，且没有 `<persisted-output>`、`Output too large`、`Full output saved to`、preview 截断等情况。
- Bash 执行成功、只写临时文件、只看 head/tail、只拿到 tool-results 路径，都不能算覆盖。
- 覆盖台账通过前，禁止写 `_angle_brief.json`、初稿、修订稿或 `raw.json`。

生成窗口计划：

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
  END { if (chars > 0) printf "%d\t%d\t%d\n", start, NR, chars }
' "$EXTRACT"
```

按计划逐窗读取：

```bash
EXTRACT="output/<project>/text/_extract.txt"
START=1
END=180
sed -n "${START},${END}p" "$EXTRACT" | awk '{print NR+('"$START"'-1) "\t" $0}'
```

如果输出被截断或落盘：将当前窗字符预算减半（23000 -> 11500 -> 5750 ...），重读同一区间；原窗口记为 `coverage_status: partial`，减半后的完整子窗口记为 `complete`。不要改用 `Read` 或跳读下一段。

## 4. 覆盖台账

读取正文前创建并持续更新：

```text
output/<project>/text/_coverage_ledger.json
```

顶层至少包含：

- `source_file`
- `source_total_lines`
- `source_total_chars`
- `read_strategy: bash_char_budget_window`
- `chars_per_window`
- `coverage_policy`
- `required_coverage_ratio`
- `planned_windows`
- `coverage_windows`
- `coverage_check`

每读完一窗，立即追加 `coverage_windows`，不要最后一次性补。单窗至少记录：

- `window_id`
- `read_tool: bash`
- `planned_range`
- `actual_read_range`
- `planned_chars`
- `coverage_status: complete | partial`
- `section_hint`
- `main_points_seen`
- `important_examples_seen`
- `relation_to_whole_book`
- `uncertainties`

台账是覆盖证明，不是摘要。`partial` 不能计入通过覆盖率。

## 5. 写稿前检查

只有满足以下条件，才能进入角度 brief 和写稿流程：

- `_coverage_ledger.json` 已保存，且 `coverage_check.passed=true` 与事实一致。
- 覆盖率达到当前分档要求，行覆盖率 `line_coverage_ratio` 和字符覆盖率 `char_coverage_ratio` 不虚高。
- 开头、中段、结尾和主要章节均已覆盖。
- 所有计入覆盖率的窗口都是 `coverage_status: complete`。
- 没有把 Bash 成功、输出落盘、preview、head/tail 当成已读。
- 已理解全书回答的问题、论证主线、关键事实/案例、核心冲突和不应夸大的边界。

## 6. 失败和切换

遇到以下情况，停止直接读法并建议切换：

- 字符窗口反复减半后仍无法完整进入上下文。
- 文档规模或复杂度超出单次 Agent 会话可可靠保持的上下文。
- 连续 Bash 读法仍频繁遗漏章节关系或论证链。
- 用户要求可审计证据链、短引文、限制条件和回查文件。
