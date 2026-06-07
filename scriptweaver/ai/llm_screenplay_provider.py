from __future__ import annotations

import dataclasses
from dataclasses import replace
from typing import Any

from scriptweaver.ai.provider import AIProviderInputError
from scriptweaver.domain.models import (
    AdaptationPlan,
    Beat,
    Chapter,
    SceneHeading,
    ScreenplayDraft,
    ScreenplayScene,
)
from scriptweaver.domain.screenplay_validation import (
    ScreenplayValidationError,
    validate_screenplay,
)
from scriptweaver.llm.client import StructuredLLMClient, StructuredLLMError


class AIProviderError(RuntimeError):
    """Raised when the LLM screenplay provider cannot produce a valid result."""


SYSTEM_PROMPT = """\
You are a professional screenplay writer adapting a novel into a screenplay. \
Given an adaptation plan and the original chapters, write a detailed, \
scene-by-scene screenplay draft.

Return a JSON object with exactly these keys:

- "scenes": list of scene objects, each with fields:
  id (string matching plan scene id),
  heading (object with: location, time, interior_exterior),
  source_chapter_indexes (list of ints),
  character_ids (list of strings),
  beats (list of beat objects)
- "revision_notes": list of strings with revision suggestions

A beat object has fields:
  type (one of: "action", "dialogue", "voiceover"),
  text (string — MUST be detailed and vivid, 1-3 sentences per beat),
  character_id (string, required for dialogue and voiceover, null for action)

CRITICAL — Content density requirements:
- Each scene MUST have 6-15 beats. Do NOT stop at 2-3 beats.
- Action beats: describe concrete movements, expressions, environmental details.
  Do NOT write one-liners like "He walks in." — describe HOW, the mood, the stakes.
- Dialogue beats: write natural, character-specific lines that reveal personality
  and advance the plot. Include subtext and emotional weight.
- Voiceover beats: reveal inner thoughts, memories, or thematic commentary.
- Mine the source chapters thoroughly — every important character moment,
  plot event, and emotional beat from the chapters should appear in the screenplay.
- Balance action and dialogue: aim for roughly 40% action, 40% dialogue, 20% voiceover.

IMPORTANT: Chapter indexes are 1-based. Use the EXACT source_chapter_indexes \
shown in the plan for each scene. For example, if the plan says \
"Source chapters: [1, 2]" you MUST use [1, 2], NOT [0, 1].
Character IDs must also match exactly those listed in the plan scene.
Scene IDs must match the plan scene IDs exactly.
The scenes array must be in the same order as the plan."""


def _field_names(cls: type) -> set[str]:
    return {field.name for field in dataclasses.fields(cls)}


def _filter_fields(cls: type, raw: dict[str, Any]) -> dict[str, Any]:
    allowed = _field_names(cls)
    return {k: v for k, v in raw.items() if k in allowed}


def _parse_heading(raw: dict[str, Any], label: str) -> SceneHeading:
    try:
        return SceneHeading(**_filter_fields(SceneHeading, raw))
    except TypeError as error:
        raise AIProviderError(
            f"Failed to parse {label}: {error}"
        ) from error


def _parse_beat(raw: dict[str, Any], label: str) -> Beat:
    try:
        return Beat(**_filter_fields(Beat, raw))
    except TypeError as error:
        raise AIProviderError(
            f"Failed to parse {label}: {error}"
        ) from error


def _parse_scene(raw: dict[str, Any], label: str) -> ScreenplayScene:
    heading_raw = raw.get("heading", {})
    if not isinstance(heading_raw, dict):
        heading_raw = {}
    heading = _parse_heading(heading_raw, f"{label}.heading")
    beats = [
        _parse_beat(b, f"{label}.beats[{i}]")
        for i, b in enumerate(raw.get("beats", []))
        if isinstance(b, dict)
    ]
    source_indexes = _normalize_chapter_indexes(
        raw.get("source_chapter_indexes", [])
    )
    return ScreenplayScene(
        id=raw.get("id", ""),
        heading=heading,
        source_chapter_indexes=source_indexes,
        character_ids=raw.get("character_ids", []),
        beats=beats,
    )


def _normalize_chapter_indexes(raw_indexes: Any) -> list[int]:
    """Auto-correct 0-based chapter indexes to 1-based when detected."""
    if not isinstance(raw_indexes, list):
        return []
    # Convert to ints, dropping non-numeric values
    result: list[int] = []
    for i in raw_indexes:
        if isinstance(i, (int, float)) and i == int(i):
            result.append(int(i))
    # If 0 is present the LLM used 0-based indexing — shift all by +1
    if 0 in result:
        result = [i + 1 for i in result]
    return result


def _align_scene_ids(
    draft: ScreenplayDraft,
    plan_scene_ids: list[str],
) -> ScreenplayDraft:
    """Override LLM-generated scene IDs with exact plan scene IDs.

    Scene order is preserved; IDs are assigned by position.
    If counts don't match the draft is returned unchanged
    (validation will catch the mismatch).
    """
    if len(draft.scenes) != len(plan_scene_ids):
        return draft

    corrected = [
        replace(scene, id=plan_id)
        for scene, plan_id in zip(draft.scenes, plan_scene_ids)
    ]
    return replace(draft, scenes=corrected)


