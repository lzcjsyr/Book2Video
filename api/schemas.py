"""Pydantic request/response schemas for API adapters."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AutoRunRequest(BaseModel):
    """Run full pipeline synchronously."""

    params: Dict[str, Any] = Field(default_factory=dict)


class StepRunRequest(BaseModel):
    """Run single step synchronously."""

    params: Dict[str, Any] = Field(default_factory=dict)


class SubmitJobRequest(BaseModel):
    """Submit async job for future worker execution."""

    job_type: str = Field(default="auto")
    payload: Dict[str, Any] = Field(default_factory=dict)


class JobSubmitResponse(BaseModel):
    job_id: Optional[str] = None
    accepted: bool


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    data: Dict[str, Any] = Field(default_factory=dict)

