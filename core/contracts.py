"""Contracts: enums, request/response data classes for the pipeline."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── Enums ──────────────────────────────────────────────────────

class StepName(str, enum.Enum):
    """Pipeline step identifiers."""
    STEP_1   = "step_1"
    STEP_1_5 = "step_1_5"
    STEP_2   = "step_2"
    STEP_3   = "step_3"
    STEP_4   = "step_4"
    STEP_5   = "step_5"
    STEP_6   = "step_6"
    AUTO     = "auto"


class JobStatus(str, enum.Enum):
    """Job lifecycle states."""
    PENDING    = "pending"
    RUNNING    = "running"
    COMPLETED  = "completed"
    SUCCEEDED  = "succeeded"
    FAILED     = "failed"
    CANCELED   = "canceled"


# ── Requests ───────────────────────────────────────────────────

@dataclass
class GenerationRequest:
    """Full pipeline generation request."""
    input_file: str
    output_dir: str
    target_length: int = 800
    num_segments: int = 10
    llm_server: str = ""
    llm_model: str = ""
    image_server: str = ""
    image_model: str = ""
    tts_server: str = ""
    voice: str = ""
    image_style_preset: str = ""
    image_size: str = "1024x1024"
    opening_image_style: str = ""
    enable_subtitles: bool = True
    bgm_filename: Optional[str] = None


@dataclass
class StepRequest:
    """Single-step execution request."""
    step: StepName
    project_output_dir: str = ""
    params: Dict[str, Any] = field(default_factory=dict)


# ── Responses ──────────────────────────────────────────────────

@dataclass
class PipelineResult:
    """Outcome of a full pipeline run."""
    success: bool = False
    message: str = ""
    project_output_dir: str = ""
    final_video: str = ""
    steps_completed: List[str] = field(default_factory=list)


@dataclass
class JobRecord:
    """Persisted job record for the job store."""
    job_id: str = ""
    job_type: str = ""
    status: JobStatus = JobStatus.PENDING
    payload_json: str = ""
    current_step: Optional[str] = None
    progress: float = 0.0
    error_json: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    step: str = ""
    project_dir: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


__all__ = [
    "StepName",
    "JobStatus",
    "GenerationRequest",
    "StepRequest",
    "PipelineResult",
    "JobRecord",
]
