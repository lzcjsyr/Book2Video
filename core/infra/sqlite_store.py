"""SQLite-backed job storage for future async execution."""

import datetime
import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.contracts import JobStatus
from core.contracts import JobRecord


class JobStoreSQLite:
    """Persist lightweight job and event records in SQLite."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    current_step TEXT,
                    progress REAL NOT NULL DEFAULT 0.0,
                    error_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS job_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    ts TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    meta_json TEXT,
                    FOREIGN KEY (job_id) REFERENCES jobs(id)
                )
                """
            )

    def submit_job(self, job_type: str, payload: Dict[str, Any]) -> JobRecord:
        now = datetime.datetime.now().isoformat()
        job_id = uuid.uuid4().hex
        payload_json = json.dumps(payload, ensure_ascii=False)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs (id, type, status, payload_json, current_step, progress, error_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    job_type,
                    JobStatus.PENDING.value,
                    payload_json,
                    None,
                    0.0,
                    None,
                    now,
                    now,
                ),
            )
        return self.get_job(job_id)  # type: ignore[return-value]

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        return JobRecord(
            job_id=row["id"],
            job_type=row["type"],
            status=JobStatus(row["status"]),
            payload_json=row["payload_json"],
            current_step=row["current_step"],
            progress=float(row["progress"] or 0.0),
            error_json=row["error_json"],
            created_at=row["created_at"] or "",
            updated_at=row["updated_at"] or "",
            started_at=row["started_at"],
            finished_at=row["finished_at"],
        )

    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        *,
        current_step: Optional[str] = None,
        progress: Optional[float] = None,
        error: Optional[Dict[str, Any]] = None,
    ) -> None:
        now = datetime.datetime.now().isoformat()
        error_json = json.dumps(error, ensure_ascii=False) if error is not None else None
        updates = ["status = ?", "updated_at = ?"]
        values: List[Any] = [status.value, now]

        if current_step is not None:
            updates.append("current_step = ?")
            values.append(current_step)
        if progress is not None:
            updates.append("progress = ?")
            values.append(progress)
        if error is not None:
            updates.append("error_json = ?")
            values.append(error_json)
        if status == JobStatus.RUNNING:
            updates.append("started_at = COALESCE(started_at, ?)")
            values.append(now)
        if status in (JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELED):
            updates.append("finished_at = ?")
            values.append(now)

        values.append(job_id)
        query = f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?"
        with self._connect() as conn:
            conn.execute(query, values)

    def append_event(
        self,
        job_id: str,
        level: str,
        message: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        now = datetime.datetime.now().isoformat()
        meta_json = json.dumps(meta, ensure_ascii=False) if meta is not None else None
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO job_events (job_id, ts, level, message, meta_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (job_id, now, level, message, meta_json),
            )

    def list_events(self, job_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT ts, level, message, meta_json FROM job_events WHERE job_id = ? ORDER BY id ASC",
                (job_id,),
            ).fetchall()
        events: List[Dict[str, Any]] = []
        for row in rows:
            meta_json = row["meta_json"]
            events.append(
                {
                    "ts": row["ts"],
                    "level": row["level"],
                    "message": row["message"],
                    "meta": json.loads(meta_json) if meta_json else None,
                }
            )
        return events


__all__ = ["JobStoreSQLite"]
