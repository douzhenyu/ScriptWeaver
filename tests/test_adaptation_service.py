from dataclasses import replace

import pytest

from scriptweaver.ai.mock_provider import (
    MockAIAnalysisProvider,
    MockPlanProvider,
    MockScreenplayProvider,
)
from scriptweaver.domain.analysis_validation import AnalysisValidationError
from scriptweaver.domain.models import (
    AIAnalysis,
    AdaptationPlan,
    Chapter,
    Character,
    Conflict,
    KeyEvent,
    ScenePlan,
    ScreenplayDraft,
    Uncertainty,
    UncertaintyOption,
    UncertaintyResolution,
    UserConfirmations,
)
from scriptweaver.domain.plan_validation import PlanValidationError
from scriptweaver.domain.uncertainty_validation import (
    UncertaintyValidationError,
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


class BadCharacterRefProvider:
    """Returns analysis with an event referencing a non-existent character."""

    def analyze_chapters(self, chapters):
        return AIAnalysis(
            characters=[
                Character(
                    id="char-001",
                    name="林照",
                    role="protagonist",
                    description="主角。",
                    goal="查明真相。",
                    motivation="保护家人。",
                )
            ],
            key_events=[
                KeyEvent(
                    id="event-001",
                    summary="事件。",
                    character_ids=["char-nonexistent"],
                    source_chapter_indexes=[1],
                )
            ],
        )


def test_generate_analysis_rejects_invalid_character_ref():
    """Provider output with bad character ref must not enter ANALYSIS_GENERATED."""
    service = AdaptationService(BadCharacterRefProvider())
    job = service.attach_chapters(
        service.create_job("job-001"),
        make_chapters(),
    )

    with pytest.raises(AnalysisValidationError, match="unknown character"):
        service.generate_analysis(job)

    # Job state must remain unchanged
    assert job.state == AdaptationState.CHAPTERS_UPLOADED
    assert job.ai_analysis is None


class BadChapterIndexProvider:
    """Returns analysis with a conflict referencing a non-existent chapter."""

    def analyze_chapters(self, chapters):
        return AIAnalysis(
            conflicts=[
                Conflict(
                    id="conflict-001",
                    description="冲突。",
                    stakes="高风险。",
                    source_chapter_indexes=[99],
                )
            ],
        )


def test_generate_analysis_rejects_invalid_chapter_index():
    """Provider output with bad chapter index must not enter ANALYSIS_GENERATED."""
    service = AdaptationService(BadChapterIndexProvider())
    job = service.attach_chapters(
        service.create_job("job-001"),
        make_chapters(),
    )

    with pytest.raises(AnalysisValidationError, match="unknown chapter"):
        service.generate_analysis(job)

    assert job.state == AdaptationState.CHAPTERS_UPLOADED
    assert job.ai_analysis is None


class BadUncertaintyProvider:
    """Returns analysis with 1 option and allow_custom_answer=False."""

    def analyze_chapters(self, chapters):
        return AIAnalysis(
            uncertainties=[
                Uncertainty(
                    id="uncertainty-001",
                    question="?",
                    context="ctx",
                    options=[
                        UncertaintyOption(
                            id="opt-001",
                            label="唯一选项",
                            description="只有一个选项。",
                            impact="重大。",
                        )
                    ],
                    allow_custom_answer=False,
                )
            ],
        )


def test_generate_analysis_rejects_invalid_uncertainty():
    """Provider output with invalid uncertainty must not enter ANALYSIS_GENERATED."""
    service = AdaptationService(BadUncertaintyProvider())
    job = service.attach_chapters(
        service.create_job("job-001"),
        make_chapters(),
    )

    with pytest.raises(AnalysisValidationError, match="between 2 and 4"):
        service.generate_analysis(job)

    assert job.state == AdaptationState.CHAPTERS_UPLOADED
    assert job.ai_analysis is None


def test_confirm_analysis_validates_and_advances_state():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    job = service.submit_uncertainty_answer(
        job,
        UncertaintyResolution(
            uncertainty_id="uncertainty_001",
            selected_option_id="option_001",
        ),
    )
    raw_analysis = job.ai_analysis

    updated_job = service.confirm_analysis(job)

    assert updated_job is not job
    assert updated_job.state == AdaptationState.ANALYSIS_CONFIRMED
    assert updated_job.ai_analysis is raw_analysis
    assert updated_job.confirmed_analysis is not None
    assert updated_job.confirmed_analysis is not raw_analysis
    # confirmed_analysis derives from ai_analysis
    assert len(updated_job.confirmed_analysis.characters) == len(
        raw_analysis.characters
    )
    assert job.state == AdaptationState.ANALYSIS_GENERATED
    assert job.confirmed_analysis is None


def test_confirm_analysis_accepts_empty_analysis():
    """When ai_analysis is empty, confirmed_analysis is also empty."""
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    # Replace ai_analysis with empty analysis
    job = replace(job, ai_analysis=AIAnalysis())

    updated_job = service.confirm_analysis(job)

    assert updated_job.state == AdaptationState.ANALYSIS_CONFIRMED
    assert updated_job.confirmed_analysis == AIAnalysis()


def test_confirm_analysis_rejects_invalid_analysis():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    job = service.submit_uncertainty_answer(
        job,
        UncertaintyResolution(
            uncertainty_id="uncertainty_001",
            selected_option_id="option_001",
        ),
    )
    # Corrupt ai_analysis with duplicate characters
    char = job.ai_analysis.characters[0]
    corrupted = replace(job.ai_analysis, characters=[char, char])
    job = replace(job, ai_analysis=corrupted)

    with pytest.raises(
        AnalysisValidationError,
        match="Duplicate characters id",
    ):
        service.confirm_analysis(job)

    assert job.state == AdaptationState.ANALYSIS_GENERATED
    assert job.confirmed_analysis is None


def test_confirm_analysis_rejects_wrong_state_before_analysis_validation():
    service = AdaptationService(MockAIAnalysisProvider())
    job = service.create_job("job-001")
    # Give it an ai_analysis but wrong state
    job = replace(job, ai_analysis=AIAnalysis())

    with pytest.raises(WorkflowTransitionError, match="Cannot transition"):
        service.confirm_analysis(job)


def test_confirm_analysis_deep_copies_submitted_snapshot():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    job = service.submit_uncertainty_answer(
        job,
        UncertaintyResolution(
            uncertainty_id="uncertainty_001",
            selected_option_id="option_001",
        ),
    )

    updated_job = service.confirm_analysis(job)

    # Mutating ai_analysis after confirm must not affect confirmed_analysis
    job.ai_analysis.characters.clear()
    job.ai_analysis.key_events.clear()
    assert len(updated_job.confirmed_analysis.characters) > 0


def test_confirm_analysis_derives_from_ai_analysis():
    """confirmed_analysis must be derived from ai_analysis, not passed in."""
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    job = service.submit_uncertainty_answer(
        job,
        UncertaintyResolution(
            uncertainty_id="uncertainty_001",
            selected_option_id="option_001",
        ),
    )

    updated_job = service.confirm_analysis(job)

    # confirmed_analysis should contain the same characters as ai_analysis
    assert updated_job.confirmed_analysis is not None
    assert len(updated_job.confirmed_analysis.characters) == len(
        job.ai_analysis.characters
    )
    assert (
        updated_job.confirmed_analysis.characters[0].id
        == job.ai_analysis.characters[0].id
    )


def test_confirm_analysis_filters_by_accepted_characters():
    """accepted_character_ids in user_confirmations must filter characters."""
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    # Set up user_confirmations with accepted_character_ids
    job = replace(
        job,
        user_confirmations=UserConfirmations(
            accepted_character_ids=["char_001"],
            uncertainty_resolutions=[
                UncertaintyResolution(
                    uncertainty_id="uncertainty_001",
                    selected_option_id="option_001",
                ),
            ],
        ),
    )

    updated_job = service.confirm_analysis(job)

    assert len(updated_job.confirmed_analysis.characters) == 1
    assert updated_job.confirmed_analysis.characters[0].id == "char_001"


def test_confirm_analysis_preserves_uncertainty_resolutions():
    """Uncertainty resolutions must be preserved after confirmation."""
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    resolution = UncertaintyResolution(
        uncertainty_id="uncertainty_001",
        selected_option_id="option_001",
    )
    job = replace(
        job,
        user_confirmations=UserConfirmations(
            uncertainty_resolutions=[resolution],
        ),
    )

    updated_job = service.confirm_analysis(job)

    assert updated_job.user_confirmations is not None
    assert len(updated_job.user_confirmations.uncertainty_resolutions) == 1
    assert (
        updated_job.user_confirmations.uncertainty_resolutions[0].selected_option_id
        == "option_001"
    )


def test_confirm_analysis_rejects_without_ai_analysis():
    """confirm_analysis must raise when ai_analysis is None."""
    service = AdaptationService(MockAIAnalysisProvider())
    job = service.attach_chapters(
        service.create_job("job-001"),
        make_chapters(),
    )
    # Manually advance to ANALYSIS_GENERATED but with ai_analysis=None
    job = replace(job, state=AdaptationState.ANALYSIS_GENERATED)

    with pytest.raises(AdaptationServiceError, match="No AI analysis"):
        service.confirm_analysis(job)


# ── PR 37: Require all uncertainties resolved ───────────────────


def test_confirm_analysis_fails_when_uncertainties_unresolved():
    """When AI analysis has uncertainties but none are resolved, confirm must fail."""
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)

    with pytest.raises(
        AdaptationServiceError, match="Unresolved uncertainties"
    ):
        service.confirm_analysis(job)

    assert job.state == AdaptationState.ANALYSIS_GENERATED
    assert job.confirmed_analysis is None


