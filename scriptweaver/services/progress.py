"""Lightweight in-memory progress tracking for long-running operations.

Providers and services call progress() during lengthy steps.
The API exposes GET /jobs/{id}/progress for the frontend to poll.

Usage:
    from scriptweaver.services.progress import with_progress
    with_progress("demo-001", lambda msg: ...)
    # Inside the block, progress("message") records the message.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from contextvars import ContextVar

_progress: dict[str, str] = {}
_lock = threading.Lock()

_current_job: ContextVar[str | None] = ContextVar("current_job", default=None)


def progress(message: str) -> None:
    """Record a progress message for the current job."""
    job_id = _current_job.get()
    if job_id is None:
        return
    with _lock:
        _progress[job_id] = message


from typing import TypeVar as _TypeVar

_T = _TypeVar("_T")


def with_progress(job_id: str, fn: Callable[[], _T]) -> _T:
    """Execute fn with progress tracking scoped to job_id. Returns fn's result."""
    token = _current_job.set(job_id)
    try:
        return fn()
    finally:
        _current_job.reset(token)


def get_progress(job_id: str) -> str:
    """Get the latest progress message for a job."""
    with _lock:
        return _progress.get(job_id, "")


def clear_progress(job_id: str) -> None:
    """Remove progress tracking for a completed job."""
    with _lock:
        _progress.pop(job_id, None)
