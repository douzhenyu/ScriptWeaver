from __future__ import annotations

import dataclasses
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
from scriptweaver.llm.client import StructuredLLMClient, StructuredLLMError


class AIProviderError(RuntimeError):
    """Raised when the LLM screenplay provider cannot produce a valid result."""


SYSTEM_PROMPT = """\
You are a screenplay writer. Given an adaptation plan and the original \
chapters, write a structured screenplay draft.

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
  text (string),
  character_id (string, required for dialogue and voiceover, null for action)

Generate at least 2 beats per scene. Use concrete, visual descriptions.
Every dialogue beat must reference a valid character_id from the scene."""


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
    heading = _parse_heading(raw.get("heading", {}), f"{label}.heading")
    beats = [
        _parse_beat(b, f"{label}.beats[{i}]")
        for i, b in enumerate(raw.get("beats", []))
    ]
    return ScreenplayScene(
        id=raw.get("id", ""),
        heading=heading,
        source_chapter_indexes=raw.get("source_chapter_indexes", []),
        character_ids=raw.get("character_ids", []),
        beats=beats,
    )


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

        try:
            raw = self._llm_client.generate_json(SYSTEM_PROMPT, user_prompt)
        except StructuredLLMError as error:
            raise AIProviderError(str(error)) from error
        except Exception as error:
            raise AIProviderError(
                f"LLM screenplay generation failed: {error}"
            ) from error

        return self._parse_response(raw)

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
                f"Source chapters: {scene.source_chapter_indexes}"
            )

        parts.append("\n## Source Chapters")
        for chapter in chapters:
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
        ]

        revision_notes = raw.get("revision_notes", [])
        if not isinstance(revision_notes, list):
            revision_notes = []

        return ScreenplayDraft(
            scenes=scenes,
            revision_notes=list(revision_notes),
        )
