"""HTTP routes for async job submission/status."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_pipeline_service
from api.schemas import JobSubmitResponse, SubmitJobRequest
from api.security import verify_api_token
from core.pipeline.service import PipelineService


router = APIRouter(prefix="/v1/jobs", tags=["jobs"], dependencies=[Depends(verify_api_token)])


@router.post("")
def submit_job(
    request: SubmitJobRequest,
    service: PipelineService = Depends(get_pipeline_service),
) -> JobSubmitResponse:
    job_id = service.submit_job(job_type=request.job_type, payload=request.payload or {})
    return JobSubmitResponse(job_id=job_id, accepted=bool(job_id))


@router.get("/{job_id}")
def get_job_status(
    job_id: str,
    service: PipelineService = Depends(get_pipeline_service),
) -> Dict[str, Any]:
    status_payload = service.get_job_status(job_id)
    if status_payload is None:
        raise HTTPException(status_code=404, detail="job not found")
    return status_payload
