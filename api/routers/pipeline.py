"""HTTP routes for synchronous pipeline execution."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_pipeline_service
from api.schemas import AutoRunRequest, StepRunRequest
from api.security import verify_api_token
from core.generation_config import VideoGenerationConfig
from core.pipeline.service import PipelineService


router = APIRouter(prefix="/v1/pipeline", tags=["pipeline"], dependencies=[Depends(verify_api_token)])


@router.post("/auto")
def run_auto(
    request: AutoRunRequest,
    service: PipelineService = Depends(get_pipeline_service),
) -> Dict[str, Any]:
    params = dict(request.params or {})
    try:
        config = VideoGenerationConfig.from_dict(params)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"invalid params: {exc}") from exc
    result = service.run_auto(config)
    return result


@router.post("/steps/{step}")
def run_step(
    step: float,
    request: StepRunRequest,
    service: PipelineService = Depends(get_pipeline_service),
) -> Dict[str, Any]:
    result = service.run_step(step=step, **(request.params or {}))
    return result