def test_confirm_analysis_fails_when_uncertainties_partially_resolved():
    """When only some uncertainties are resolved, confirm must fail."""
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    # Add a second uncertainty
    uncertainties = list(job.ai_analysis.uncertainties) + [
        Uncertainty(
            id="uncertainty_002",
            question="第二个问题",
            context="更多上下文。",
            options=[
                UncertaintyOption(
                    id="opt_a", label="A", description="dA",
                    impact="iA",
                ),
                UncertaintyOption(
                    id="opt_b", label="B", description="dB",
                    impact="iB",
                ),
            ],
            allow_custom_answer=True,
            source_chapter_indexes=[1, 2, 3],
        )
    ]
    job = replace(
        job,
        ai_analysis=replace(
            job.ai_analysis, uncertainties=uncertainties
        ),
    )
    # Answer only the first uncertainty
    job = replace(
        job,
        user_confirmations=UserConfirmations(
            uncertainty_resolutions=[
                UncertaintyResolution(
                    uncertainty_id="uncertainty_001",
                    selected_option_id="option_001",
                ),
            ],
        ),
    )

    with pytest.raises(
        AdaptationServiceError, match="Unresolved uncertainties"
    ):
        service.confirm_analysis(job)

    assert job.state == AdaptationState.ANALYSIS_GENERATED
    assert job.confirmed_analysis is None


