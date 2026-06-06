from __future__ import annotations

from scriptweaver.domain.models import AdaptationPlan


class PlanValidationError(ValueError):
    """Raised when an adaptation plan fails validation."""


def validate_plan(plan: AdaptationPlan) -> None:
    if not plan.target_format.strip():
        raise PlanValidationError("target_format must not be blank")

    if not plan.structure.strip():
        raise PlanValidationError("structure must not be blank")

    scene_ids: set[str] = set()
    scene_orders: set[int] = set()

    for scene in plan.scenes:
        if scene.id in scene_ids:
            raise PlanValidationError(
                f"Duplicate scene id: {scene.id}"
            )
        scene_ids.add(scene.id)

        if scene.scene_order in scene_orders:
            raise PlanValidationError(
                f"Duplicate scene_order: {scene.scene_order}"
            )
        scene_orders.add(scene.scene_order)
