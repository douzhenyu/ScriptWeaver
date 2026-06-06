"""End-to-end tests covering the full adaptation workflow."""

import yaml

from scriptweaver.ai.mock_provider import (
    MockAIAnalysisProvider,
    MockPlanProvider,
    MockScreenplayProvider,
)
from scriptweaver.domain.models import (
    AIAnalysis,
    Chapter,
    UncertaintyResolution,
)
from scriptweaver.domain.workflow import AdaptationState
from scriptweaver.export.yaml_exporter import export_job_to_yaml
from scriptweaver.services.adaptation_service import AdaptationService


def make_chapters() -> list[Chapter]:
    return [
        Chapter(
            index=1,
            title="第一章",
            content="林照收到父亲留下的密信。",
        ),
        Chapter(
            index=2,
            title="第二章",
            content="沈微出现并阻止林照公开密信。",
        ),
        Chapter(
            index=3,
            title="第三章",
            content="两人发现密信指向旧案。",
        ),
    ]


def test_full_workflow_from_create_to_export():
    """Exercise every workflow state and verify end-to-end consistency."""
    service = AdaptationService(
        MockAIAnalysisProvider(),
        plan_provider=MockPlanProvider(),
        screenplay_provider=MockScreenplayProvider(),
    )

    # ── Stage 1: Create job ──────────────────────────────────
    job = service.create_job("e2e-001")
    assert job.state == AdaptationState.CREATED
    assert job.id == "e2e-001"

    # ── Stage 2: Attach chapters ─────────────────────────────
    chapters = make_chapters()
    job = service.attach_chapters(job, chapters)
    assert job.state == AdaptationState.CHAPTERS_UPLOADED
    assert len(job.chapters) == 3

    # ── Stage 3: Generate AI analysis ────────────────────────
    job = service.generate_analysis(job)
    assert job.state == AdaptationState.ANALYSIS_GENERATED
    assert job.ai_analysis is not None
    assert len(job.ai_analysis.characters) == 2
    assert len(job.ai_analysis.uncertainties) == 1

    # ── Stage 4: One-question-at-a-time confirmation ─────────
    uncertainty = service.get_next_unanswered_uncertainty(job)
    assert uncertainty is not None
    assert uncertainty.id == "uncertainty_001"

    resolution = UncertaintyResolution(
        uncertainty_id="uncertainty_001",
        selected_option_id="option_001",
    )
    job = service.submit_uncertainty_answer(job, resolution)

    # All answered — next should return None
    assert service.get_next_unanswered_uncertainty(job) is None
    assert job.user_confirmations is not None
    resolutions = job.user_confirmations.uncertainty_resolutions
    assert len(resolutions) == 1
    assert resolutions[0].selected_option_id == "option_001"

    # ── Stage 5: Confirm analysis ────────────────────────────
    job = service.confirm_analysis(
        job,
        job.ai_analysis,  # accept AI analysis as-is
    )
    assert job.state == AdaptationState.ANALYSIS_CONFIRMED
    assert job.confirmed_analysis is not None

    # ── Stage 6: Generate adaptation plan ────────────────────
    job = service.generate_plan(job)
    assert job.state == AdaptationState.PLAN_GENERATED
    plan = job.adaptation_plan
    assert plan is not None
    assert len(plan.scenes) == 3
    assert plan.scenes[0].scene_order == 1
    assert plan.scenes[0].id == "scene_001"
    # Each scene has compression choices and review questions
    assert len(plan.scenes[0].compression_choices) >= 1
    assert len(plan.scenes[0].review_questions) >= 1
    # Plan has overall review questions
    assert len(plan.review_questions) >= 1

    # ── Stage 7: Confirm adaptation plan ─────────────────────
    job = service.confirm_plan(job, plan)
    assert job.state == AdaptationState.PLAN_CONFIRMED

    # ── Stage 8: Generate screenplay ─────────────────────────
    job = service.generate_screenplay(job)
    assert job.state == AdaptationState.SCREENPLAY_GENERATED
    draft = job.screenplay_draft
    assert draft is not None
    assert draft.scene_ids == ["scene_001", "scene_002", "scene_003"]
    assert len(draft.revision_notes) == 3

    # ── Stage 9: Export to YAML ──────────────────────────────
    metadata = {
        "title": "密信",
        "author": "测试作者",
        "adapter": "ScriptWeaver AI",
        "target_format": "short_drama",
        "language": "zh-CN",
        "created_at": "2026-06-07T10:00:00",
    }
    yaml_str = export_job_to_yaml(job, metadata)
    parsed = yaml.safe_load(yaml_str)

    # Verify top-level structure
    assert parsed["schema_version"] == "1.0"
    assert parsed["metadata"]["title"] == "密信"
    assert parsed["source"]["chapter_count"] == 3
    assert len(parsed["source"]["chapters"]) == 3

    # Verify AI analysis was exported
    assert len(parsed["ai_analysis"]["characters"]) == 2
    assert len(parsed["ai_analysis"]["uncertainties"]) == 1

    # Verify confirmed analysis present
    assert parsed["confirmed_analysis"] is not None

    # Verify user confirmations include uncertainty resolution
    uc = parsed["user_confirmations"]
    assert uc is not None
    assert len(uc["uncertainty_resolutions"]) == 1
    assert (
        uc["uncertainty_resolutions"][0]["selected_option_id"]
        == "option_001"
    )

    # Verify adaptation plan
    plan_yaml = parsed["adaptation_plan"]
    assert len(plan_yaml["scenes"]) == 3
    assert plan_yaml["scenes"][0]["id"] == "scene_001"
    assert len(plan_yaml["scenes"][0]["compression_choices"]) >= 1

    # Verify screenplay draft
    assert parsed["screenplay"]["scene_ids"] == [
        "scene_001", "scene_002", "scene_003",
    ]

    # Verify revision notes
    assert len(parsed["revision_notes"]) == 3