def test_confirm_analysis_succeeds_when_all_uncertainties_resolved():
    """When all uncertainties are resolved, confirm must succeed."""
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    job = replace(
        job,
        user_confirmations=UserConfirmations(
            uncertainty_resolutions=[
                UncertaintyResolution(
                    uncertainty_id="uncertainty_001",
                    selected_option_id="option_001",
                ),
            ],
        ),
    )

    updated_job = service.confirm_analysis(job)

    assert updated_job.state == AdaptationState.ANALYSIS_CONFIRMED
    assert updated_job.confirmed_analysis is not None


def test_confirm_analysis_succeeds_when_no_uncertainties():
    """When AI analysis has no uncertainties, confirm must succeed directly."""
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    job = replace(
        job, ai_analysis=replace(job.ai_analysis, uncertainties=[])
    )

    updated_job = service.confirm_analysis(job)

    assert updated_job.state == AdaptationState.ANALYSIS_CONFIRMED
    assert updated_job.confirmed_analysis is not None


# ── get_next_unanswered_uncertainty ──────────────────────────────


def test_get_next_unanswered_returns_first_uncertainty_when_no_resolutions():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)

    result = service.get_next_unanswered_uncertainty(job)

    assert result is not None
    assert result.id == "uncertainty_001"


def test_get_next_unanswered_returns_none_when_all_resolved():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    resolution = UncertaintyResolution(
        uncertainty_id="uncertainty_001",
        selected_option_id="option_001",
    )
    job = replace(
        job,
        user_confirmations=UserConfirmations(
            uncertainty_resolutions=[resolution],
        ),
    )

    result = service.get_next_unanswered_uncertainty(job)

    assert result is None


