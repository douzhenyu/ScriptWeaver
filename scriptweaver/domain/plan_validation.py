from __future__ import annotations

from scriptweaver.domain.models import AIAnalysis, AdaptationPlan


class PlanValidationError(ValueError):
    """Raised when an adaptation plan fails validation."""


def validate_plan(
    plan: AdaptationPlan,
    *,
    confirmed_analysis: AIAnalysis | None = None,
    chapter_indexes: set[int] | None = None,
) -> None:
    if not plan.target_format.strip():
        raise PlanValidationError("target_format must not be blank")

    if not plan.structure.strip():
        raise PlanValidationError("structure must not be blank")

    # Build context lookups
    character_ids: set[str] = set()
    event_ids: set[str] = set()
    candidate_scene_ids: set[str] = set()
    if confirmed_analysis is not None:
        character_ids = {c.id for c in confirmed_analysis.characters}
        event_ids = {e.id for e in confirmed_analysis.key_events}
        candidate_scene_ids = {
            s.id for s in confirmed_analysis.candidate_scenes
        }

    scene_ids: set[str] = set()
    scene_orders: set[int] = set()
    all_review_question_ids: set[str] = set()

    for scene in plan.scenes:
        # ── Blank checks ────────────────────────────────────
        if not scene.id.strip():
            raise PlanValidationError("scene id must not be blank")

        if scene.id in scene_ids:
            raise PlanValidationError(
                f"Duplicate scene id: {scene.id}"
            )
        scene_ids.add(scene.id)

        if not scene.title.strip():
            raise PlanValidationError(
                f"scene {scene.id}: title must not be blank"
            )

        if not scene.dramatic_purpose.strip():
            raise PlanValidationError(
                f"scene {scene.id}: dramatic_purpose must not be blank"
            )

        # ── scene_order uniqueness ───────────────────────────
        if scene.scene_order in scene_orders:
            raise PlanValidationError(
                f"Duplicate scene_order: {scene.scene_order}"
            )
        scene_orders.add(scene.scene_order)

        # ── Character references ──────────────────────────────
        if confirmed_analysis is not None:
            for cid in scene.character_ids:
                if cid not in character_ids:
                    raise PlanValidationError(
                        f"scene {scene.id}: unknown character '{cid}'"
                    )

        # ── Chapter index references ──────────────────────────
        if chapter_indexes is not None:
            for ci in scene.source_chapter_indexes:
                if ci not in chapter_indexes:
                    raise PlanValidationError(
                        f"scene {scene.id}: unknown chapter index {ci}"
                    )

        # ── Retained event / candidate scene references ────────
        # Not validated strictly — LLM may not reproduce exact IDs.
        # Unknown IDs are silently tolerated; they don't break the plan.

        # ── Decision validation ───────────────────────────────
        decision_ids: set[str] = set()
        for attr in (
            "compression_choices", "merge_choices", "rewrite_choices",
        ):
            for d in getattr(scene, attr):
                if not d.id.strip():
                    raise PlanValidationError(
                        f"scene {scene.id}: decision id must not be "
                        f"blank"
                    )
                if d.id in decision_ids:
                    raise PlanValidationError(
                        f"scene {scene.id}: duplicate decision id "
                        f"'{d.id}'"
                    )
                decision_ids.add(d.id)
                if confirmed_analysis is not None:
                    for eid in d.source_event_ids:
                        if eid not in event_ids:
                            raise PlanValidationError(
                                f"scene {scene.id} decision {d.id}: "
                                f"unknown event '{eid}'"
                            )

        # ── Scene-level review questions ──────────────────────
        for rq in scene.review_questions:
            if rq.id in all_review_question_ids:
                raise PlanValidationError(
                    f"Duplicate review question id: {rq.id}"
                )
            all_review_question_ids.add(rq.id)

    # ── scene_order consecutive from 1 ────────────────────────
    if scene_orders:
        expected = set(range(1, len(plan.scenes) + 1))
        if scene_orders != expected:
            raise PlanValidationError(
                f"scene_order must be 1..{len(plan.scenes)} "
                f"consecutive, got: {sorted(scene_orders)}"
            )

    # ── Validate all review question scene references ──────────
    for rq in plan.review_questions:
        if rq.id in all_review_question_ids:
            raise PlanValidationError(
                f"Duplicate review question id: {rq.id}"
            )
        all_review_question_ids.add(rq.id)
    for rq in plan.review_questions:
        for rsid in rq.related_scene_ids:
            if rsid not in scene_ids:
                raise PlanValidationError(
                    f"review question {rq.id}: unknown scene '{rsid}'"
                )
    for scene in plan.scenes:
        for rq in scene.review_questions:
            for rsid in rq.related_scene_ids:
                if rsid not in scene_ids:
                    raise PlanValidationError(
                        f"review question {rq.id}: unknown scene "
                        f"'{rsid}'"
                    )
