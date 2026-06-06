from dataclasses import replace

import pytest

from scriptweaver.domain.models import (
    AdaptationDecision,
    AdaptationPlan,
    PlanReviewQuestion,
    ScenePlan,
)
from scriptweaver.domain.plan_validation import (
    PlanValidationError,
    validate_plan,
)


def make_valid_plan() -> AdaptationPlan:
    return AdaptationPlan(
        target_format="1-3 minute short drama",
        structure="3 scenes, linear narrative",
        scenes=[
            ScenePlan(
                id="scene_001",
                scene_order=1,
                title="第一幕",
                dramatic_purpose="建立核心悬念。",
                character_ids=["char_001"],
                source_chapter_indexes=[1],
                retained_event_ids=["event_001"],
                source_candidate_scene_ids=["candidate_scene_001"],
                compression_choices=[
                    AdaptationDecision(
                        id="compression_001",
                        description="压缩时间线。",
                        reason="短剧需要快速推进。",
                        source_event_ids=["event_001"],
                    )
                ],
                merge_choices=[],
                rewrite_choices=[],
                review_questions=[
                    PlanReviewQuestion(
                        id="review_001",
                        question="是否保留了核心冲突？",
                        context="原始章节内容。",
                        related_scene_ids=["scene_001"],
                    )
                ],
            ),
            ScenePlan(
                id="scene_002",
                scene_order=2,
                title="第二幕",
                dramatic_purpose="升级冲突。",
                character_ids=["char_001", "char_002"],
                source_chapter_indexes=[2],
                retained_event_ids=["event_002"],
                source_candidate_scene_ids=["candidate_scene_002"],
                compression_choices=[],
                merge_choices=[],
                rewrite_choices=[],
                review_questions=[],
            ),
        ],
        review_questions=[
            PlanReviewQuestion(
                id="review_overall",
                question="整体节奏合适吗？",
                context="共 2 个场景。",
                related_scene_ids=["scene_001", "scene_002"],
            )
        ],
    )


# ── Valid plans ──────────────────────────────────────────────────


def test_validate_plan_accepts_valid_plan():
    validate_plan(make_valid_plan())


def test_validate_plan_accepts_empty_scenes():
    plan = AdaptationPlan(
        target_format="short_drama",
        structure="minimal",
    )
    validate_plan(plan)


def test_validate_plan_accepts_empty_review_questions():
    plan = replace(make_valid_plan(), review_questions=[])
    validate_plan(plan)


# ── target_format ────────────────────────────────────────────────


def test_validate_plan_rejects_empty_target_format():
    plan = replace(make_valid_plan(), target_format="")

    with pytest.raises(
        PlanValidationError,
        match="target_format must not be blank",
    ):
        validate_plan(plan)


def test_validate_plan_rejects_whitespace_target_format():
    plan = replace(make_valid_plan(), target_format="  \n\t ")

    with pytest.raises(
        PlanValidationError,
        match="target_format must not be blank",
    ):
        validate_plan(plan)


# ── structure ────────────────────────────────────────────────────


def test_validate_plan_rejects_empty_structure():
    plan = replace(make_valid_plan(), structure="")

    with pytest.raises(
        PlanValidationError,
        match="structure must not be blank",
    ):
        validate_plan(plan)


# ── scene IDs ────────────────────────────────────────────────────


def test_validate_plan_rejects_duplicate_scene_ids():
    scenes = list(make_valid_plan().scenes)
    scenes[1] = replace(scenes[1], id="scene_001")
    plan = replace(make_valid_plan(), scenes=scenes)

    with pytest.raises(
        PlanValidationError,
        match="Duplicate scene id: scene_001",
    ):
        validate_plan(plan)


# ── scene_order ──────────────────────────────────────────────────


def test_validate_plan_rejects_duplicate_scene_order():
    scenes = list(make_valid_plan().scenes)
    scenes[1] = replace(scenes[1], scene_order=1)
    plan = replace(make_valid_plan(), scenes=scenes)

    with pytest.raises(
        PlanValidationError,
        match="Duplicate scene_order: 1",
    ):
        validate_plan(plan)


# ── Public export ────────────────────────────────────────────────


def test_plan_validators_are_public_domain_exports():
    from scriptweaver.domain import plan_validation

    assert plan_validation.validate_plan is validate_plan
    assert plan_validation.PlanValidationError is PlanValidationError
