from dataclasses import replace

import pytest

from scriptweaver.ai.mock_provider import MockAIAnalysisProvider
from scriptweaver.domain.analysis_validation import AnalysisValidationError
from scriptweaver.domain.models import (
    AIAnalysis,
    Chapter,
    Character,
    Conflict,
    KeyEvent,
)
from scriptweaver.domain.workflow import AdaptationState, WorkflowTransitionError
from scriptweaver.services.adaptation_service import (
    AdaptationService,
    AdaptationServiceError,
)


def make_chapters() -> list[Chapter]:
    return [
        Chapter(index=1, title="第一章", content="林照收到父亲留下的密信。"),
        Chapter(index=2, title="第二章", content="沈微出现并阻止林照公开密信。"),
        Chapter(index=3, title="第三章", content="两人发现密信指向旧案。"),
    ]


def make_confirmed_analysis() -> AIAnalysis:
    return AIAnalysis(
        characters=[
            Character(
                id="char-confirmed",
                name="林照",
                role="protagonist",
                description="用户确认后的主角描述。",
                goal="查明真相。",
                motivation="保护家人。",
            )
        ],
        key_events=[
            KeyEvent(
                id="event-confirmed",
                summary="用户确认密信必须保留。",
                character_ids=["char-confirmed"],
                source_chapter_indexes=[1],
            )
        ],
    )


def make_analysis_generated_job(service: AdaptationService):
    job = service.create_job("job-001")
    job = service.attach_chapters(job, make_chapters())
    return service.generate_analysis(job)


def test_create_job_starts_in_created_state():
    service = AdaptationService(MockAIAnalysisProvider())

    job = service.create_job("job-001")

    assert job.id == "job-001"
    assert job.state == AdaptationState.CREATED
    assert job.chapters == []
    assert job.ai_analysis is None


def test_attach_chapters_validates_and_advances_state():
    service = AdaptationService(MockAIAnalysisProvider())
    original_job = service.create_job("job-001")
    chapters = make_chapters()

    updated_job = service.attach_chapters(original_job, chapters)

    assert updated_job is not original_job
    assert updated_job.id == original_job.id
    assert updated_job.state == AdaptationState.CHAPTERS_UPLOADED
    assert updated_job.chapters == chapters
    assert updated_job.chapters is not chapters
    assert original_job.state == AdaptationState.CREATED
    assert original_job.chapters == []


def test_attach_chapters_rejects_chapters_uploaded_state():
    service = AdaptationService(MockAIAnalysisProvider())
    chaptered_job = service.attach_chapters(service.create_job("job-001"), make_chapters())

    with pytest.raises(WorkflowTransitionError, match="Cannot transition"):
        service.attach_chapters(chaptered_job, make_chapters())


def test_attach_chapters_accepts_single_chapter():
    service = AdaptationService(MockAIAnalysisProvider())
    job = service.create_job("job-001")
    chapters = make_chapters()[:1]

    updated_job = service.attach_chapters(job, chapters)

    assert updated_job.state == AdaptationState.CHAPTERS_UPLOADED
    assert updated_job.chapters == chapters


def test_attach_chapters_rejects_empty_chapter_list():
    service = AdaptationService(MockAIAnalysisProvider())
    job = service.create_job("job-001")

    with pytest.raises(
        AdaptationServiceError,
        match="At least 1 chapter is required",
    ):
        service.attach_chapters(job, [])


def test_attach_chapters_rejects_empty_chapter_content():
    service = AdaptationService(MockAIAnalysisProvider())
    job = service.create_job("job-001")
    chapters = make_chapters()
    chapters[1] = Chapter(index=2, title="第二章", content=" \n\t ")

    with pytest.raises(AdaptationServiceError, match="第二章 is empty"):
        service.attach_chapters(job, chapters)


class RecordingProvider:
    def __init__(self) -> None:
        self.received_chapters: list[Chapter] | None = None
        self.analysis = AIAnalysis(
            conflicts=[
                Conflict(
                    id="conflict_001",
                    description="外部目标与内部动机冲突",
                    stakes="错误选择会破坏关键关系。",
                    character_ids=[],
                    source_chapter_indexes=[1],
                )
            ]
        )

    def analyze_chapters(self, chapters: list[Chapter]) -> AIAnalysis:
        self.received_chapters = chapters
        return self.analysis


class MutatingProvider:
    def __init__(self) -> None:
        self.analysis = AIAnalysis(
            characters=[
                Character(
                    id="char-001",
                    name="林照",
                    role="protagonist",
                    description="调查旧案的人。",
                    goal="查明真相。",
                    motivation="保护家人。",
                )
            ],
            key_events=[
                KeyEvent(
                    id="event-001",
                    summary="林照收到密信。",
                    character_ids=["char-001"],
                    source_chapter_indexes=[1],
                )
            ],
        )

    def analyze_chapters(self, chapters: list[Chapter]) -> AIAnalysis:
        chapters.clear()
        return self.analysis


