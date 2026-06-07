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

PER_CHAPTER_SYSTEM_PROMPT = """\
You are a story analysis assistant. Analyze a SINGLE novel chapter and \
produce a structured JSON analysis of its contents.

Return a JSON object with exactly these keys:

- "characters": list of objects with fields: \
id (unique string, prefix with ch{chapter_index}_), name, role, description, \
goal, motivation
- "relationships": list of objects with fields: \
id, source_character_id, target_character_id, description, \
source_chapter_indexes (list with just this chapter index)
- "key_events": list of objects with fields: \
id, summary, character_ids, source_chapter_indexes (list with just this index)
- "conflicts": list of objects with fields: \
id, description, stakes, character_ids, source_chapter_indexes
- "themes": list of objects with fields: \
id, statement, source_chapter_indexes
- "candidate_scenes": list of objects with fields: \
id, title, summary, dramatic_purpose, location, time_hint, \
character_ids, source_chapter_indexes
- "uncertainties": list of objects with fields: \
id, question, context, source_chapter_indexes, \
options (list of objects with id, label, description, impact), \
allow_custom_answer (boolean)

This is chapter {chapter_index} of {total_chapters}. Focus only on what \
appears in this chapter. Use 1-based chapter indexes."""

MERGE_SYSTEM_PROMPT = """\
You are a story analysis coordinator. Given per-chapter analyses from a \
novel, merge them into a single, coherent story analysis.

IMPORTANT tasks:
1. Character deduplication: the same character appearing in multiple \
   chapters must be merged into ONE entry with a stable id. Combine \
   descriptions and motivations from all chapters. Aggregate \
   source_chapter_indexes.
2. Event linking: key events that span multiple chapters should be linked \
   — use the same event id and aggregate source_chapter_indexes.
3. Conflict and theme merging: deduplicate similar conflicts/themes across \
   chapters.
4. Candidate scene consolidation: combine or refine candidate scenes that \
   draw from multiple chapters.

Return a JSON object with the same keys as the analysis: characters, \
relationships, key_events, conflicts, themes, candidate_scenes, \
uncertainties. Every id must be unique within its category. \
Use 1-based chapter indexes."""


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
    """AI analysis provider backed by a structured LLM client.

    Uses Map-Reduce for 5+ chapters: per-chapter analysis (Map)
    followed by a coordinator merge (Reduce). For fewer chapters
    a single LLM call is more efficient and preserves cross-chapter
    context natively.
    """

    MAP_THRESHOLD = 5

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

        # Short novels: single LLM call preserves cross-chapter context
        if len(chapters) < self.MAP_THRESHOLD:
            return self._analyze_single_call(chapters)

        # Long novels: Map-Reduce
        return self._analyze_map_reduce(chapters)

    # ── Single-call path (original behaviour) ─────────────────

    def _analyze_single_call(
        self, chapters: list[Chapter]
    ) -> AIAnalysis:
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

    # ── Map-Reduce path ───────────────────────────────────────

    def _analyze_map_reduce(
        self, chapters: list[Chapter]
    ) -> AIAnalysis:
        from scriptweaver.services.progress import progress as _p

        total = len(chapters)

        # Phase 1 — Map: per-chapter analysis
        per_chapter: list[AIAnalysis] = []
        for i, ch in enumerate(chapters):
            _p(f"正在分析第 {i+1}/{total} 章：{ch.title}")
            per_chapter.append(self._analyze_chapter(ch, total))

        # Phase 2 — Reduce: merge into unified analysis
        _p(f"正在合并 {total} 个章节的分析结果…")
        return self._merge_analyses(per_chapter, chapters)

    def _analyze_chapter(
        self, chapter: Chapter, total_chapters: int
    ) -> AIAnalysis:
        prompt = (
            f"Chapter {chapter.index}: {chapter.title}\n\n"
            f"{chapter.content}"
        )
        system = PER_CHAPTER_SYSTEM_PROMPT.format(
            chapter_index=chapter.index,
            total_chapters=total_chapters,
        )
        try:
            raw = self._llm_client.generate_json(system, prompt)
        except StructuredLLMError as error:
            raise AIProviderError(
                f"Chapter {chapter.index} analysis failed: {error}"
            ) from error
        except Exception as error:
            raise AIProviderError(
                f"Chapter {chapter.index} analysis error: {error}"
            ) from error
        return self._parse_response(raw)

    def _merge_analyses(
        self,
        per_chapter: list[AIAnalysis],
        chapters: list[Chapter],
    ) -> AIAnalysis:
        # Build a compact summary of per-chapter findings
        parts: list[str] = [
            "Merge the following per-chapter analyses into one unified "
            "story analysis.",
            f"Total chapters: {len(chapters)}",
        ]
        for i, (analysis, ch) in enumerate(
            zip(per_chapter, chapters)
        ):
            parts.append(
                f"\n## Chapter {ch.index}: {ch.title}"
            )
            parts.append(
                f"Characters: "
                f"{', '.join(c.name for c in analysis.characters)}"
            )
            parts.append(
                f"Key events: "
                f"{', '.join(e.summary[:80] for e in analysis.key_events)}"
            )
            parts.append(
                f"Candidate scenes: "
                f"{', '.join(s.title for s in analysis.candidate_scenes)}"
            )
            parts.append(
                f"Conflicts: "
                f"{', '.join(c.description[:80] for c in analysis.conflicts)}"
            )
            parts.append(
                f"Themes: "
                f"{', '.join(t.statement for t in analysis.themes)}"
            )

        try:
            raw = self._llm_client.generate_json(
                MERGE_SYSTEM_PROMPT, "\n".join(parts)
            )
        except StructuredLLMError as error:
            raise AIProviderError(
                f"Analysis merge failed: {error}"
            ) from error
        except Exception as error:
            raise AIProviderError(
                f"Analysis merge error: {error}"
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
