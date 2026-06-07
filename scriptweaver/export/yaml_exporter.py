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


def export_screenplay_to_text(job: AdaptationJob) -> str:
    """Export screenplay as human-readable text format."""
    draft = job.screenplay_draft
    if draft is None or not draft.scenes:
        return ""

    lines: list[str] = []
    # Build character name lookup from analysis
    char_names: dict[str, str] = {}
    analysis = job.confirmed_analysis or job.ai_analysis
    if analysis:
        for c in analysis.characters:
            char_names[c.id] = c.name

    for scene in draft.scenes:
        h = scene.heading
        loc = h.location if h else ""
        t = h.time if h else ""
        ie = h.interior_exterior if h else ""
        lines.append(f"\n{'='*50}")
        lines.append(f"场景: {loc} - {t} ({ie})")
        lines.append(f"{'='*50}\n")

        for beat in scene.beats:
            btype = beat.type or "action"
            if btype == "action":
                lines.append(f"  {beat.text}")
            elif btype == "dialogue":
                name = char_names.get(
                    beat.character_id or "", beat.character_id or "?"
                )
                lines.append(f"  {name}：{beat.text}")
            elif btype == "voiceover":
                name = char_names.get(
                    beat.character_id or "", beat.character_id or "?"
                )
                lines.append(f"  [{name} 旁白]：{beat.text}")
            else:
                lines.append(f"  [{btype}] {beat.text}")
            lines.append("")

    if draft.revision_notes:
        lines.append(f"\n{'='*50}")
        lines.append("修订建议：")
        for note in draft.revision_notes:
            lines.append(f"  - {note}")

    return "\n".join(lines)
