from __future__ import annotations

import json
import sqlite3
from copy import deepcopy
from dataclasses import fields
from typing import Any, Protocol, runtime_checkable

from scriptweaver.domain.models import AdaptationJob


def _job_to_dict(job: AdaptationJob) -> dict[str, Any]:
    """Serialize an AdaptationJob to a JSON-compatible dict."""
    return job.to_dict()


def _job_from_dict(data: dict[str, Any]) -> AdaptationJob:
    """Deserialize an AdaptationJob from a JSON-compatible dict."""
    from scriptweaver.domain.models import Chapter
    from scriptweaver.domain.workflow import AdaptationState

    field_names = {f.name for f in fields(AdaptationJob)}
    filtered: dict[str, Any] = {
        k: v for k, v in data.items() if k in field_names
    }
    # Convert state from string back to enum
    if "state" in filtered and isinstance(filtered["state"], str):
        filtered["state"] = AdaptationState(filtered["state"])
    # Convert chapter dicts back to Chapter objects
    if "chapters" in filtered and isinstance(filtered["chapters"], list):
        filtered["chapters"] = [
            Chapter(**ch) if isinstance(ch, dict) else ch
            for ch in filtered["chapters"]
        ]
    return AdaptationJob(**filtered)


@runtime_checkable
class JobRepository(Protocol):
    """Abstract storage for adaptation jobs."""

    def save(self, job: AdaptationJob) -> None:
        """Persist a job. Creates or updates."""
        ...

    def get(self, job_id: str) -> AdaptationJob | None:
        """Retrieve a job by ID. Returns None if not found."""
        ...

    def exists(self, job_id: str) -> bool:
        """Check whether a job exists."""
        ...

    def list_all(self) -> list[dict[str, str]]:
        """List all jobs with id and state. Lightweight summary."""
        ...

    def delete(self, job_id: str) -> bool:
        """Delete a job by ID. Returns True if it existed."""
        ...


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    data TEXT NOT NULL
)
"""

UPSERT_SQL = """
INSERT INTO jobs (id, state, data)
VALUES (?, ?, ?)
ON CONFLICT(id) DO UPDATE SET state = excluded.state, data = excluded.data
"""

SELECT_SQL = "SELECT data FROM jobs WHERE id = ?"
EXISTS_SQL = "SELECT 1 FROM jobs WHERE id = ?"
LIST_SQL = "SELECT id, state FROM jobs ORDER BY id"
DELETE_SQL = "DELETE FROM jobs WHERE id = ?"


class SqliteJobRepository:
    """SQLite-backed job repository.

    Jobs are serialised as JSON in a TEXT column for simplicity —
    no ORM, no migrations beyond CREATE TABLE IF NOT EXISTS.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection
        self._conn.execute(CREATE_TABLE_SQL)
        self._conn.commit()

    def save(self, job: AdaptationJob) -> None:
        data_json = json.dumps(
            _job_to_dict(job), ensure_ascii=False, sort_keys=True
        )
        self._conn.execute(
            UPSERT_SQL,
            (job.id, job.state.value, data_json),
        )
        self._conn.commit()

    def get(self, job_id: str) -> AdaptationJob | None:
        cursor = self._conn.execute(SELECT_SQL, (job_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        data = json.loads(row[0])
        return _job_from_dict(data)

    def exists(self, job_id: str) -> bool:
        cursor = self._conn.execute(EXISTS_SQL, (job_id,))
        return cursor.fetchone() is not None

    def list_all(self) -> list[dict[str, str]]:
        rows = self._conn.execute(LIST_SQL).fetchall()
        return [{"id": r[0], "state": r[1]} for r in rows]

    def delete(self, job_id: str) -> bool:
        cursor = self._conn.execute(DELETE_SQL, (job_id,))
        self._conn.commit()
        return cursor.rowcount > 0


class InMemoryJobRepository:
    """In-memory job repository backed by a plain dict.

    Returns deep copies on read so callers cannot accidentally mutate
    stored state.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, AdaptationJob] = {}

    def save(self, job: AdaptationJob) -> None:
        self._jobs[job.id] = deepcopy(job)

    def get(self, job_id: str) -> AdaptationJob | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        return deepcopy(job)

    def exists(self, job_id: str) -> bool:
        return job_id in self._jobs

    def list_all(self) -> list[dict[str, str]]:
        return [
            {"id": jid, "state": job.state.value}
            for jid, job in self._jobs.items()
        ]

    def delete(self, job_id: str) -> bool:
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False
