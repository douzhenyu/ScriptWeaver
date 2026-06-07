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


PER_SCENE_SYSTEM_PROMPT = """\
You are a professional screenplay writer. Write a detailed screenplay scene \
based on the plan and source chapters provided.

Return a JSON object with exactly these keys:

- "heading": object with: location, time, interior_exterior
- "beats": list of beat objects (6-15 beats, must NOT be fewer than 4)
- "source_chapter_indexes": list of ints — copy EXACTLY from the plan
- "character_ids": list of strings — copy EXACTLY from the plan
- "revision_notes": list of 1-2 brief revision suggestions for this scene

A beat object has fields:
  type (one of: "action", "dialogue", "voiceover"),
  text (string — MUST be detailed and vivid, 1-3 sentences per beat),
  character_id (string, required for dialogue and voiceover, null for action)

CRITICAL — Content density:
- Each scene MUST have 6-15 beats. Do NOT stop at 2-3.
- Action beats: concrete movements, expressions, environmental details.
- Dialogue beats: natural, character-specific lines with subtext.
- Voiceover beats: inner thoughts, memories, thematic commentary.
- Balance: roughly 40% action, 40% dialogue, 20% voiceover.

IMPORTANT: Copy source_chapter_indexes and character_ids EXACTLY from the \
plan above. Chapter indexes are 1-based."""


class LLMScreenplayProvider:
    """Screenplay provider backed by a structured LLM client.

    Uses per-scene generation for 2+ scenes: each scene gets its own
    LLM call with only the relevant chapters, producing richer output.
    Single-scene plans use the original single-call path.
    """

    PER_SCENE_THRESHOLD = 2

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

        plan_scenes = confirmed_plan.scenes
        if not plan_scenes:
            raise AIProviderInputError(
                "Plan must have at least 1 scene"
            )

        # Single scene or few scenes: original single-call path
        if len(plan_scenes) < self.PER_SCENE_THRESHOLD:
            return self._generate_single_call(confirmed_plan, chapters)

        # Per-scene generation for better focus
        return self._generate_per_scene(confirmed_plan, chapters)

    # ── Single-call path ──────────────────────────────────────

    def _generate_single_call(
        self,
        confirmed_plan: AdaptationPlan,
        chapters: list[Chapter],
    ) -> ScreenplayDraft:
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
            draft = self._retry_single_call(
                user_prompt, plan_scene_ids, confirmed_plan, error
            )
        return draft

    def _retry_single_call(
        self,
        user_prompt: str,
        plan_scene_ids: list[str],
        confirmed_plan: AdaptationPlan,
        error: ScreenplayValidationError,
    ) -> ScreenplayDraft:
        retry_prompt = (
            f"{user_prompt}\n\n"
            f"Your previous response was invalid.\n"
            f"Validation error: {error}\n\n"
            f"CRITICAL: You MUST use exactly these scene IDs "
            f"in order: {plan_scene_ids}\n"
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

    # ── Per-scene path ────────────────────────────────────────

    def _generate_per_scene(
        self,
        confirmed_plan: AdaptationPlan,
        chapters: list[Chapter],
    ) -> ScreenplayDraft:
        from scriptweaver.services.progress import progress as _p

        chapters_by_index = {ch.index: ch for ch in chapters}
        scenes: list[ScreenplayScene] = []
        all_notes: list[str] = []
        plan_scenes = confirmed_plan.scenes

        for i, plan_scene in enumerate(plan_scenes):
            _p(f"正在生成第 {i+1}/{len(plan_scenes)} 场：{plan_scene.title}")
            scene, notes = self._generate_scene(
                plan_scene, chapters_by_index,
            )
            scene = replace(scene, id=plan_scene.id)
            scenes.append(scene)
            all_notes.extend(notes)

        draft = ScreenplayDraft(
            scenes=scenes,
            revision_notes=all_notes,
        )
        try:
            validate_screenplay(draft, confirmed_plan)
        except ScreenplayValidationError as error:
            # Retry: find the failing scene and regenerate it
            _p(f"验证未通过，正在修正：{error}")
            err_msg = str(error)
            # Try to extract scene id from error message
            for j, s in enumerate(scenes):
                if s.id in err_msg:
                    _p(f"重新生成场景：{s.id}")
                    retry_scene, retry_notes = self._generate_scene(
                        plan_scenes[j], chapters_by_index,
                    )
                    scenes[j] = replace(retry_scene, id=s.id)
                    all_notes.extend(retry_notes)
                    break

            draft = ScreenplayDraft(
                scenes=scenes,
                revision_notes=all_notes,
            )
            try:
                validate_screenplay(draft, confirmed_plan)
            except ScreenplayValidationError as retry_error:
                raise AIProviderError(str(retry_error)) from retry_error
        return draft

    def _generate_scene(
        self,
        plan_scene,
        chapters_by_index: dict[int, Chapter],
    ) -> tuple[ScreenplayScene, list[str]]:
        # Build prompt with only this scene's chapters
        prompt = self._build_scene_prompt(plan_scene, chapters_by_index)

        try:
            raw = self._llm_client.generate_json(
                PER_SCENE_SYSTEM_PROMPT, prompt
            )
        except StructuredLLMError as error:
            raise AIProviderError(str(error)) from error
        except Exception as error:
            raise AIProviderError(
                f"Scene {plan_scene.id} generation failed: {error}"
            ) from error

        heading_raw = raw.get("heading", {})
        if not isinstance(heading_raw, dict):
            heading_raw = {}
        heading = _parse_heading(heading_raw, f"scene {plan_scene.id}")

        beats = [
            _parse_beat(b, f"scene {plan_scene.id}.beats[{i}]")
            for i, b in enumerate(raw.get("beats", []))
            if isinstance(b, dict)
        ]
        # Auto-correct: action beats must not have character_id
        beats = [
            replace(b, character_id=None)
            if b.type in ("action", "transition") and b.character_id
            else b
            for b in beats
        ]

        source_indexes = _normalize_chapter_indexes(
            raw.get("source_chapter_indexes", plan_scene.source_chapter_indexes)
        )

        notes = raw.get("revision_notes", [])
        if not isinstance(notes, list):
            notes = []

        scene = ScreenplayScene(
            id=plan_scene.id,
            heading=heading,
            source_chapter_indexes=source_indexes,
            character_ids=plan_scene.character_ids,
            beats=beats,
        )
        return scene, [n for n in notes if isinstance(n, str)]

    @staticmethod
    def _build_scene_prompt(
        plan_scene,
        chapters_by_index: dict[int, Chapter],
    ) -> str:
        parts: list[str] = [
            f"## Scene: {plan_scene.title}",
            f"Scene ID: {plan_scene.id}",
            f"Dramatic purpose: {plan_scene.dramatic_purpose}",
            f"Character IDs: {plan_scene.character_ids}",
            f"Source chapters: {plan_scene.source_chapter_indexes}",
            "",
            "You MUST use the EXACT source_chapter_indexes and "
            "character_ids listed above. Chapter indexes are 1-based.",
            "",
            "## Source Chapters",
        ]
        for idx in plan_scene.source_chapter_indexes:
            ch = chapters_by_index.get(idx)
            if ch:
                parts.append(
                    f"\n### Chapter {ch.index}: {ch.title}\n{ch.content}"
                )
        return "\n".join(parts)

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
