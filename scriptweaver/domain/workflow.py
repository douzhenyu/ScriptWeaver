from __future__ import annotations

from enum import StrEnum


class AdaptationState(StrEnum):
    CREATED = "created"
    CHAPTERS_UPLOADED = "chapters_uploaded"
    ANALYSIS_GENERATED = "analysis_generated"
    ANALYSIS_CONFIRMED = "analysis_confirmed"
    PLAN_GENERATED = "plan_generated"
    PLAN_CONFIRMED = "plan_confirmed"
    SCREENPLAY_GENERATED = "screenplay_generated"


class WorkflowTransitionError(ValueError):
    """Raised when an adaptation job transition is not allowed."""


ALLOWED_TRANSITIONS: dict[AdaptationState, set[AdaptationState]] = {
    AdaptationState.CREATED: {AdaptationState.CHAPTERS_UPLOADED},
    AdaptationState.CHAPTERS_UPLOADED: {AdaptationState.ANALYSIS_GENERATED},
    AdaptationState.ANALYSIS_GENERATED: {AdaptationState.ANALYSIS_CONFIRMED},
    AdaptationState.ANALYSIS_CONFIRMED: {AdaptationState.PLAN_GENERATED},
    AdaptationState.PLAN_GENERATED: {AdaptationState.PLAN_CONFIRMED},
    AdaptationState.PLAN_CONFIRMED: {AdaptationState.SCREENPLAY_GENERATED},
    AdaptationState.SCREENPLAY_GENERATED: set(),
}


def ensure_transition_allowed(
    current_state: AdaptationState,
    next_state: AdaptationState,
) -> None:
    allowed_next_states = ALLOWED_TRANSITIONS[current_state]
    if next_state not in allowed_next_states:
        raise WorkflowTransitionError(
            f"Cannot transition adaptation job from {current_state.value} "
            f"to {next_state.value}"
        )
