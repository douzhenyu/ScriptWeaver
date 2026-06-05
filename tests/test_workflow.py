import pytest

from scriptweaver.domain.workflow import (
    AdaptationState,
    WorkflowTransitionError,
    ensure_transition_allowed,
)


def test_allows_expected_workflow_progression():
    progression = [
        AdaptationState.CREATED,
        AdaptationState.CHAPTERS_UPLOADED,
        AdaptationState.ANALYSIS_GENERATED,
        AdaptationState.ANALYSIS_CONFIRMED,
        AdaptationState.PLAN_GENERATED,
        AdaptationState.PLAN_CONFIRMED,
        AdaptationState.SCREENPLAY_GENERATED,
    ]

    for current_state, next_state in zip(progression, progression[1:]):
        ensure_transition_allowed(current_state, next_state)


def test_rejects_skipping_required_user_confirmation():
    with pytest.raises(WorkflowTransitionError, match="Cannot transition"):
        ensure_transition_allowed(
            AdaptationState.ANALYSIS_GENERATED,
            AdaptationState.PLAN_GENERATED,
        )


def test_rejects_regressing_to_previous_state():
    with pytest.raises(WorkflowTransitionError, match="Cannot transition"):
        ensure_transition_allowed(
            AdaptationState.PLAN_CONFIRMED,
            AdaptationState.ANALYSIS_CONFIRMED,
        )