def test_get_next_unanswered_skips_resolved_and_returns_next():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    # Manually add a second uncertainty to the analysis
    uncertainties = list(job.ai_analysis.uncertainties) + [
        Uncertainty(
            id="uncertainty_002",
            question="第二个问题",
            context="更多上下文。",
            options=[
                UncertaintyOption(
                    id="option_a",
                    label="选项A",
                    description="描述A",
                    impact="影响A",
                ),
                UncertaintyOption(
                    id="option_b",
                    label="选项B",
                    description="描述B",
                    impact="影响B",
                ),
            ],
            allow_custom_answer=True,
            source_chapter_indexes=[1, 2, 3],
        )
    ]
    job = replace(
        job,
        ai_analysis=replace(job.ai_analysis, uncertainties=uncertainties),
        user_confirmations=UserConfirmations(
            uncertainty_resolutions=[
                UncertaintyResolution(
                    uncertainty_id="uncertainty_001",
                    selected_option_id="option_001",
                ),
            ],
        ),
    )

    result = service.get_next_unanswered_uncertainty(job)

    assert result is not None
    assert result.id == "uncertainty_002"


def test_get_next_unanswered_returns_none_when_no_uncertainties():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    job = replace(
        job,
        ai_analysis=replace(job.ai_analysis, uncertainties=[]),
    )

    result = service.get_next_unanswered_uncertainty(job)

    assert result is None


def test_get_next_unanswered_rejects_wrong_state():
    service = AdaptationService(MockAIAnalysisProvider())
    job = service.create_job("job-001")

    with pytest.raises(
        AdaptationServiceError,
        match="get_next_unanswered_uncertainty requires ANALYSIS_GENERATED",
    ):
        service.get_next_unanswered_uncertainty(job)


# ── submit_uncertainty_answer ────────────────────────────────────


def test_submit_answer_appends_resolution():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    resolution = UncertaintyResolution(
        uncertainty_id="uncertainty_001",
        selected_option_id="option_001",
    )

    updated_job = service.submit_uncertainty_answer(job, resolution)

    assert updated_job is not job
    assert updated_job.user_confirmations is not None
    assert (
        updated_job.user_confirmations.uncertainty_resolutions
        == [resolution]
    )
    assert updated_job.state == AdaptationState.ANALYSIS_GENERATED
    assert job.user_confirmations is None


def test_submit_answer_auto_initializes_user_confirmations():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    resolution = UncertaintyResolution(
        uncertainty_id="uncertainty_001",
        custom_answer="自定义答案。",
    )

    updated_job = service.submit_uncertainty_answer(job, resolution)

    assert updated_job.user_confirmations is not None
    assert (
        updated_job.user_confirmations.uncertainty_resolutions
        == [resolution]
    )


def test_submit_answer_preserves_existing_resolutions():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    first = UncertaintyResolution(
        uncertainty_id="uncertainty_001",
        selected_option_id="option_001",
    )
    job = service.submit_uncertainty_answer(job, first)
    second = UncertaintyResolution(
        uncertainty_id="uncertainty_002",
        custom_answer="新的答案。",
    )
    uncertainties = list(job.ai_analysis.uncertainties) + [
        Uncertainty(
            id="uncertainty_002",
            question="第二个问题",
            context="更多上下文。",
            options=[
                UncertaintyOption(
                    id="opt_a", label="A", description="dA",
                    impact="iA",
                ),
                UncertaintyOption(
                    id="opt_b", label="B", description="dB",
                    impact="iB",
                ),
            ],
            allow_custom_answer=True,
            source_chapter_indexes=[1],
        )
    ]
    job = replace(
        job,
        ai_analysis=replace(job.ai_analysis, uncertainties=uncertainties),
    )

    updated_job = service.submit_uncertainty_answer(job, second)

    assert (
        updated_job.user_confirmations.uncertainty_resolutions
        == [first, second]
    )


def test_submit_answer_rejects_unknown_uncertainty():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    resolution = UncertaintyResolution(
        uncertainty_id="nonexistent",
        selected_option_id="option_001",
    )

    with pytest.raises(
        UncertaintyValidationError,
        match="references unknown uncertainty",
    ):
        service.submit_uncertainty_answer(job, resolution)


def test_submit_answer_rejects_duplicate_resolution():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    resolution = UncertaintyResolution(
        uncertainty_id="uncertainty_001",
        selected_option_id="option_001",
    )
    job = service.submit_uncertainty_answer(job, resolution)

    with pytest.raises(
        UncertaintyValidationError,
        match="Duplicate resolution",
    ):
        service.submit_uncertainty_answer(job, resolution)


