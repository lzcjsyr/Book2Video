# core Architecture

## Goal

`core` is the shared business/runtime layer for all adapters (`cli`, future UI).
Keep orchestration in `pipeline`, business logic in `domain`, and all external systems in `infra`.

## Current Layout

```text
core/
├── __init__.py
├── config.py
├── startup.py             # CLI startup validation (provider resolution)
├── llm_gateway.py         # Domain-safe gateway to LLM text generation
├── media_gateway.py       # Domain-safe gateway to media infrastructure
├── prompts.py
├── shared.py
│
├── pipeline/              # Application orchestration
│   ├── __init__.py
│   ├── run_auto.py
│   ├── scanner.py
│   └── steps.py
│
├── domain/                # Domain/business logic
│   ├── __init__.py
│   ├── composer.py
│   ├── docx_transform.py
│   ├── reader.py
│   ├── subtitles.py
│   └── summarizer.py
│
└── infra/                 # Infrastructure and external integrations
    ├── __init__.py
    ├── ai/                # Third-party AI provider adapters
    │   ├── __init__.py
    │   ├── image_client.py
    │   ├── llm_client.py
    │   └── tts_client.py  # Includes silence trimming helper
    ├── media/             # Low-level media operation adapters
    │   ├── __init__.py
    │   ├── exporter.py
    │   └── ffmpeg.py
    └── project_paths.py
```

## Dependency Rules

1. `domain/` must not import `core.infra`.
2. `pipeline/` may import `domain/`, `infra/`, and core shared modules.
3. `infra/` exports only infrastructure types/utilities.
4. Adapters (`cli/`, future UI) should call `core.pipeline` as main entry.
