import pytest

from scriptweaver.ai.mock_provider import MockAIAnalysisProvider
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


def make_chapters() -> list[Chapter]:
    return [
        Chapter(index=1, title="第一章", content="林照收到父亲留下的密信。"),
        Chapter(index=2, title="第二章", content="沈微出现并阻止林照公开密信。"),
        Chapter(index=3, title="第三章", content="两人发现密信指向旧案。"),
    ]


def test_mock_provider_returns_deterministic_ai_analysis():
    provider = MockAIAnalysisProvider()

    analysis = provider.analyze_chapters(make_chapters())

    assert isinstance(analysis, AIAnalysis)
    assert analysis.characters == [
        Character(
            id="char_001",
            name="主角",
            role="protagonist",
            description="推动调查并承担主要风险的人物。",
            goal="理解所有章节中的关键事件。",
            motivation="找到事件背后的真相。",
        ),
        Character(
            id="char_002",
            name="关键关系人",
            role="supporting",
            description="与主角合作但保留关键信息的人物。",
            goal="影响主角对真相的选择。",
            motivation="避免关键事件造成更大代价。",
        ),
    ]
    assert analysis.relationships == [
        CharacterRelationship(
            id="relationship_001",
            source_character_id="char_001",
            target_character_id="char_002",
            description="双方共同调查，但对是否公开真相存在分歧。",
            source_chapter_indexes=[1, 2, 3],
        )
    ]
    assert analysis.key_events == [
        KeyEvent(
            id="event_001",
            summary="第一章: 林照收到父亲留下的密信。",
            character_ids=["char_001", "char_002"],
            source_chapter_indexes=[1],
        ),
        KeyEvent(
            id="event_002",
            summary="第二章: 沈微出现并阻止林照公开密信。",
            character_ids=["char_001", "char_002"],
            source_chapter_indexes=[2],
        ),
        KeyEvent(
            id="event_003",
            summary="第三章: 两人发现密信指向旧案。",
            character_ids=["char_001", "char_002"],
            source_chapter_indexes=[3],
        ),
    ]
    assert analysis.conflicts == [
        Conflict(
            id="conflict_001",
            description="主角需要理解《第一章》中的关键事件，但后续章节不断提高代价。",
            stakes="如果主角无法理解真相，关键关系和后续选择都会受到影响。",
            character_ids=["char_001", "char_002"],
            source_chapter_indexes=[1, 2, 3],
        )
    ]
    assert analysis.themes == [
        Theme(
            id="theme_001",
            statement="理解真相需要面对不断提高的代价。",
            source_chapter_indexes=[1, 2, 3],
        )
    ]
    assert analysis.candidate_scenes == [
        CandidateScene(
            id="candidate_scene_001",
            title="第一章",
            summary="林照收到父亲留下的密信。",
            dramatic_purpose="将第一章的关键事件转化为可见的戏剧行动。",
            location="待作者确认",
            time_hint="待作者确认",
            character_ids=["char_001", "char_002"],
            source_chapter_indexes=[1],
        ),
        CandidateScene(
            id="candidate_scene_002",
            title="第二章",
            summary="沈微出现并阻止林照公开密信。",
            dramatic_purpose="将第二章的关键事件转化为可见的戏剧行动。",
            location="待作者确认",
            time_hint="待作者确认",
            character_ids=["char_001", "char_002"],
            source_chapter_indexes=[2],
        ),
        CandidateScene(
            id="candidate_scene_003",
            title="第三章",
            summary="两人发现密信指向旧案。",
            dramatic_purpose="将第三章的关键事件转化为可见的戏剧行动。",
            location="待作者确认",
            time_hint="待作者确认",
            character_ids=["char_001", "char_002"],
            source_chapter_indexes=[3],
        ),
    ]
    assert analysis.uncertainties == [
        Uncertainty(
            id="uncertainty_001",
            question="关键关系人是否提前知道主角发现的线索？",
            context="人物动机将影响后续场景冲突。",
            options=[
                UncertaintyOption(
                    id="option_001",
                    label="提前知情",
                    description="关键关系人一直知道主角发现的线索。",
                    impact="强化隐瞒与信任冲突。",
                ),
                UncertaintyOption(
                    id="option_002",
                    label="刚刚得知",
                    description="关键关系人与主角同时发现线索。",
                    impact="强化共同调查关系。",
                ),
            ],
            allow_custom_answer=True,
            source_chapter_indexes=[1, 2, 3],
        )
    ]


def test_mock_provider_rejects_empty_chapter_list():
    provider = MockAIAnalysisProvider()

    with pytest.raises(
        AIProviderInputError,
        match="At least 1 chapter is required for analysis",
    ):
        provider.analyze_chapters([])


def make_five_chapters() -> list[Chapter]:
    return [
        *make_chapters(),
        Chapter(index=4, title="第四章", content="林照决定追查旧案知情人。"),
        Chapter(index=5, title="第五章", content="沈微承认自己隐瞒了关键证据。"),
    ]


def test_mock_provider_accepts_single_chapter():
    provider = MockAIAnalysisProvider()
    chapter = make_chapters()[0]

    analysis = provider.analyze_chapters([chapter])

    assert analysis.key_events == [
        KeyEvent(
            id="event_001",
            summary="第一章: 林照收到父亲留下的密信。",
            character_ids=["char_001", "char_002"],
            source_chapter_indexes=[1],
        )
    ]


def test_mock_provider_rejects_empty_chapter_content():
    provider = MockAIAnalysisProvider()
    chapters = make_chapters()
    chapters[1] = Chapter(index=2, title="第二章", content=" \n\t ")

    with pytest.raises(AIProviderInputError, match="第二章 is empty"):
        provider.analyze_chapters(chapters)


def test_mock_provider_analyzes_all_supplied_chapters():
    provider = MockAIAnalysisProvider()

    analysis = provider.analyze_chapters(make_five_chapters())

    character_ids = {character.id for character in analysis.characters}
    chapter_indexes = {chapter.index for chapter in make_five_chapters()}

    assert [event.id for event in analysis.key_events] == [
        "event_001",
        "event_002",
        "event_003",
        "event_004",
        "event_005",
    ]
    assert [event.source_chapter_indexes for event in analysis.key_events] == [
        [1],
        [2],
        [3],
        [4],
        [5],
    ]
    assert [scene.id for scene in analysis.candidate_scenes] == [
        "candidate_scene_001",
        "candidate_scene_002",
        "candidate_scene_003",
        "candidate_scene_004",
        "candidate_scene_005",
    ]
    assert analysis.candidate_scenes[-1].source_chapter_indexes == [5]

    assert all(
        set(item.character_ids) <= character_ids
        for item in [
            *analysis.key_events,
            *analysis.conflicts,
            *analysis.candidate_scenes,
        ]
    )
    assert all(
        set(item.source_chapter_indexes) <= chapter_indexes
        for item in [
            *analysis.relationships,
            *analysis.key_events,
            *analysis.conflicts,
            *analysis.themes,
            *analysis.candidate_scenes,
            *analysis.uncertainties,
        ]
    )


def test_mock_provider_uncertainties_are_answerable():
    from scriptweaver.domain.uncertainty_validation import (
        validate_uncertainties,
    )

    analysis = MockAIAnalysisProvider().analyze_chapters(make_chapters())

    validate_uncertainties(analysis.uncertainties)
