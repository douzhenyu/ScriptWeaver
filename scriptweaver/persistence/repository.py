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
    from scriptweaver.domain.models import (
        AdaptationPlan,
        AIAnalysis,
        Beat,
        CandidateScene,
        Chapter,
        Character,
        CharacterRelationship,
        Conflict,
        KeyEvent,
        PlanReviewQuestion,
        SceneHeading,
        ScenePlan,
        ScreenplayDraft,
        ScreenplayScene,
        Theme,
        Uncertainty,
        UncertaintyOption,
        UserConfirmations,
    )
    from scriptweaver.domain.workflow import AdaptationState

    field_names = {f.name for f in fields(AdaptationJob)}
    filtered: dict[str, Any] = {
        k: v for k, v in data.items() if k in field_names
    }
    if "state" in filtered and isinstance(filtered["state"], str):
        filtered["state"] = AdaptationState(filtered["state"])

    # Reconstruct chapters
    if "chapters" in filtered and isinstance(filtered["chapters"], list):
        filtered["chapters"] = [
            Chapter(**ch) if isinstance(ch, dict) else ch
            for ch in filtered["chapters"]
        ]

    # Reconstruct AIAnalysis
    for key in ("ai_analysis", "confirmed_analysis"):
        val = filtered.get(key)
        if isinstance(val, dict):
            filtered[key] = AIAnalysis(
                characters=[
                    Character(**c)
                    for c in val.get("characters", [])
                    if isinstance(c, dict)
                ],
                relationships=[
                    CharacterRelationship(**r)
                    for r in val.get("relationships", [])
                    if isinstance(r, dict)
                ],
                key_events=[
                    KeyEvent(**e)
                    for e in val.get("key_events", [])
                    if isinstance(e, dict)
                ],
                conflicts=[
                    Conflict(**c)
                    for c in val.get("conflicts", [])
                    if isinstance(c, dict)
                ],
                themes=[
                    Theme(**t)
                    for t in val.get("themes", [])
                    if isinstance(t, dict)
                ],
                candidate_scenes=[
                    CandidateScene(**s)
                    for s in val.get("candidate_scenes", [])
                    if isinstance(s, dict)
                ],
                uncertainties=[
                    Uncertainty(
                        **{k: v for k, v in u.items() if k != "options"},
                        options=[
                            UncertaintyOption(**o)
                            for o in u.get("options", [])
                            if isinstance(o, dict)
                        ],
                    )
                    for u in val.get("uncertainties", [])
                    if isinstance(u, dict)
                ],
            )

    # Reconstruct AdaptationPlan
    plan = filtered.get("adaptation_plan")
    if isinstance(plan, dict):
        from scriptweaver.domain.models import AdaptationDecision

        def _parse_decisions(raw):
            return [
                AdaptationDecision(**d)
                for d in (raw or [])
                if isinstance(d, dict)
            ]

        filtered["adaptation_plan"] = AdaptationPlan(
            target_format=plan.get("target_format", ""),
            structure=plan.get("structure", ""),
            scenes=[
                ScenePlan(
                    **{k: v for k, v in s.items()
                       if k not in (
                           "compression_choices", "merge_choices",
                           "rewrite_choices", "review_questions",
                       )},
                    compression_choices=_parse_decisions(
                        s.get("compression_choices")
                    ),
                    merge_choices=_parse_decisions(
                        s.get("merge_choices")
                    ),
                    rewrite_choices=_parse_decisions(
                        s.get("rewrite_choices")
                    ),
                    review_questions=[
                        PlanReviewQuestion(**q)
                        for q in s.get("review_questions", [])
                        if isinstance(q, dict)
                    ],
                )
                for s in plan.get("scenes", [])
                if isinstance(s, dict)
            ],
            review_questions=[
                PlanReviewQuestion(**q)
                for q in plan.get("review_questions", [])
                if isinstance(q, dict)
            ],
        )

    # Reconstruct ScreenplayDraft
    draft = filtered.get("screenplay_draft")
    if isinstance(draft, dict):
        filtered["screenplay_draft"] = ScreenplayDraft(
            scenes=[
                ScreenplayScene(
                    id=s.get("id", ""),
                    heading=SceneHeading(
                        **s.get("heading", {})
                    ) if isinstance(s.get("heading"), dict)
                    else SceneHeading(location="", time="",
                                      interior_exterior="INT"),
                    source_chapter_indexes=s.get(
                        "source_chapter_indexes", []
                    ),
                    character_ids=s.get("character_ids", []),
                    beats=[
                        Beat(**b)
                        for b in s.get("beats", [])
                        if isinstance(b, dict)
                    ],
                )
                for s in draft.get("scenes", [])
                if isinstance(s, dict)
            ],
            revision_notes=list(draft.get("revision_notes", [])),
        )

    # Reconstruct UserConfirmations
    uc = filtered.get("user_confirmations")
    if isinstance(uc, dict):
        from scriptweaver.domain.models import UncertaintyResolution

        filtered["user_confirmations"] = UserConfirmations(
            uncertainty_resolutions=[
                UncertaintyResolution(**r)
                for r in uc.get("uncertainty_resolutions", [])
                if isinstance(r, dict)
            ],
            accepted_character_ids=list(
                uc.get("accepted_character_ids", [])
            ),
            required_plot_points=list(
                uc.get("required_plot_points", [])
            ),
            notes=uc.get("notes"),
        )

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
