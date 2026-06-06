from __future__ import annotations

import dataclasses
from typing import Any

from scriptweaver.ai.provider import AIProviderInputError
from scriptweaver.domain.models import (
    AdaptationDecision,
    AdaptationPlan,
    AIAnalysis,
    Chapter,
    PlanReviewQuestion,
    ScenePlan,
)
from scriptweaver.domain.plan_validation import (
    PlanValidationError,
    validate_plan,
)
from scriptweaver.llm.client import StructuredLLMClient, StructuredLLMError


class AIProviderError(RuntimeError):
    """Raised when the LLM plan provider cannot produce a valid result."""


SYSTEM_PROMPT = """\
You are a screenplay adaptation planner. Given a confirmed story analysis \
and the original chapters, produce a structured adaptation plan.

Return a JSON object with exactly these keys:

- "target_format": string (e.g., "1-3 minute short drama")
- "structure": string (e.g., "3 scenes, linear narrative")
- "scenes": list of scene objects, each with fields:
  id (unique string), scene_order (int), title (string),
  dramatic_purpose (string), character_ids (list of strings),
  source_chapter_indexes (list of ints), retained_event_ids (list of strings),
  source_candidate_scene_ids (list of strings),
  compression_choices (list of decision objects),
  merge_choices (list of decision objects),
  rewrite_choices (list of decision objects),
  review_questions (list of question objects)
- "review_questions": list of question objects with fields:
  id (unique string), question (string), context (string),
  related_scene_ids (list of strings)

A decision object has fields:
  id (unique string), description (string), reason (string),
  source_event_ids (list of strings)

A question object has fields:
  id (unique string), question (string), context (string),
  related_scene_ids (list of strings)

Every id must be unique within its category. Use 1-based indexes."""


def _field_names(cls: type) -> set[str]:
    return {field.name for field in dataclasses.fields(cls)}


def _filter_fields(cls: type, raw: dict[str, Any]) -> dict[str, Any]:
    allowed = _field_names(cls)
    return {k: v for k, v in raw.items() if k in allowed}


def _parse_item(cls: type, raw: dict[str, Any], label: str) -> Any:
    try:
        return cls(**_filter_fields(cls, raw))
    except TypeError as error:
        raise AIProviderError(
            f"Failed to parse {label}: {error}"
        ) from error


def _parse_decision(raw: dict[str, Any], label: str) -> AdaptationDecision:
    return _parse_item(AdaptationDecision, raw, label)


def _parse_question(raw: dict[str, Any], label: str) -> PlanReviewQuestion:
    return _parse_item(PlanReviewQuestion, raw, label)


def _parse_scene(raw: dict[str, Any], label: str) -> ScenePlan:
    compression = [
        _parse_decision(d, f"{label}.compression_choices[{i}]")
        for i, d in enumerate(raw.get("compression_choices", []))
    ]
    merge = [
        _parse_decision(d, f"{label}.merge_choices[{i}]")
        for i, d in enumerate(raw.get("merge_choices", []))
    ]
    rewrite = [
        _parse_decision(d, f"{label}.rewrite_choices[{i}]")
        for i, d in enumerate(raw.get("rewrite_choices", []))
    ]
    review = [
        _parse_question(q, f"{label}.review_questions[{i}]")
        for i, q in enumerate(raw.get("review_questions", []))
    ]

    filtered = _filter_fields(ScenePlan, raw)
    filtered["compression_choices"] = compression
    filtered["merge_choices"] = merge
    filtered["rewrite_choices"] = rewrite
    filtered["review_questions"] = review

    try:
        return ScenePlan(**filtered)
    except TypeError as error:
        raise AIProviderError(
            f"Failed to parse {label}: {error}"
        ) from error


class LLMPlanProvider:
    """Adaptation plan provider backed by a structured LLM client."""

    def __init__(self, llm_client: StructuredLLMClient) -> None:
        self._llm_client = llm_client

    def generate_plan(
        self,
        confirmed_analysis: AIAnalysis,
        chapters: list[Chapter],
    ) -> AdaptationPlan:
        if not chapters:
            raise AIProviderInputError(
                "At least 1 chapter is required for plan generation"
            )

        user_prompt = self._build_user_prompt(confirmed_analysis, chapters)

        try:
            raw = self._llm_client.generate_json(SYSTEM_PROMPT, user_prompt)
        except StructuredLLMError as error:
            raise AIProviderError(str(error)) from error
        except Exception as error:
            raise AIProviderError(
                f"LLM plan generation failed: {error}"
            ) from error

        plan = self._parse_response(raw)
        try:
            validate_plan(plan)
        except PlanValidationError as error:
            raise AIProviderError(str(error)) from error
        return plan

    @staticmethod
    def _build_user_prompt(
        confirmed_analysis: AIAnalysis,
        chapters: list[Chapter],
    ) -> str:
        parts: list[str] = ["## Confirmed Analysis"]

        if confirmed_analysis.characters:
            parts.append("\n### Characters")
            for c in confirmed_analysis.characters:
                parts.append(
                    f"- {c.id}: {c.name} ({c.role}) - {c.goal}"
                )

        if confirmed_analysis.key_events:
            parts.append("\n### Key Events")
            for e in confirmed_analysis.key_events:
                parts.append(
                    f"- {e.id}: {e.summary} "
                    f"(chapters: {e.source_chapter_indexes})"
                )

        if confirmed_analysis.candidate_scenes:
            parts.append("\n### Candidate Scenes")
            for s in confirmed_analysis.candidate_scenes:
                parts.append(
                    f"- {s.id}: {s.title} - {s.dramatic_purpose}"
                )

        parts.append("\n## Source Chapters")
        for chapter in chapters:
            parts.append(
                f"\n### Chapter {chapter.index}: {chapter.title}\n"
                f"{chapter.content}"
            )

        return "\n".join(parts)

    @staticmethod
    def _parse_response(raw: dict[str, Any]) -> AdaptationPlan:
        if "scenes" not in raw:
            raise AIProviderError(
                "Missing required key in LLM response: scenes"
            )
        if not isinstance(raw["scenes"], list):
            raise AIProviderError(
                "'scenes' must be a list"
            )

        scenes = [
            _parse_scene(s, f"scenes[{i}]")
            for i, s in enumerate(raw["scenes"])
        ]

        review_questions = [
            _parse_question(q, f"review_questions[{i}]")
            for i, q in enumerate(raw.get("review_questions", []))
        ]

        try:
            return AdaptationPlan(
                target_format=raw.get("target_format", ""),
                structure=raw.get("structure", ""),
                scenes=scenes,
                review_questions=review_questions,
            )
        except TypeError as error:
            raise AIProviderError(
                f"Failed to construct AdaptationPlan: {error}"
            ) from error
