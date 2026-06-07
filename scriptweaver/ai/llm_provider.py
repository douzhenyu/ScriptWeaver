from __future__ import annotations

import dataclasses
from typing import Any

from scriptweaver.ai.provider import AIProviderInputError
from scriptweaver.domain.models import (
    AIAnalysis,
    CandidateScene,
    Chapter,
    Character,
    CharacterRelationship,
    Conflict,
    KeyEvent,
    Theme,
    Uncertainty,
    UncertaintyOption,
)
from scriptweaver.llm.client import StructuredLLMClient, StructuredLLMError


class AIProviderError(RuntimeError):
    """Raised when the LLM analysis provider cannot produce a valid result."""


CATEGORY_CLASSES: dict[str, type] = {
    "characters": Character,
    "relationships": CharacterRelationship,
    "key_events": KeyEvent,
    "conflicts": Conflict,
    "themes": Theme,
    "candidate_scenes": CandidateScene,
    "uncertainties": Uncertainty,
}

SYSTEM_PROMPT = """\
You are a story analysis assistant for screenplay adaptation. \
Analyze the provided novel chapters and produce a structured JSON analysis.

Return a JSON object with exactly these keys:

- "characters": list of objects with fields: \
id (unique string), name, role, description, goal, motivation

- "relationships": list of objects with fields: \
id (unique string), source_character_id, target_character_id, \
description, source_chapter_indexes (list of ints, default [])

- "key_events": list of objects with fields: \
id (unique string), summary, character_ids (list of strings, default []), \
source_chapter_indexes (list of ints, default [])

- "conflicts": list of objects with fields: \
id (unique string), description, stakes, \
character_ids (list of strings, default []), \
source_chapter_indexes (list of ints, default [])

- "themes": list of objects with fields: \
id (unique string), statement, \
source_chapter_indexes (list of ints, default [])

- "candidate_scenes": list of objects with fields: \
id (unique string), title, summary, dramatic_purpose, location, time_hint, \
character_ids (list of strings, default []), \
source_chapter_indexes (list of ints, default [])

- "uncertainties": list of objects with fields: \
id (unique string), question, context, \
source_chapter_indexes (list of ints, default []), \
options (list of objects with id, label, description, impact), \
allow_custom_answer (boolean, default true)

Generate at least 1 entry per category. Every id must be unique within \
its category. Use 1-based chapter indexes."""


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


def _parse_uncertainty(raw: dict[str, Any], label: str) -> Uncertainty:
    options_raw = raw.get("options", [])
    options = [
        _parse_item(UncertaintyOption, opt, f"{label}.options[{i}]")
        for i, opt in enumerate(options_raw)
        if isinstance(opt, dict)
    ]
    filtered = _filter_fields(Uncertainty, raw)
    filtered["options"] = options
    try:
        return Uncertainty(**filtered)
    except TypeError as error:
        raise AIProviderError(
            f"Failed to parse {label}: {error}"
        ) from error


class LLMAnalysisProvider:
    """AI analysis provider backed by a structured LLM client."""

    def __init__(self, llm_client: StructuredLLMClient) -> None:
        self._llm_client = llm_client

    def analyze_chapters(self, chapters: list[Chapter]) -> AIAnalysis:
        if not chapters:
            raise AIProviderInputError(
                "At least 1 chapter is required for analysis"
            )

        for chapter in chapters:
            if not chapter.content.strip():
                raise AIProviderInputError(f"{chapter.title} is empty")

        user_prompt = self._build_user_prompt(chapters)

        try:
            raw = self._llm_client.generate_json(
                SYSTEM_PROMPT, user_prompt
            )
        except StructuredLLMError as error:
            raise AIProviderError(str(error)) from error
        except Exception as error:
            raise AIProviderError(
                f"LLM analysis failed: {error}"
            ) from error

        return self._parse_response(raw)

    @staticmethod
    def _build_user_prompt(chapters: list[Chapter]) -> str:
        parts: list[str] = []
        for chapter in chapters:
            parts.append(
                f"Chapter {chapter.index}: {chapter.title}\n"
                f"{chapter.content}"
            )
        return "\n\n".join(parts)

    @staticmethod
    def _parse_response(raw: dict[str, Any]) -> AIAnalysis:
        for category in CATEGORY_CLASSES:
            if category not in raw:
                raise AIProviderError(
                    f"Missing required category: {category}"
                )
            if not isinstance(raw[category], list):
                raise AIProviderError(
                    f"Category '{category}' must be a list, "
                    f"got {type(raw[category]).__name__}"
                )

        return AIAnalysis(
            characters=[
                _parse_item(Character, c, f"characters[{i}]")
                for i, c in enumerate(raw["characters"])
                if isinstance(c, dict)
            ],
            relationships=[
                _parse_item(
                    CharacterRelationship, r, f"relationships[{i}]"
                )
                for i, r in enumerate(raw["relationships"])
                if isinstance(r, dict)
            ],
            key_events=[
                _parse_item(KeyEvent, k, f"key_events[{i}]")
                for i, k in enumerate(raw["key_events"])
                if isinstance(k, dict)
            ],
            conflicts=[
                _parse_item(Conflict, c, f"conflicts[{i}]")
                for i, c in enumerate(raw["conflicts"])
                if isinstance(c, dict)
            ],
            themes=[
                _parse_item(Theme, t, f"themes[{i}]")
                for i, t in enumerate(raw["themes"])
                if isinstance(t, dict)
            ],
            candidate_scenes=[
                _parse_item(
                    CandidateScene, s, f"candidate_scenes[{i}]"
                )
                for i, s in enumerate(raw["candidate_scenes"])
                if isinstance(s, dict)
            ],
            uncertainties=[
                _parse_uncertainty(u, f"uncertainties[{i}]")
                for i, u in enumerate(raw["uncertainties"])
                if isinstance(u, dict)
            ],
        )