def test_submit_answer_rejects_invalid_option_id():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    resolution = UncertaintyResolution(
        uncertainty_id="uncertainty_001",
        selected_option_id="nonexistent_option",
    )

    with pytest.raises(
        UncertaintyValidationError,
        match="references unknown option",
    ):
        service.submit_uncertainty_answer(job, resolution)


def test_submit_answer_rejects_custom_answer_when_disallowed():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    # Modify the uncertainty to disallow custom answers
    modified_uncertainties = [
        replace(
            job.ai_analysis.uncertainties[0],
            allow_custom_answer=False,
        )
    ]
    job = replace(
        job,
        ai_analysis=replace(
            job.ai_analysis,
            uncertainties=modified_uncertainties,
        ),
    )
    resolution = UncertaintyResolution(
        uncertainty_id="uncertainty_001",
        custom_answer="不允许的自定义答案。",
    )

    with pytest.raises(
        UncertaintyValidationError,
        match="does not allow a custom answer",
    ):
        service.submit_uncertainty_answer(job, resolution)


def test_submit_answer_rejects_both_option_and_custom():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    resolution = UncertaintyResolution(
        uncertainty_id="uncertainty_001",
        selected_option_id="option_001",
        custom_answer="多余的答案。",
    )

    with pytest.raises(
        UncertaintyValidationError,
        match="exactly one",
    ):
        service.submit_uncertainty_answer(job, resolution)


def test_submit_answer_rejects_neither_option_nor_custom():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    resolution = UncertaintyResolution(
        uncertainty_id="uncertainty_001",
    )

    with pytest.raises(
        UncertaintyValidationError,
        match="exactly one",
    ):
        service.submit_uncertainty_answer(job, resolution)


def test_submit_answer_rejects_wrong_state():
    service = AdaptationService(MockAIAnalysisProvider())
    job = service.create_job("job-001")
    resolution = UncertaintyResolution(
        uncertainty_id="uncertainty_001",
        selected_option_id="option_001",
    )

    with pytest.raises(
        AdaptationServiceError,
        match="submit_uncertainty_answer requires ANALYSIS_GENERATED",
    ):
        service.submit_uncertainty_answer(job, resolution)


def test_submit_answer_deep_copies_user_confirmations():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_generated_job(service)
    resolution = UncertaintyResolution(
        uncertainty_id="uncertainty_001",
        selected_option_id="option_001",
    )

    updated_job = service.submit_uncertainty_answer(job, resolution)
    # Mutate the original resolution — should not affect the stored one
    object.__setattr__(resolution, "selected_option_id", "option_002")

    assert (
        updated_job.user_confirmations.uncertainty_resolutions[0]
        .selected_option_id
        == "option_001"
    )


# ── generate_plan ────────────────────────────────────────────────


def make_analysis_confirmed_job(service: AdaptationService):
    job = service.create_job("job-001")
    chapters = make_chapters()
    job = service.attach_chapters(job, chapters)
    job = service.generate_analysis(job)
    # Answer all uncertainties before confirming
    job = service.submit_uncertainty_answer(
        job,
        UncertaintyResolution(
            uncertainty_id="uncertainty_001",
            selected_option_id="option_001",
        ),
    )
    return service.confirm_analysis(job)


class RecordingPlanProvider:
    def __init__(self) -> None:
        self.received_analysis: AIAnalysis | None = None
        self.received_chapters: list[Chapter] | None = None
        self.received_confirmations: UserConfirmations | None = None
        self.plan = AdaptationPlan(
            target_format="short_drama",
            structure="3 scenes, linear progression",
        )

    def generate_plan(
        self,
        confirmed_analysis: AIAnalysis,
        chapters: list[Chapter],
        user_confirmations: UserConfirmations | None = None,
    ) -> AdaptationPlan:
        self.received_analysis = confirmed_analysis
        self.received_chapters = chapters
        self.received_confirmations = user_confirmations
        return self.plan


class MutatingPlanProvider:
    def __init__(self) -> None:
        self.plan = AdaptationPlan(
            target_format="short_drama",
            structure="3 scenes",
        )

    def generate_plan(
        self,
        confirmed_analysis: AIAnalysis,
        chapters: list[Chapter],
        user_confirmations: UserConfirmations | None = None,
    ) -> AdaptationPlan:
        chapters.clear()
        return self.plan


