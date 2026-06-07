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
    UserConfirmations,
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
- "structure": string describing the overall narrative structure
  (e.g., "5 scenes, linear narrative with flashback")
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

IMPORTANT — Scene count guidance:
- Typically 1-2 scenes per chapter, depending on content density.
- A novel with 5+ substantial chapters should have at least 5 scenes.
- Do NOT default to 3 scenes — adapt to the actual chapter count and
  complexity of the source material.
- More chapters with rich events → more scenes.

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
        if isinstance(d, dict)
    ]
    merge = [
        _parse_decision(d, f"{label}.merge_choices[{i}]")
        for i, d in enumerate(raw.get("merge_choices", []))
        if isinstance(d, dict)
    ]
    rewrite = [
        _parse_decision(d, f"{label}.rewrite_choices[{i}]")
        for i, d in enumerate(raw.get("rewrite_choices", []))
        if isinstance(d, dict)
    ]
    review = [
        _parse_question(q, f"{label}.review_questions[{i}]")
        for i, q in enumerate(raw.get("review_questions", []))
        if isinstance(q, dict)
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
        user_confirmations: UserConfirmations | None = None,
    ) -> AdaptationPlan:
        if not chapters:
            raise AIProviderInputError(
                "At least 1 chapter is required for plan generation"
            )

        user_prompt = self._build_user_prompt(
            confirmed_analysis, chapters, user_confirmations
        )

        try:
            raw = self._llm_client.generate_json(SYSTEM_PROMPT, user_prompt)
        except StructuredLLMError as error:
            raise AIProviderError(str(error)) from error
        except Exception as error:
            raise AIProviderError(
                f"LLM plan generation failed: {error}"
            ) from error

        valid_chapter_indexes = {chapter.index for chapter in chapters}

        plan = self._parse_response(raw)
        try:
            validate_plan(
                plan,
                confirmed_analysis=confirmed_analysis,
                chapter_indexes=valid_chapter_indexes,
            )
        except PlanValidationError as error:
            # Retry once with validation error feedback
            retry_prompt = (
                f"{user_prompt}\n\n"
                f"Your previous response was invalid.\n"
                f"Validation error: {error}\n\n"
                f"Valid chapter indexes are: "
                f"{sorted(valid_chapter_indexes)}\n"
                f"Please fix all issues and return a corrected "
                f"adaptation plan JSON."
            )
            try:
                retry_raw = self._llm_client.generate_json(
                    SYSTEM_PROMPT, retry_prompt
                )
            except StructuredLLMError as retry_error:
                raise AIProviderError(str(retry_error)) from retry_error
            except Exception as retry_error:
                raise AIProviderError(
                    f"LLM plan retry failed: {retry_error}"
                ) from retry_error

            plan = self._parse_response(retry_raw)
            try:
                validate_plan(
                    plan,
                    confirmed_analysis=confirmed_analysis,
                    chapter_indexes=valid_chapter_indexes,
                )
            except PlanValidationError as retry_error:
                raise AIProviderError(str(retry_error)) from retry_error

        return plan

    @staticmethod
    def _build_user_prompt(
        confirmed_analysis: AIAnalysis,
        chapters: list[Chapter],
        user_confirmations: UserConfirmations | None,
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

        # ── Author Confirmations ──────────────────────────────
        if user_confirmations is not None:
            parts.append("\n## Author Confirmations")

            # Resolved uncertainties
            resolutions = user_confirmations.uncertainty_resolutions
            if resolutions:
                parts.append("\n### Resolved Uncertainties")
                # Build lookup: uncertainty_id → Uncertainty
                u_by_id = {
                    u.id: u for u in confirmed_analysis.uncertainties
                }
                # Build lookup: option_id → UncertaintyOption
                opt_by_id: dict[tuple[str, str], tuple[str, str, str]] = {}
                for u in confirmed_analysis.uncertainties:
                    for opt in u.options:
                        opt_by_id[(u.id, opt.id)] = (
                            opt.label, opt.description, opt.impact
                        )

                for r in resolutions:
                    uncertainty = u_by_id.get(r.uncertainty_id)
                    question = (
                        uncertainty.question
                        if uncertainty
                        else r.uncertainty_id
                    )
                    parts.append(f"- {r.uncertainty_id}: \"{question}\"")

                    if r.selected_option_id:
                        opt_info = opt_by_id.get((r.uncertainty_id, r.selected_option_id))
                        if opt_info:
                            label, desc, impact = opt_info
                            parts.append(
                                f"  Selected: {r.selected_option_id}"
                                f" \"{label}\" — {desc}"
                            )
                            parts.append(f"  Impact: {impact}")
                        else:
                            parts.append(
                                f"  Selected: {r.selected_option_id}"
                            )
                    elif r.custom_answer:
                        parts.append(
                            f"  Custom answer: {r.custom_answer}"
                        )

            # Required plot points
            if user_confirmations.required_plot_points:
                parts.append("\n### Required Plot Points")
                for pt in user_confirmations.required_plot_points:
                    parts.append(f"- {pt}")

            # Author notes
            if user_confirmations.notes:
                parts.append("\n### Author Notes")
                parts.append(user_confirmations.notes)

        parts.append(
            f"\n## Scene Count\n"
            f"This novel has {len(chapters)} chapters. "
            f"Your plan should have at least {max(3, len(chapters))} "
            f"scenes — typically 1-2 scenes per chapter. "
            f"Do NOT default to 3 scenes. Scale up with the chapter count."
        )

        # Use full text for short novels, summaries for long ones
        if len(chapters) < 5:
            parts.append("\n## Source Chapters (full text)")
            for chapter in chapters:
                parts.append(
                    f"\n### Chapter {chapter.index}: {chapter.title}\n"
                    f"{chapter.content}"
                )
        else:
            parts.append("\n## Chapter Summaries")
            # Build per-chapter event and scene indexes from analysis
            events_by_ch: dict[int, list[str]] = {}
            for e in confirmed_analysis.key_events:
                for idx in e.source_chapter_indexes:
                    events_by_ch.setdefault(idx, []).append(e.summary)

            scenes_by_ch: dict[int, list[str]] = {}
            for s in confirmed_analysis.candidate_scenes:
                for idx in s.source_chapter_indexes:
                    scenes_by_ch.setdefault(idx, []).append(s.title)

            conflicts_by_ch: dict[int, list[str]] = {}
            for c in confirmed_analysis.conflicts:
                for idx in c.source_chapter_indexes:
                    conflicts_by_ch.setdefault(idx, []).append(
                        c.description[:80]
                    )

            themes_by_ch: dict[int, list[str]] = {}
            for t in confirmed_analysis.themes:
                for idx in t.source_chapter_indexes:
                    themes_by_ch.setdefault(idx, []).append(t.statement)

            for chapter in chapters:
                idx = chapter.index
                parts.append(
                    f"\n### Chapter {idx}: {chapter.title}"
                )
                if idx in events_by_ch:
                    parts.append(
                        "Key events: "
                        + "; ".join(events_by_ch[idx])
                    )
                if idx in scenes_by_ch:
                    parts.append(
                        "Candidate scenes: "
                        + "; ".join(scenes_by_ch[idx])
                    )
                if idx in conflicts_by_ch:
                    parts.append(
                        "Conflicts: "
                        + "; ".join(conflicts_by_ch[idx])
                    )
                if idx in themes_by_ch:
                    parts.append(
                        "Themes: "
                        + "; ".join(themes_by_ch[idx])
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
            if isinstance(s, dict)
        ]

        review_questions = [
            _parse_question(q, f"review_questions[{i}]")
            for i, q in enumerate(raw.get("review_questions", []))
            if isinstance(q, dict)
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
