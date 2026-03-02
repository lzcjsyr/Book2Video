"""Dependency wiring for FastAPI adapters."""

import os
from functools import lru_cache

from core.infra.sqlite_store import JobStoreSQLite
from core.pipeline.service import PipelineService


def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@lru_cache(maxsize=1)
def get_pipeline_service() -> PipelineService:
    jobs_db = os.path.join(_project_root(), "output", ".jobs", "pipeline_jobs.sqlite3")
    job_store = JobStoreSQLite(jobs_db)
    return PipelineService(job_store=job_store)