def test_generate_plan_advances_state_and_stores_plan():
    provider = RecordingPlanProvider()
    service = AdaptationService(
        MockAIAnalysisProvider(), plan_provider=provider
    )
    job = make_analysis_confirmed_job(service)

    updated_job = service.generate_plan(job)

    assert updated_job is not job
    assert updated_job.state == AdaptationState.PLAN_GENERATED
    assert updated_job.adaptation_plan is not None
    assert updated_job.adaptation_plan.target_format == "short_drama"
    assert updated_job.adaptation_plan == provider.plan
    assert job.state == AdaptationState.ANALYSIS_CONFIRMED
    assert job.adaptation_plan is None


def test_generate_plan_passes_confirmed_analysis_to_provider():
    provider = RecordingPlanProvider()
    service = AdaptationService(
        MockAIAnalysisProvider(), plan_provider=provider
    )
    job = make_analysis_confirmed_job(service)

    service.generate_plan(job)

    assert provider.received_analysis is job.confirmed_analysis
    assert provider.received_chapters == job.chapters


def test_generate_plan_rejects_wrong_state():
    service = AdaptationService(
        MockAIAnalysisProvider(), plan_provider=MockPlanProvider()
    )
    job = service.create_job("job-001")

    with pytest.raises(WorkflowTransitionError, match="Cannot transition"):
        service.generate_plan(job)


def test_generate_plan_requires_confirmed_analysis():
    service = AdaptationService(
        MockAIAnalysisProvider(), plan_provider=MockPlanProvider()
    )
    job = make_analysis_confirmed_job(service)
    # Corrupt the job to simulate missing confirmed analysis
    job = replace(job, confirmed_analysis=None)

    with pytest.raises(
        AdaptationServiceError,
        match="No confirmed analysis to generate plan from",
    ):
        service.generate_plan(job)


def test_generate_plan_requires_plan_provider():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_analysis_confirmed_job(service)

    with pytest.raises(
        AdaptationServiceError,
        match="No plan provider configured",
    ):
        service.generate_plan(job)


def test_generate_plan_deep_copies_provider_plan():
    service = AdaptationService(
        MockAIAnalysisProvider(), plan_provider=MutatingPlanProvider()
    )
    job = make_analysis_confirmed_job(service)

    updated_job = service.generate_plan(job)

    assert updated_job.adaptation_plan is not None
    assert updated_job.adaptation_plan.target_format == "short_drama"


def test_generate_plan_does_not_mutate_original_job():
    service = AdaptationService(
        MockAIAnalysisProvider(), plan_provider=RecordingPlanProvider()
    )
    job = make_analysis_confirmed_job(service)

    service.generate_plan(job)

    assert job.adaptation_plan is None
    assert job.state == AdaptationState.ANALYSIS_CONFIRMED


def test_generate_plan_with_mock_provider():
    service = AdaptationService(
        MockAIAnalysisProvider(), plan_provider=MockPlanProvider()
    )
    job = make_analysis_confirmed_job(service)

    updated_job = service.generate_plan(job)

    assert updated_job.state == AdaptationState.PLAN_GENERATED
    plan = updated_job.adaptation_plan
    assert plan is not None
    assert plan.target_format == "1-3 minute short drama"
    assert len(plan.scenes) == 3
    assert plan.scenes[0].scene_order == 1
    assert len(plan.scenes[0].compression_choices) == 1
    assert len(plan.scenes[0].review_questions) == 1
    assert len(plan.review_questions) == 1


# ── confirm_plan ─────────────────────────────────────────────────


def make_plan_generated_job(service: AdaptationService):
    job = service.create_job("job-001")
    job = service.attach_chapters(job, make_chapters())
    job = service.generate_analysis(job)
    analysis = job.ai_analysis
    job = service.submit_uncertainty_answer(
        job,
        UncertaintyResolution(
            uncertainty_id="uncertainty_001",
            selected_option_id="option_001",
        ),
    )
    job = service.confirm_analysis(job)
    # Manually set a plan to simulate PLAN_GENERATED state
    plan = AdaptationPlan(
        target_format="short_drama",
        structure="3 scenes, linear progression",
        scenes=[
            ScenePlan(
                id="scene_001",
                scene_order=1,
                title="第一幕",
                dramatic_purpose="建立冲突。",
                character_ids=["char_001"],
                source_chapter_indexes=[1],
                retained_event_ids=["event_001"],
                source_candidate_scene_ids=["candidate_scene_001"],
            ),
            ScenePlan(
                id="scene_002",
                scene_order=2,
                title="第二幕",
                dramatic_purpose="升级冲突。",
                character_ids=["char_001"],
                source_chapter_indexes=[2],
                retained_event_ids=["event_002"],
                source_candidate_scene_ids=["candidate_scene_002"],
            ),
        ],
    )
    return replace(
        job,
        state=AdaptationState.PLAN_GENERATED,
        adaptation_plan=plan,
    )


