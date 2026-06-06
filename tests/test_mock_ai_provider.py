import pytest

from scriptweaver.ai.mock_provider import MockAIAnalysisProvider
from scriptweaver.ai.provider import AIProviderInputError
from scriptweaver.domain.models import AIAnalysis, Chapter


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
    assert [character.to_dict() for character in analysis.characters] == [
        {"id": "char_001", "name": "主角", "role": "protagonist"},
        {"id": "char_002", "name": "关键关系人", "role": "supporting"},
    ]
    assert analysis.conflicts == [
        "主角需要理解《第一章》中的关键事件，但后续章节不断提高代价。"
    ]
    assert analysis.key_events == [
        "第一章: 林照收到父亲留下的密信。",
        "第二章: 沈微出现并阻止林照公开密信。",
        "第三章: 两人发现密信指向旧案。",
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
        "第一章: 林照收到父亲留下的密信。",
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

    assert analysis.key_events == [
        "第一章: 林照收到父亲留下的密信。",
        "第二章: 沈微出现并阻止林照公开密信。",
        "第三章: 两人发现密信指向旧案。",
        "第四章: 林照决定追查旧案知情人。",
        "第五章: 沈微承认自己隐瞒了关键证据。",
    ]
