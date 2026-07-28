# 文件与输出契约

## 过程文件

最终 `raw.json` 同目录只需要：

```text
raw.json
```

`raw.json` 是唯一必需交付物。`_extract.md` 可作为长文缓存；其余台账和 brief 默认在当前上下文中完成，只有调试需要时才落盘。不要创建轮次稿、评分稿、subagent 任务包或多版本正文。

## 带货 brief

commerce brief 默认只存在于当前上下文；调试时可保存为 `_commerce_brief.json`：

```json
{
  "source_name": "《作品名》",
  "core_audience": "此刻最容易被本书打动的一类人",
  "life_moment": "一个具体生活瞬间",
  "emotional_engine": "relief|recognition|curiosity|awe|hope|ambition|nostalgia|belonging|indignation",
  "tension_source": "观众旧理解与本书新解释的落差",
  "unspoken_emotion": "与主发动机一致的真实感受",
  "piercing_truth": "有原书支撑的刺痛判断",
  "emotional_promise": "从什么情绪走向什么情绪",
  "free_payoff": "视频完整交付的故事、观点或反转",
  "why_this_book": {"reason": "本书独有的购买理由", "evidence_ids": ["E03"]},
  "objection": {"concern": "...", "answer": "...", "evidence_ids": ["E04"]},
  "emotional_turns": [
    {"before": "...", "source_detail": "...", "after": "...", "evidence_ids": ["E02"]}
  ],
  "cta_boundary": {"mode": "product_card|search_title|none", "allowed": "..."},
  "evidence_ids": ["E01"]
}
```

## 最终 raw JSON

只能包含以下 7 个字段：

```json
{
  "source_name": "《作品名》",
  "video_titles": ["3条发布标题候选"],
  "cover_titles": ["3条封面主标题，10字以内"],
  "cover_subtitles": ["3条封面副标题，15字以内"],
  "golden_quotes": ["3条开场金句"],
  "content": "完整纯口播终稿，保留自然段落换行",
  "total_length": 0
}
```

- 不增加分析、评分、受众或 CTA 等额外字段。
- `source_name` 使用书名号，不带文件后缀。
- 四个候选数组各正好 3 条，互不重复；相同下标组成一套情绪承诺一致的创意。
- `content` 是唯一口播终稿；若调试时保存了 `_draft_final.txt`，两者必须逐字一致，仅可统一行尾和清理首尾空白。
- `total_length` 为 Python `len(content)`。
- 用 `json.dump(..., ensure_ascii=False, indent=2)` 写入，再运行 `scripts/validate_raw.py`。