class LLMScreenplayProvider:
    """Screenplay provider backed by a structured LLM client."""

    def __init__(self, llm_client: StructuredLLMClient) -> None:
        self._llm_client = llm_client

    def generate_screenplay(
        self,
        confirmed_plan: AdaptationPlan,
        chapters: list[Chapter],
    ) -> ScreenplayDraft:
        if not chapters:
            raise AIProviderInputError(
                "At least 1 chapter is required for screenplay generation"
            )

        user_prompt = self._build_user_prompt(confirmed_plan, chapters)
        plan_scene_ids = [s.id for s in confirmed_plan.scenes]

        try:
            raw = self._llm_client.generate_json(SYSTEM_PROMPT, user_prompt)
        except StructuredLLMError as error:
            raise AIProviderError(str(error)) from error
        except Exception as error:
            raise AIProviderError(
                f"LLM screenplay generation failed: {error}"
            ) from error

        draft = _align_scene_ids(
            self._parse_response(raw), plan_scene_ids
        )
        try:
            validate_screenplay(draft, confirmed_plan)
        except ScreenplayValidationError as error:
            # Retry once with validation error feedback
            retry_prompt = (
                f"{user_prompt}\n\n"
                f"Your previous response was invalid.\n"
                f"Validation error: {error}\n\n"
                f"CRITICAL: You MUST use exactly these scene IDs "
                f"in order: {plan_scene_ids}\n"
                f"Each scene's source_chapter_indexes and character_ids "
                f"must match the plan above. "
                f"Please fix all issues and return a corrected "
                f"screenplay JSON."
            )
            try:
                retry_raw = self._llm_client.generate_json(
                    SYSTEM_PROMPT, retry_prompt
                )
            except StructuredLLMError as retry_error:
                raise AIProviderError(str(retry_error)) from retry_error
            except Exception as retry_error:
                raise AIProviderError(
                    f"LLM screenplay retry failed: {retry_error}"
                ) from retry_error

            draft = _align_scene_ids(
                self._parse_response(retry_raw), plan_scene_ids
            )
            try:
                validate_screenplay(draft, confirmed_plan)
            except ScreenplayValidationError as retry_error:
                raise AIProviderError(str(retry_error)) from retry_error

        return draft

    @staticmethod
    def _build_user_prompt(
        confirmed_plan: AdaptationPlan,
        chapters: list[Chapter],
    ) -> str:
        parts: list[str] = ["## Adaptation Plan"]
        parts.append(f"Format: {confirmed_plan.target_format}")
        parts.append(f"Structure: {confirmed_plan.structure}")

        for scene in confirmed_plan.scenes:
            parts.append(
                f"\n### Scene {scene.scene_order}: {scene.title}\n"
                f"Purpose: {scene.dramatic_purpose}\n"
                f"Character IDs: {scene.character_ids}\n"
                f"Source chapters: {scene.source_chapter_indexes}\n"
                f"MUST use scene id='{scene.id}', "
                f"source_chapter_indexes={scene.source_chapter_indexes}, "
                f"character_ids={scene.character_ids}"
            )

        total_chapters = len(chapters)
        parts.append(
            "\n## Instructions\n"
            "For each scene you MUST use the EXACT scene id, "
            "source_chapter_indexes, and character_ids listed above. "
            "Chapter indexes are 1-based — use [1, 2], NOT [0, 1].\n\n"
            f"This novel has {total_chapters} chapters of substantial length. "
            "Your screenplay MUST be detailed and thorough:\n"
            "- Each scene needs 6-15 beats (NOT 2-3).\n"
            "- Action beats should be vivid 1-3 sentence descriptions.\n"
            "- Dialogue beats should be natural exchanges that reveal character.\n"
            "- Extract ALL key moments, conflicts, and emotional beats from the "
            "source chapters.\n"
            "- Do NOT summarize or skip — adapt the content fully."
        )

        # Only include chapters referenced by at least one plan scene.
        # Fall back to all chapters if no scene declares source_chapter_indexes.
        referenced_indexes: set[int] = set()
        for scene in confirmed_plan.scenes:
            referenced_indexes.update(scene.source_chapter_indexes)

        if referenced_indexes:
            relevant_chapters = [
                ch for ch in chapters if ch.index in referenced_indexes
            ]
        else:
            relevant_chapters = list(chapters)

        parts.append("\n## Source Chapters")
        for chapter in relevant_chapters:
            parts.append(
                f"\n### Chapter {chapter.index}: {chapter.title}\n"
                f"{chapter.content}"
            )

        return "\n".join(parts)

    @staticmethod
    def _parse_response(raw: dict[str, Any]) -> ScreenplayDraft:
        if "scenes" not in raw:
            raise AIProviderError(
                "Missing required key in LLM response: scenes"
            )
        if not isinstance(raw["scenes"], list):
            raise AIProviderError("'scenes' must be a list")

        scenes = [
            _parse_scene(s, f"scenes[{i}]")
            for i, s in enumerate(raw["scenes"])
            if isinstance(s, dict)
        ]

        revision_notes = raw.get("revision_notes", [])
        if not isinstance(revision_notes, list):
            revision_notes = []

        return ScreenplayDraft(
            scenes=scenes,
            revision_notes=list(revision_notes),
        )
