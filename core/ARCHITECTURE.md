# core Architecture

## Goal

`core` is the shared business/runtime layer for all adapters (`cli`, `api`, future UI).
Keep orchestration in `pipeline`, business logic in `domain`, and all external systems in `infra`.

## Current Layout

```text
core/
├── __init__.py
├── config.py
├── contracts.py
├── generation_config.py
├── llm_gateway.py         # Domain-safe gateway to LLM text generation
├── prompts.py
├── shared.py
│
├── pipeline/              # Application orchestration
│   ├── __init__.py
│   ├── run_auto.py
│   ├── scanner.py
│   ├── service.py
│   └── steps.py
│
├── domain/                # Domain/business logic
│   ├── __init__.py
│   ├── composer.py
│   ├── docx_transform.py
│   ├── reader.py
│   └── summarizer.py
│
└── infra/                 # Infrastructure and external integrations
    ├── __init__.py
    ├── ai/                # Third-party AI provider adapters
    │   ├── __init__.py
    │   ├── image_client.py
    │   ├── llm_client.py
    │   └── tts_client.py  # Includes silence trimming helper
    ├── project_paths.py
    └── sqlite_store.py
```

## Dependency Rules

1. `domain/` must not import `core.infra`.
2. `pipeline/` may import `domain/`, `infra/`, and core shared modules.
3. `infra/` exports only infrastructure types/utilities.
4. Adapters (`cli/`, `api/`, `tools/`) should call `core.pipeline` as main entry.
