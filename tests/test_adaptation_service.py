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
    return service.confirm_analysis(job, job.ai_analysis)


class RecordingPlanProvider:
    def __init__(self) -> None:
        self.received_analysis: AIAnalysis | None = None
        self.received_chapters: list[Chapter] | None = None
        self.plan = AdaptationPlan(
            target_format="short_drama",
            structure="3 scenes, linear progression",
        )

    def generate_plan(
        self,
        confirmed_analysis: AIAnalysis,
        chapters: list[Chapter],
    ) -> AdaptationPlan:
        self.received_analysis = confirmed_analysis
        self.received_chapters = chapters
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
    job = service.confirm_analysis(job, analysis)
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
    job = service.confirm_analysis(job, analysis)
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
        self.draft = ScreenplayDraft(
            scene_ids=["scene_001", "scene_002"],
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
    assert (
        updated_job.screenplay_draft.scene_ids
        == ["scene_001", "scene_002"]
    )
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
    provider.draft.scene_ids.clear()
    provider.draft.revision_notes.clear()

    assert (
        updated_job.screenplay_draft.scene_ids
        == ["scene_001", "scene_002"]
    )
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
    assert draft.scene_ids == ["scene_001", "scene_002"]
    assert len(draft.revision_notes) == 2
    assert "场景 1" in draft.revision_notes[0]
