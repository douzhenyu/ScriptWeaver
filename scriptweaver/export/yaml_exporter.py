from __future__ import annotations

from typing import Any

import yaml

from scriptweaver.domain.models import AdaptationJob


SCHEMA_VERSION = "1.0"


def _build_source(job: AdaptationJob) -> dict[str, Any]:
    return {
        "source_type": "novel_chapters",
        "chapter_count": len(job.chapters),
        "chapters": [
            {
                "index": chapter.index,
                "title": chapter.title,
            }
            for chapter in job.chapters
        ],
    }


def _or_none(value: Any) -> Any:
    if value is None:
        return None
    return value.to_dict()


def export_job_to_yaml(
    job: AdaptationJob,
    metadata: dict[str, str],
) -> str:
    doc: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "metadata": metadata,
        "source": _build_source(job),
        "ai_analysis": _or_none(job.ai_analysis),
        "confirmed_analysis": _or_none(job.confirmed_analysis),
        "user_confirmations": _or_none(job.user_confirmations),
        "adaptation_plan": _or_none(job.adaptation_plan),
        "screenplay": _or_none(job.screenplay_draft),
        "revision_notes": (
            list(job.screenplay_draft.revision_notes)
            if job.screenplay_draft is not None
            else []
        ),
    }

    return yaml.dump(
        doc,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