def make_plan_confirmed_job(service: AdaptationService):
    """Build a job in PLAN_CONFIRMED state with a confirmed plan."""
    job = service.create_job("job-001")
    job = service.attach_chapters(job, make_chapters())
    job = service.generate_analysis(job)
    analysis = job.ai_analysis
    job = service.submit_uncertainty_answer(
        job,
        UncertaintyResolution(
            uncertainty_id="uncertainty_001",
            selected_option_id="option_001",
        ),
    )
    job = service.confirm_analysis(job)
    plan = AdaptationPlan(
        target_format="short_drama",
        structure="3 scenes, linear progression",
        scenes=[
            ScenePlan(
                id="scene_001",
                scene_order=1,
                title="第一幕",
                dramatic_purpose="建立冲突。",
                character_ids=["char_001"],
                source_chapter_indexes=[1],
                retained_event_ids=["event_001"],
                source_candidate_scene_ids=["candidate_scene_001"],
            ),
            ScenePlan(
                id="scene_002",
                scene_order=2,
                title="第二幕",
                dramatic_purpose="升级冲突。",
                character_ids=["char_001"],
                source_chapter_indexes=[2],
                retained_event_ids=["event_002"],
                source_candidate_scene_ids=["candidate_scene_002"],
            ),
        ],
    )
    return replace(
        job,
        state=AdaptationState.PLAN_CONFIRMED,
        adaptation_plan=plan,
    )


def test_confirm_plan_validates_and_advances_state():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_plan_generated_job(service)
    confirmed_plan = job.adaptation_plan

    updated_job = service.confirm_plan(job, confirmed_plan)

    assert updated_job is not job
    assert updated_job.state == AdaptationState.PLAN_CONFIRMED
    assert updated_job.adaptation_plan is not None
    assert (
        updated_job.adaptation_plan.target_format == "short_drama"
    )
    assert updated_job.adaptation_plan is not confirmed_plan
    assert job.state == AdaptationState.PLAN_GENERATED


def test_confirm_plan_rejects_wrong_state():
    service = AdaptationService(MockAIAnalysisProvider())
    job = service.create_job("job-001")
    plan = AdaptationPlan(
        target_format="short_drama", structure="minimal"
    )

    with pytest.raises(WorkflowTransitionError, match="Cannot transition"):
        service.confirm_plan(job, plan)


def test_confirm_plan_rejects_invalid_plan():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_plan_generated_job(service)
    invalid_plan = replace(job.adaptation_plan, target_format="")

    with pytest.raises(
        PlanValidationError,
        match="target_format must not be blank",
    ):
        service.confirm_plan(job, invalid_plan)

    assert job.state == AdaptationState.PLAN_GENERATED


def test_confirm_plan_deep_copies_confirmed_plan():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_plan_generated_job(service)
    confirmed_plan = job.adaptation_plan

    updated_job = service.confirm_plan(job, confirmed_plan)
    # Mutate the original — stored plan should be unchanged
    object.__setattr__(confirmed_plan, "target_format", "changed")

    assert (
        updated_job.adaptation_plan.target_format == "short_drama"
    )


def test_confirm_plan_original_job_unchanged():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_plan_generated_job(service)
    original_plan = job.adaptation_plan

    service.confirm_plan(job, original_plan)

    assert job.state == AdaptationState.PLAN_GENERATED
    assert job.adaptation_plan is original_plan
# ── generate_screenplay ───────────────────────────────────────────


