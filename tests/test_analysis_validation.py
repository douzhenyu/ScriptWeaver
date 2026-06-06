from dataclasses import replace

import pytest

from scriptweaver.domain import AnalysisValidationError, validate_analysis
from scriptweaver.domain.models import (
    AIAnalysis,
    CandidateScene,
    Character,
    CharacterRelationship,
    Conflict,
    KeyEvent,
    Theme,
    Uncertainty,
)


def make_valid_analysis() -> AIAnalysis:
    return AIAnalysis(
        characters=[
            Character(
                id="char_001",
                name="林照",
                role="protagonist",
                description="追查旧案的人。",
                goal="查明真相。",
                motivation="保护家人。",
            ),
            Character(
                id="char_002",
                name="沈微",
                role="supporting",
                description="掌握线索的人。",
                goal="控制调查风险。",
                motivation="保护无辜者。",
            ),
        ],
        relationships=[
            CharacterRelationship(
                id="relationship_001",
                source_character_id="char_001",
                target_character_id="char_002",
                description="共同调查但存在分歧。",
                source_chapter_indexes=[1, 2],
            )
        ],
        key_events=[
            KeyEvent(
                id="event_001",
                summary="林照收到密信。",
                character_ids=["char_001"],
                source_chapter_indexes=[1],
            )
        ],
        conflicts=[
            Conflict(
                id="conflict_001",
                description="两人对公开真相存在分歧。",
                stakes="错误选择会伤害无辜者。",
                character_ids=["char_001", "char_002"],
                source_chapter_indexes=[1, 2],
            )
        ],
        themes=[
            Theme(
                id="theme_001",
                statement="真相需要代价。",
                source_chapter_indexes=[1, 2],
            )
        ],
        candidate_scenes=[
            CandidateScene(
                id="candidate_scene_001",
                title="密信出现",
                summary="林照收到密信。",
                dramatic_purpose="建立调查目标。",
                location="茶馆",
                time_hint="夜",
                character_ids=["char_001"],
                source_chapter_indexes=[1],
            )
        ],
        uncertainties=[
            Uncertainty(
                id="uncertainty_001",
                question="沈微是否提前知道密信？",
                context="答案影响人物动机。",
                source_chapter_indexes=[1, 2],
            )
        ],
    )


def test_validate_analysis_accepts_empty_analysis():
    validate_analysis(AIAnalysis(), {1, 2})


def test_validate_analysis_accepts_valid_analysis():
    validate_analysis(make_valid_analysis(), {1, 2})


@pytest.mark.parametrize(
    "category",
    [
        "characters",
        "relationships",
        "key_events",
        "conflicts",
        "themes",
        "candidate_scenes",
        "uncertainties",
    ],
)
def test_validate_analysis_rejects_duplicate_ids(category: str):
    analysis = make_valid_analysis()
    item = getattr(analysis, category)[0]
    invalid_analysis = replace(analysis, **{category: [item, item]})

    with pytest.raises(
        AnalysisValidationError,
        match=rf"Duplicate {category} id: {item.id}",
    ):
        validate_analysis(invalid_analysis, {1, 2})


@pytest.mark.parametrize(
    "field_name",
    ["source_character_id", "target_character_id"],
)
def test_validate_analysis_rejects_unknown_relationship_characters(
    field_name: str,
):
    analysis = make_valid_analysis()
    relationship = replace(
        analysis.relationships[0],
        **{field_name: "char_999"},
    )
    invalid_analysis = replace(analysis, relationships=[relationship])

    with pytest.raises(
        AnalysisValidationError,
        match=(
            r"Relationship relationship_001 references unknown character: "
            r"char_999"
        ),
    ):
        validate_analysis(invalid_analysis, {1, 2})


@pytest.mark.parametrize(
    ("category", "label"),
    [
        ("key_events", "Key event"),
        ("conflicts", "Conflict"),
        ("candidate_scenes", "Candidate scene"),
    ],
)
def test_validate_analysis_rejects_unknown_item_characters(
    category: str,
    label: str,
):
    analysis = make_valid_analysis()
    item = replace(getattr(analysis, category)[0], character_ids=["char_999"])
    invalid_analysis = replace(analysis, **{category: [item]})

    with pytest.raises(
        AnalysisValidationError,
        match=rf"{label} {item.id} references unknown character: char_999",
    ):
        validate_analysis(invalid_analysis, {1, 2})


@pytest.mark.parametrize(
    ("category", "label"),
    [
        ("relationships", "Relationship"),
        ("key_events", "Key event"),
        ("conflicts", "Conflict"),
        ("themes", "Theme"),
        ("candidate_scenes", "Candidate scene"),
        ("uncertainties", "Uncertainty"),
    ],
)
def test_validate_analysis_rejects_unknown_chapter_references(
    category: str,
    label: str,
):
    analysis = make_valid_analysis()
    item = replace(
        getattr(analysis, category)[0],
        source_chapter_indexes=[99],
    )
    invalid_analysis = replace(analysis, **{category: [item]})

    with pytest.raises(
        AnalysisValidationError,
        match=rf"{label} {item.id} references unknown chapter index: 99",
    ):
        validate_analysis(invalid_analysis, {1, 2})
