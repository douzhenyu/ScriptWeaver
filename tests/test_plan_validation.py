from dataclasses import replace

import pytest

from scriptweaver.domain.models import (
    AIAnalysis,
    AdaptationDecision,
    AdaptationPlan,
    CandidateScene,
    Character,
    KeyEvent,
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


# ── PR 40: Context-aware validation helpers ────────────────────────


def make_context() -> tuple[AIAnalysis, set[int]]:
    """Build confirmed_analysis and chapter_indexes matching make_valid_plan."""
    analysis = AIAnalysis(
        characters=[
            Character(
                id="char_001", name="A", role="protagonist",
                description="d", goal="g", motivation="m",
            ),
            Character(
                id="char_002", name="B", role="supporting",
                description="d", goal="g", motivation="m",
            ),
        ],
        key_events=[
            KeyEvent(
                id="event_001", summary="事件1",
                character_ids=["char_001"], source_chapter_indexes=[1],
            ),
            KeyEvent(
                id="event_002", summary="事件2",
                character_ids=["char_002"], source_chapter_indexes=[2],
            ),
        ],
        candidate_scenes=[
            CandidateScene(
                id="candidate_scene_001", title="候选1",
                summary="摘要1", dramatic_purpose="目的1",
                location="L", time_hint="T", character_ids=[],
                source_chapter_indexes=[1],
            ),
            CandidateScene(
                id="candidate_scene_002", title="候选2",
                summary="摘要2", dramatic_purpose="目的2",
                location="L", time_hint="T", character_ids=[],
                source_chapter_indexes=[2],
            ),
        ],
    )
    chapter_indexes = {1, 2}
    return analysis, chapter_indexes


def test_validate_plan_with_context_accepts_valid_plan():
    """Valid plan with full context must pass."""
    analysis, chapters = make_context()
    validate_plan(make_valid_plan(),
                  confirmed_analysis=analysis,
                  chapter_indexes=chapters)


def test_validate_plan_accepts_legacy_call_without_context():
    """Calling validate_plan without context must still work."""
    validate_plan(make_valid_plan())


# ── Blank scene fields ─────────────────────────────────────────────


def test_rejects_blank_scene_id():
    analysis, chapters = make_context()
    scenes = list(make_valid_plan().scenes)
    scenes[0] = replace(scenes[0], id="")
    plan = replace(make_valid_plan(), scenes=scenes)

    with pytest.raises(PlanValidationError, match="scene id must not be blank"):
        validate_plan(plan, confirmed_analysis=analysis,
                      chapter_indexes=chapters)


def test_rejects_blank_scene_title():
    analysis, chapters = make_context()
    scenes = list(make_valid_plan().scenes)
    scenes[0] = replace(scenes[0], title="")
    plan = replace(make_valid_plan(), scenes=scenes)

    with pytest.raises(PlanValidationError, match="title must not be blank"):
        validate_plan(plan, confirmed_analysis=analysis,
                      chapter_indexes=chapters)


def test_rejects_blank_dramatic_purpose():
    analysis, chapters = make_context()
    scenes = list(make_valid_plan().scenes)
    scenes[0] = replace(scenes[0], dramatic_purpose="")
    plan = replace(make_valid_plan(), scenes=scenes)

    with pytest.raises(PlanValidationError,
                       match="dramatic_purpose must not be blank"):
        validate_plan(plan, confirmed_analysis=analysis,
                      chapter_indexes=chapters)


# ── scene_order consecutive ────────────────────────────────────────


def test_rejects_scene_order_not_starting_from_one():
    analysis, chapters = make_context()
    scenes = list(make_valid_plan().scenes)
    scenes[0] = replace(scenes[0], scene_order=2)
    scenes[1] = replace(scenes[1], scene_order=3)
    plan = replace(make_valid_plan(), scenes=scenes)

    with pytest.raises(PlanValidationError,
                       match="scene_order must be 1..2 consecutive"):
        validate_plan(plan, confirmed_analysis=analysis,
                      chapter_indexes=chapters)


def test_rejects_non_consecutive_scene_order():
    analysis, chapters = make_context()
    scenes = list(make_valid_plan().scenes)
    scenes[1] = replace(scenes[1], scene_order=3)
    plan = replace(make_valid_plan(), scenes=scenes)

    with pytest.raises(PlanValidationError, match="consecutive"):
        validate_plan(plan, confirmed_analysis=analysis,
                      chapter_indexes=chapters)


# ── Reference validation ───────────────────────────────────────────


def test_rejects_unknown_character_reference():
    analysis, chapters = make_context()
    scenes = list(make_valid_plan().scenes)
    scenes[0] = replace(scenes[0], character_ids=["char_nonexistent"])
    plan = replace(make_valid_plan(), scenes=scenes)

    with pytest.raises(PlanValidationError, match="unknown character"):
        validate_plan(plan, confirmed_analysis=analysis,
                      chapter_indexes=chapters)


def test_rejects_unknown_chapter_index():
    analysis, chapters = make_context()
    scenes = list(make_valid_plan().scenes)
    scenes[0] = replace(scenes[0], source_chapter_indexes=[99])
    plan = replace(make_valid_plan(), scenes=scenes)

    with pytest.raises(PlanValidationError, match="unknown chapter index"):
        validate_plan(plan, confirmed_analysis=analysis,
                      chapter_indexes=chapters)


def test_rejects_unknown_retained_event():
    analysis, chapters = make_context()
    scenes = list(make_valid_plan().scenes)
    scenes[0] = replace(scenes[0], retained_event_ids=["event_nonexistent"])
    plan = replace(make_valid_plan(), scenes=scenes)

    with pytest.raises(PlanValidationError, match="unknown event"):
        validate_plan(plan, confirmed_analysis=analysis,
                      chapter_indexes=chapters)


def test_rejects_unknown_candidate_scene():
    analysis, chapters = make_context()
    scenes = list(make_valid_plan().scenes)
    scenes[0] = replace(
        scenes[0], source_candidate_scene_ids=["candidate_nonexistent"]
    )
    plan = replace(make_valid_plan(), scenes=scenes)

    with pytest.raises(PlanValidationError,
                       match="unknown candidate scene"):
        validate_plan(plan, confirmed_analysis=analysis,
                      chapter_indexes=chapters)


def test_rejects_decision_with_unknown_event():
    analysis, chapters = make_context()
    scenes = list(make_valid_plan().scenes)
    invalid_decision = AdaptationDecision(
        id="bad_decision",
        description="desc",
        reason="reason",
        source_event_ids=["event_nonexistent"],
    )
    scenes[0] = replace(
        scenes[0], compression_choices=[invalid_decision],
    )
    plan = replace(make_valid_plan(), scenes=scenes)

    with pytest.raises(PlanValidationError, match="unknown event"):
        validate_plan(plan, confirmed_analysis=analysis,
                      chapter_indexes=chapters)


def test_rejects_review_question_with_unknown_scene():
    analysis, chapters = make_context()
    rq = PlanReviewQuestion(
        id="rq_bad",
        question="Q?",
        context="ctx",
        related_scene_ids=["scene_nonexistent"],
    )
    plan = replace(make_valid_plan(), review_questions=[rq])

    with pytest.raises(PlanValidationError, match="unknown scene"):
        validate_plan(plan, confirmed_analysis=analysis,
                      chapter_indexes=chapters)


# ── ID uniqueness ──────────────────────────────────────────────────


def test_rejects_duplicate_decision_id_within_scene():
    analysis, chapters = make_context()
    d = AdaptationDecision(
        id="dup_decision", description="d1", reason="r",
    )
    scenes = list(make_valid_plan().scenes)
    scenes[0] = replace(
        scenes[0],
        compression_choices=[d, d],
    )
    plan = replace(make_valid_plan(), scenes=scenes)

    with pytest.raises(PlanValidationError,
                       match="duplicate decision id"):
        validate_plan(plan, confirmed_analysis=analysis,
                      chapter_indexes=chapters)


def test_rejects_duplicate_review_question_id():
    analysis, chapters = make_context()
    rq = PlanReviewQuestion(
        id="dup_rq", question="Q", context="C",
    )
    plan = replace(
        make_valid_plan(),
        review_questions=[rq, rq],
    )

    with pytest.raises(PlanValidationError,
                       match="Duplicate review question id"):
        validate_plan(plan, confirmed_analysis=analysis,
                      chapter_indexes=chapters)


def test_rejects_blank_decision_id():
    analysis, chapters = make_context()
    d = AdaptationDecision(id="", description="d", reason="r")
    scenes = list(make_valid_plan().scenes)
    scenes[0] = replace(scenes[0], compression_choices=[d])
    plan = replace(make_valid_plan(), scenes=scenes)

    with pytest.raises(PlanValidationError,
                       match="decision id must not be blank"):
        validate_plan(plan, confirmed_analysis=analysis,
                      chapter_indexes=chapters)


def test_accepts_forward_reference_in_review_question():
    """A review question in an earlier scene may reference a later scene."""
    rq = PlanReviewQuestion(
        id="rq_fwd", question="Q", context="C",
        related_scene_ids=["scene_002"],
    )
    scenes = list(make_valid_plan().scenes)
    scenes[0] = replace(scenes[0], review_questions=[rq])
    plan = replace(make_valid_plan(), scenes=scenes)
    validate_plan(plan)


def test_rejects_character_reference_when_analysis_empty():
    """Plan referencing a character must fail even when analysis has none."""
    plan = replace(make_valid_plan(), scenes=[
        replace(s, character_ids=["ghost"])
        for s in make_valid_plan().scenes
    ])
    with pytest.raises(PlanValidationError, match="unknown character"):
        validate_plan(plan, confirmed_analysis=AIAnalysis())