def test_generate_analysis_calls_provider_and_advances_state():
    provider = RecordingProvider()
    service = AdaptationService(provider)
    chaptered_job = service.attach_chapters(service.create_job("job-001"), make_chapters())

    updated_job = service.generate_analysis(chaptered_job)

    assert provider.received_chapters == chaptered_job.chapters
    assert updated_job is not chaptered_job
    assert updated_job.id == chaptered_job.id
    assert updated_job.state == AdaptationState.ANALYSIS_GENERATED
    assert updated_job.ai_analysis == provider.analysis
    assert chaptered_job.state == AdaptationState.CHAPTERS_UPLOADED
    assert chaptered_job.ai_analysis is None


def test_generate_analysis_isolates_chapters_from_provider_mutation():
    service = AdaptationService(MutatingProvider())
    expected_chapters = make_chapters()
    chaptered_job = service.attach_chapters(
        service.create_job("job-001"),
        expected_chapters,
    )

    updated_job = service.generate_analysis(chaptered_job)

    assert chaptered_job.chapters == expected_chapters
    assert updated_job.chapters == expected_chapters


def test_generate_analysis_deep_copies_provider_analysis():
    provider = MutatingProvider()
    service = AdaptationService(provider)
    chaptered_job = service.attach_chapters(service.create_job("job-001"), make_chapters())

    updated_job = service.generate_analysis(chaptered_job)
    provider.analysis.key_events[0].character_ids.clear()
    provider.analysis.key_events[0].source_chapter_indexes.clear()
    provider.analysis.characters.clear()
    provider.analysis.key_events.clear()

    assert updated_job.ai_analysis is not provider.analysis
    assert updated_job.ai_analysis == AIAnalysis(
        characters=[
            Character(
                id="char-001",
                name="林照",
                role="protagonist",
                description="调查旧案的人。",
                goal="查明真相。",
                motivation="保护家人。",
            )
        ],
        key_events=[
            KeyEvent(
                id="event-001",
                summary="林照收到密信。",
                character_ids=["char-001"],
                source_chapter_indexes=[1],
            )
        ],
    )


def test_generate_analysis_rejects_wrong_state():
    service = AdaptationService(MockAIAnalysisProvider())
    job = service.create_job("job-001")

    with pytest.raises(WorkflowTransitionError, match="Cannot transition"):
        service.generate_analysis(job)


def test_confirm_analysis_validates_and_advances_state():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    raw_analysis = job.ai_analysis
    confirmed_analysis = make_confirmed_analysis()

    updated_job = service.confirm_analysis(job, confirmed_analysis)

    assert updated_job is not job
    assert updated_job.state == AdaptationState.ANALYSIS_CONFIRMED
    assert updated_job.ai_analysis is raw_analysis
    assert updated_job.confirmed_analysis == confirmed_analysis
    assert updated_job.confirmed_analysis is not confirmed_analysis
    assert job.state == AdaptationState.ANALYSIS_GENERATED
    assert job.confirmed_analysis is None


def test_confirm_analysis_accepts_empty_analysis():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)

    updated_job = service.confirm_analysis(job, AIAnalysis())

    assert updated_job.state == AdaptationState.ANALYSIS_CONFIRMED
    assert updated_job.confirmed_analysis == AIAnalysis()


def test_confirm_analysis_rejects_invalid_analysis():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    confirmed_analysis = make_confirmed_analysis()
    character = confirmed_analysis.characters[0]
    invalid_analysis = replace(
        confirmed_analysis,
        characters=[character, character],
    )

    with pytest.raises(
        AnalysisValidationError,
        match="Duplicate characters id: char-confirmed",
    ):
        service.confirm_analysis(job, invalid_analysis)

    assert job.state == AdaptationState.ANALYSIS_GENERATED
    assert job.confirmed_analysis is None


def test_confirm_analysis_rejects_wrong_state_before_analysis_validation():
    service = AdaptationService(MockAIAnalysisProvider())
    job = service.create_job("job-001")
    character = make_confirmed_analysis().characters[0]
    invalid_analysis = AIAnalysis(characters=[character, character])

    with pytest.raises(WorkflowTransitionError, match="Cannot transition"):
        service.confirm_analysis(job, invalid_analysis)


def test_confirm_analysis_deep_copies_submitted_snapshot():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    confirmed_analysis = make_confirmed_analysis()

    updated_job = service.confirm_analysis(job, confirmed_analysis)
    confirmed_analysis.key_events[0].character_ids.clear()
    confirmed_analysis.key_events[0].source_chapter_indexes.clear()
    confirmed_analysis.characters.clear()
    confirmed_analysis.key_events.clear()

    assert updated_job.confirmed_analysis == make_confirmed_analysis()
