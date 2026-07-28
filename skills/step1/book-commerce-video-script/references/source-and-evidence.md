# 资料与证据

## 抽取

优先使用项目现有文档读取能力获取可检索全文。长文或需要重复定位时，可在最终 `raw.json` 同目录按需缓存为 `_extract.md`，并记录源文件名、格式和抽取异常；它不是必需交付物。

不要用目录、封底简介或网上摘要代替原书。外部信息只能用于核验，不能偷偷混入原书观点。

## 覆盖

按全文字符分窗阅读，单窗最多 23000 字符；若工具输出截断，立即减半。先建立全书章节地图，再用最多 12 个窗口做有界证据采样：

- 开头与作者真正想解决的问题；
- 与带货情绪切口直接相关的章节；
- 主要人物、故事、冲突或论证；
- 中段的重要转折；
- 反例、限制和可能推翻主判断的材料；
- 结尾与作者最终落点。

六章以内逐章覆盖；更多章节时，覆盖开头、结尾、核心相关章节、中段转折和至少一个反例。源文件可读但情绪角度较弱时使用中性推荐模式；只有抽取失败或正文不可读时才失败。

`_coverage_ledger.json`：

```json
{
  "source_path": "/absolute/path/book.epub",
  "extract_path": "/absolute/path/_extract.md",
  "windows": [
    {"start": 1, "end": 23000, "status": "read", "main_points": ["..."]}
  ],
  "major_sections": [{"name": "...", "covered": true}],
  "sampling_basis": "chapter_map_and_relevance",
  "coverage_check": {"passed": true, "missing": [], "limitations": []}
}
```

## 证据库

只保留 5-8 条写稿会用到的高价值材料：

```json
{
  "source_name": "《书名》",
  "claims": [
    {
      "id": "E01",
      "claim": "可用于口播的事实、故事或判断",
      "support": "原书中的人物、情节、数据或论证",
      "location": "章节或字符位置",
      "confidence": "high",
      "human_detail": "动作、选择、关系变化、冲突或可感知细节",
      "audience_mirror": "它照见目标观众的哪一刻",
      "belief_before": "观众原先可能怎样理解",
      "belief_after": "本书让理解怎样改变",
      "ownership_payload": "只有读原书才能继续获得的具体价值",
      "limits": "不能怎样夸大"
    }
  ],
  "book_only_value": [
    {"reader_need": "...", "book_delivers": "...", "evidence_ids": ["E01"]}
  ],
  "unsafe_or_unverified": ["不得写入正文的说法"]
}
```

正文的事实判断、故事和购买理由都要能回到证据 ID。区分原书事实、作者解释和写稿者推断；不要为了煽情改写事实。