class RecordingScreenplayProvider:
    def __init__(self) -> None:
        self.received_plan: AdaptationPlan | None = None
        self.received_chapters: list[Chapter] | None = None
        from scriptweaver.domain.models import Beat, SceneHeading, ScreenplayScene

        self.draft = ScreenplayDraft(
            scenes=[
                ScreenplayScene(
                    id="scene_001",
                    heading=SceneHeading(
                        location="茶馆", time="夜", interior_exterior="INT"
                    ),
                    beats=[
                        Beat(type="action", text="开场。"),
                    ],
                ),
                ScreenplayScene(
                    id="scene_002",
                    heading=SceneHeading(
                        location="街道", time="日", interior_exterior="EXT"
                    ),
                    beats=[
                        Beat(type="action", text="过渡。"),
                    ],
                ),
            ],
            revision_notes=["审查节奏。"],
        )

    def generate_screenplay(
        self,
        confirmed_plan: AdaptationPlan,
        chapters: list[Chapter],
    ) -> ScreenplayDraft:
        self.received_plan = confirmed_plan
        self.received_chapters = chapters
        return self.draft


def test_generate_screenplay_advances_state_and_stores_draft():
    provider = RecordingScreenplayProvider()
    service = AdaptationService(
        MockAIAnalysisProvider(),
        screenplay_provider=provider,
    )
    job = make_plan_confirmed_job(service)

    updated_job = service.generate_screenplay(job)

    assert updated_job is not job
    assert updated_job.state == AdaptationState.SCREENPLAY_GENERATED
    assert updated_job.screenplay_draft is not None
    scene_ids = [s.id for s in updated_job.screenplay_draft.scenes]
    assert scene_ids == ["scene_001", "scene_002"]
    assert updated_job.screenplay_draft == provider.draft
    assert job.state == AdaptationState.PLAN_CONFIRMED
    assert job.screenplay_draft is None


def test_generate_screenplay_passes_plan_to_provider():
    provider = RecordingScreenplayProvider()
    service = AdaptationService(
        MockAIAnalysisProvider(),
        screenplay_provider=provider,
    )
    job = make_plan_confirmed_job(service)

    service.generate_screenplay(job)

    assert provider.received_plan is job.adaptation_plan
    assert provider.received_chapters == job.chapters


def test_generate_screenplay_rejects_wrong_state():
    service = AdaptationService(
        MockAIAnalysisProvider(),
        screenplay_provider=MockScreenplayProvider(),
    )
    job = service.create_job("job-001")

    with pytest.raises(WorkflowTransitionError, match="Cannot transition"):
        service.generate_screenplay(job)


def test_generate_screenplay_requires_screenplay_provider():
    service = AdaptationService(MockAIAnalysisProvider())
    job = make_plan_confirmed_job(service)

    with pytest.raises(
        AdaptationServiceError,
        match="No screenplay provider configured",
    ):
        service.generate_screenplay(job)


def test_generate_screenplay_deep_copies_provider_draft():
    provider = RecordingScreenplayProvider()
    service = AdaptationService(
        MockAIAnalysisProvider(),
        screenplay_provider=provider,
    )
    job = make_plan_confirmed_job(service)

    updated_job = service.generate_screenplay(job)
    provider.draft.scenes.clear()
    provider.draft.revision_notes.clear()

    scene_ids = [s.id for s in updated_job.screenplay_draft.scenes]
    assert scene_ids == ["scene_001", "scene_002"]
    assert (
        updated_job.screenplay_draft.revision_notes == ["审查节奏。"]
    )


def test_generate_screenplay_original_job_unchanged():
    provider = RecordingScreenplayProvider()
    service = AdaptationService(
        MockAIAnalysisProvider(),
        screenplay_provider=provider,
    )
    job = make_plan_confirmed_job(service)

    service.generate_screenplay(job)

    assert job.state == AdaptationState.PLAN_CONFIRMED
    assert job.screenplay_draft is None


def test_generate_screenplay_with_mock_provider():
    service = AdaptationService(
        MockAIAnalysisProvider(),
        plan_provider=MockPlanProvider(),
        screenplay_provider=MockScreenplayProvider(),
    )
    job = make_plan_confirmed_job(service)

    updated_job = service.generate_screenplay(job)

    assert updated_job.state == AdaptationState.SCREENPLAY_GENERATED
    draft = updated_job.screenplay_draft
    assert draft is not None
    scene_ids = [s.id for s in draft.scenes]
    assert len(draft.scenes) == 2
    assert "scene_001" in scene_ids
    assert len(draft.revision_notes) == 2
    assert "场景 1" in draft.revision_notes[0]
    # Verify beats are generated
    for scene in draft.scenes:
        assert len(scene.beats) >= 2
