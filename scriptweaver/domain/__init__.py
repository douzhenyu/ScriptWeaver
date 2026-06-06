"""Domain models and workflow primitives for ScriptWeaver."""

from scriptweaver.domain.analysis_validation import (
    AnalysisValidationError,
    validate_analysis,
)
from scriptweaver.domain.models import (
    AIAnalysis,
    AdaptationDecision,
    AdaptationJob,
    AdaptationPlan,
    Chapter,
    Character,
    PlanReviewQuestion,
    ScenePlan,
    ScreenplayDraft,
    UncertaintyOption,
    UncertaintyResolution,
    UserConfirmations,
)
from scriptweaver.domain.plan_validation import (
    PlanValidationError,
    validate_plan,
)
from scriptweaver.domain.uncertainty_validation import (
    UncertaintyValidationError,
    validate_uncertainties,
    validate_uncertainty_resolutions,
)
from scriptweaver.domain.workflow import (
    AdaptationState,
    WorkflowTransitionError,
    ensure_transition_allowed,
)

__all__ = [
    "AIAnalysis",
    "AdaptationDecision",
    "AdaptationJob",
    "AdaptationPlan",
    "AdaptationState",
    "AnalysisValidationError",
    "Chapter",
    "Character",
    "PlanReviewQuestion",
    "PlanValidationError",
    "ScenePlan",
    "ScreenplayDraft",
    "UncertaintyOption",
    "UncertaintyResolution",
    "UncertaintyValidationError",
    "UserConfirmations",
    "WorkflowTransitionError",
    "ensure_transition_allowed",
    "validate_analysis",
    "validate_plan",
    "validate_uncertainties",
    "validate_uncertainty_resolutions",
]
