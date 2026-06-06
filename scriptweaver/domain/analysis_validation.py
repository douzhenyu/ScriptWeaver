from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from scriptweaver.domain.models import AIAnalysis
from scriptweaver.domain.uncertainty_validation import (
    UncertaintyValidationError,
    validate_uncertainties,
)


class AnalysisValidationError(ValueError):
    """Raised when structured AI analysis contains invalid references."""


def _validate_unique_ids(category: str, items: Iterable[Any]) -> None:
    seen_ids: set[str] = set()
    for item in items:
        if item.id in seen_ids:
            raise AnalysisValidationError(
                f"Duplicate {category} id: {item.id}"
            )
        seen_ids.add(item.id)


def _validate_character_ids(
    label: str,
    item_id: str,
    referenced_ids: Iterable[str],
    valid_ids: set[str],
) -> None:
    for character_id in referenced_ids:
        if character_id not in valid_ids:
            raise AnalysisValidationError(
                f"{label} {item_id} references unknown character: "
                f"{character_id}"
            )


def _validate_chapter_indexes(
    label: str,
    item_id: str,
    referenced_indexes: Iterable[int],
    valid_indexes: set[int],
) -> None:
    for chapter_index in referenced_indexes:
        if chapter_index not in valid_indexes:
            raise AnalysisValidationError(
                f"{label} {item_id} references unknown chapter index: "
                f"{chapter_index}"
            )


def validate_analysis(
    analysis: AIAnalysis,
    chapter_indexes: set[int],
) -> None:
    categories = (
        ("characters", analysis.characters),
        ("relationships", analysis.relationships),
        ("key_events", analysis.key_events),
        ("conflicts", analysis.conflicts),
        ("themes", analysis.themes),
        ("candidate_scenes", analysis.candidate_scenes),
        ("uncertainties", analysis.uncertainties),
    )
    for category, items in categories:
        _validate_unique_ids(category, items)

    character_ids = {character.id for character in analysis.characters}

    for relationship in analysis.relationships:
        _validate_character_ids(
            "Relationship",
            relationship.id,
            (
                relationship.source_character_id,
                relationship.target_character_id,
            ),
            character_ids,
        )

    character_reference_categories = (
        ("Key event", analysis.key_events),
        ("Conflict", analysis.conflicts),
        ("Candidate scene", analysis.candidate_scenes),
    )
    for label, items in character_reference_categories:
        for item in items:
            _validate_character_ids(
                label,
                item.id,
                item.character_ids,
                character_ids,
            )

    chapter_reference_categories = (
        ("Relationship", analysis.relationships),
        ("Key event", analysis.key_events),
        ("Conflict", analysis.conflicts),
        ("Theme", analysis.themes),
        ("Candidate scene", analysis.candidate_scenes),
        ("Uncertainty", analysis.uncertainties),
    )
    for label, items in chapter_reference_categories:
        for item in items:
            _validate_chapter_indexes(
                label,
                item.id,
                item.source_chapter_indexes,
                chapter_indexes,
            )

    try:
        validate_uncertainties(analysis.uncertainties)
    except UncertaintyValidationError as error:
        raise AnalysisValidationError(str(error)) from error
