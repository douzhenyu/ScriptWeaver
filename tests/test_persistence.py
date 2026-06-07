"""Tests for job persistence layer."""

import sqlite3
from dataclasses import replace

import pytest

from scriptweaver.domain.models import AdaptationJob
from scriptweaver.domain.workflow import AdaptationState
from scriptweaver.persistence.repository import (
    InMemoryJobRepository,
    JobRepository,
    SqliteJobRepository,
)


@pytest.fixture
def sqlite_repo() -> SqliteJobRepository:
    """In-memory SQLite repository for isolated tests."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    return SqliteJobRepository(conn)


@pytest.fixture
def memory_repo() -> InMemoryJobRepository:
    return InMemoryJobRepository()


def make_job(job_id: str = "job-001") -> AdaptationJob:
    return AdaptationJob(id=job_id)


# ── JobRepository protocol ──────────────────────────────────────────


def test_job_repository_is_protocol():
    """SqliteJobRepository must satisfy the JobRepository protocol."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    repo = SqliteJobRepository(conn)
    assert isinstance(repo, JobRepository)


def test_in_memory_repository_satisfies_protocol():
    """InMemoryJobRepository must satisfy the JobRepository protocol."""
    repo = InMemoryJobRepository()
    assert isinstance(repo, JobRepository)


# ── SQLite: save and get ────────────────────────────────────────────


def test_sqlite_save_and_get_job(sqlite_repo):
    job = make_job("job-001")
    sqlite_repo.save(job)

    loaded = sqlite_repo.get("job-001")
    assert loaded is not None
    assert loaded.id == "job-001"
    assert loaded.state == AdaptationState.CREATED


def test_sqlite_get_returns_none_for_unknown(sqlite_repo):
    assert sqlite_repo.get("nonexistent") is None


def test_sqlite_exists(sqlite_repo):
    assert not sqlite_repo.exists("job-001")
    sqlite_repo.save(make_job("job-001"))
    assert sqlite_repo.exists("job-001")


# ── SQLite: update ──────────────────────────────────────────────────


def test_sqlite_save_updates_existing_job(sqlite_repo):
    sqlite_repo.save(make_job("job-001"))
    updated = replace(make_job("job-001"), state=AdaptationState.CHAPTERS_UPLOADED)
    sqlite_repo.save(updated)

    loaded = sqlite_repo.get("job-001")
    assert loaded.state == AdaptationState.CHAPTERS_UPLOADED


# ── SQLite: data isolation ──────────────────────────────────────────


def test_sqlite_returns_independent_copy(sqlite_repo):
    sqlite_repo.save(make_job("job-001"))
    a = sqlite_repo.get("job-001")
    b = sqlite_repo.get("job-001")
    assert a is not b
    assert a == b


# ── In-memory repository ────────────────────────────────────────────


def test_memory_save_and_get(memory_repo):
    memory_repo.save(make_job("job-001"))
    loaded = memory_repo.get("job-001")
    assert loaded is not None
    assert loaded.id == "job-001"


def test_memory_get_returns_none_for_unknown(memory_repo):
    assert memory_repo.get("nonexistent") is None


def test_memory_exists(memory_repo):
    assert not memory_repo.exists("job-001")
    memory_repo.save(make_job("job-001"))
    assert memory_repo.exists("job-001")


def test_memory_returns_independent_copy(memory_repo):
    memory_repo.save(make_job("job-001"))
    a = memory_repo.get("job-001")
    b = memory_repo.get("job-001")
    assert a is not b
