# MinerU PDF Extraction

用于投资、商业、行业报告、券商研报、财报解读等 **表格密集或版式复杂 PDF**。本 reference 只负责抽取层；抽取完成后必须回到 `reading-strategy.md` 的 Bash 字符窗口阅读流程。

## 触发条件

仅在以下情况使用 MinerU：

- 输入是 PDF，且属于投资、商业、行业报告、研报、财报、招股书等报告类材料。
- PDF 含复杂表格、图表、公式、多栏排版或扫描页。
- 常规 `pdftotext` / `pandoc` / `textutil` 抽取后表格错乱、页眉页脚污染严重或段落顺序不可读。
- 用户明确要求保留表格结构。

普通文字型 PDF、EPUB、DOCX、TXT 不默认使用 MinerU。

## 调用优先级

优先使用 `mineru-open-api` CLI，因为命令和输出路径更容易被 Agent 审计。若项目已有稳定 API 封装，也可以直接调用 MinerU 精准解析 API。

复杂报告优先使用精准解析能力，不使用轻量解析作为最终抽取依据。

## CLI 调用方式

首次使用先确认 CLI 和 Token：

```bash
mineru-open-api version
mineru-open-api auth --show || mineru-open-api auth
```

复杂报告使用精准解析：

```bash
mineru-open-api extract "$INPUT_FILE" \
  --model vlm \
  --ocr \
  --table \
  -f md,json,html \
  -o "$TEXT_DIR/_mineru/"
```

如果只是小文件快速预览，可用 `flash-extract`，但不能作为复杂表格 PDF 的最终抽取依据：

```bash
mineru-open-api flash-extract "$INPUT_FILE" -o "$TEXT_DIR/_mineru/"
```

## API 调用方式

仅在项目已有 API 封装或需要服务端集成时使用。最小流程：

1. `POST https://mineru.net/api/v4/extract/task`，`Authorization: Bearer <token>`，请求体包含 `url`、`model_version: "vlm"`、`enable_table: true`、`is_ocr: true`。
2. 用返回的 `task_id` 轮询 `GET https://mineru.net/api/v4/extract/task/{task_id}`。
3. `state == "done"` 后下载 `full_zip_url`，解压到 `$TEXT_DIR/_mineru/`。
4. 记录 `_mineru_manifest.json`，再生成 `{extract_path}`。

## 推荐落盘

所有 MinerU 产物保存到最终 raw JSON 同级目录下的 `_mineru/`：

```text
text/_mineru/
  full.md
  full.zip
  content_list.json
  _mineru_manifest.json
```

`_mineru_manifest.json` 至少记录：

```json
{
  "tool": "mineru-open-api|mineru-api",
  "mode": "precision",
  "model": "vlm",
  "input_file": "",
  "output_dir": "_mineru",
  "status": "success|failed",
  "notes": []
}
```

## 抽取后处理

1. 从 MinerU Markdown 或结构化 JSON 生成 `{extract_path}`。
2. 保留表格的标题、行列含义、关键数字和单位；不要把表格压成无法理解的碎片。
3. 删除明显重复页眉页脚、页码、版权水印和导航噪声。
4. 在 `_mineru_manifest.json` 里记录清洗方式。
5. 然后立刻回到 `reading-strategy.md`：统计 `wc -l` / `wc -c`，制定每窗不超过 23000 字符的 Bash 阅读计划，建立覆盖台账。

## 硬规则

- MinerU 解析成功不等于读完。
- 只看 MinerU 输出目录、zip、Markdown 文件大小或 API 状态，不能算覆盖。
- 不能跳过 Bash 阅读窗口和 `_coverage_ledger.json`。
- 如果 MinerU 输出质量差，必须换常规抽取、调整 MinerU 模式或停止并说明失败原因。