def test_workflow_preserves_complete_history():
    """Verify each stage preserves all previous data."""
    service = AdaptationService(
        MockAIAnalysisProvider(),
        plan_provider=MockPlanProvider(),
        screenplay_provider=MockScreenplayProvider(),
    )

    chapters = make_chapters()
    job = service.create_job("e2e-002")
    job = service.attach_chapters(job, chapters)
    job = service.generate_analysis(job)
    raw_analysis = job.ai_analysis
    job = service.confirm_analysis(job, raw_analysis)
    job = service.generate_plan(job)
    job = service.confirm_plan(job, job.adaptation_plan)
    job = service.generate_screenplay(job)

    # Final job should retain all data from earlier stages
    assert job.chapters == chapters
    assert job.ai_analysis is raw_analysis
    assert job.confirmed_analysis is not None
    assert job.adaptation_plan is not None
    assert job.screenplay_draft is not None


def test_workflow_state_progression_is_strict():
    """Verify state machine rejects out-of-order operations."""
    service = AdaptationService(
        MockAIAnalysisProvider(),
        plan_provider=MockPlanProvider(),
    )
    job = service.create_job("e2e-003")

    # Cannot generate plan before analysis
    from scriptweaver.domain.workflow import WorkflowTransitionError
    import pytest

    with pytest.raises(WorkflowTransitionError):
        service.generate_plan(job)

    # Cannot confirm before generating
    job = service.attach_chapters(job, make_chapters())
    job = service.generate_analysis(job)
    with pytest.raises(WorkflowTransitionError):
        service.confirm_plan(
            job,
            job.adaptation_plan
            or AIAnalysis(),  # won't reach this
        )


def test_workflow_with_minimal_input():
    """Verify the workflow handles minimally populated inputs."""
    service = AdaptationService(
        MockAIAnalysisProvider(),
        plan_provider=MockPlanProvider(),
    )
    job = service.create_job("e2e-004")
    job = service.attach_chapters(
        job,
        [Chapter(index=1, title="单章", content="最短内容。")],
    )
    job = service.generate_analysis(job)
    # Confirm with empty analysis
    job = service.confirm_analysis(job, AIAnalysis())
    job = service.generate_plan(job)

    assert job.state == AdaptationState.PLAN_GENERATED
    assert len(job.adaptation_plan.scenes) == 1
