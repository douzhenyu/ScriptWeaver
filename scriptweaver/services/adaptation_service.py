from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

from scriptweaver.ai.provider import (
    AIAnalysisProvider,
    AdaptationPlanProvider,
    ScreenplayProvider,
)
from scriptweaver.domain.analysis_validation import validate_analysis
from scriptweaver.domain.models import (
    AIAnalysis,
    AdaptationJob,
    AdaptationPlan,
    Chapter,
    Uncertainty,
    UncertaintyResolution,
    UserConfirmations,
)
from scriptweaver.domain.plan_validation import validate_plan
from scriptweaver.domain.uncertainty_validation import (
    validate_uncertainty_resolutions,
)
from scriptweaver.domain.workflow import AdaptationState, ensure_transition_allowed


class AdaptationServiceError(ValueError):
    """Raised when an adaptation service request is invalid."""


class AdaptationService:
    def __init__(
        self,
        ai_provider: AIAnalysisProvider,
        plan_provider: AdaptationPlanProvider | None = None,
        screenplay_provider: ScreenplayProvider | None = None,
    ) -> None:
        self._ai_provider = ai_provider
        self._plan_provider = plan_provider
        self._screenplay_provider = screenplay_provider

    def create_job(self, job_id: str) -> AdaptationJob:
        return AdaptationJob(id=job_id)

    def attach_chapters(
        self,
        job: AdaptationJob,
        chapters: list[Chapter],
    ) -> AdaptationJob:
        if not chapters:
            raise AdaptationServiceError("At least 1 chapter is required")

        for chapter in chapters:
            if not chapter.content.strip():
                raise AdaptationServiceError(f"{chapter.title} is empty")

        ensure_transition_allowed(job.state, AdaptationState.CHAPTERS_UPLOADED)

        return replace(
            job,
            state=AdaptationState.CHAPTERS_UPLOADED,
            chapters=list(chapters),
        )

    def generate_analysis(self, job: AdaptationJob) -> AdaptationJob:
        ensure_transition_allowed(job.state, AdaptationState.ANALYSIS_GENERATED)

        provider_analysis = self._ai_provider.analyze_chapters(list(job.chapters))
        analysis = deepcopy(provider_analysis)

        chapter_indexes = {chapter.index for chapter in job.chapters}
        validate_analysis(analysis, chapter_indexes)

        return replace(
            job,
            state=AdaptationState.ANALYSIS_GENERATED,
            ai_analysis=analysis,
        )

    def confirm_analysis(self, job: AdaptationJob) -> AdaptationJob:
        if job.ai_analysis is None:
            raise AdaptationServiceError("No AI analysis to confirm")

        ensure_transition_allowed(job.state, AdaptationState.ANALYSIS_CONFIRMED)

        # Require all uncertainties to be resolved before confirmation
        if job.ai_analysis.uncertainties:
            resolved_ids: set[str] = set()
            if job.user_confirmations is not None:
                for r in job.user_confirmations.uncertainty_resolutions:
                    resolved_ids.add(r.uncertainty_id)
            unresolved = [
                u.id
                for u in job.ai_analysis.uncertainties
                if u.id not in resolved_ids
            ]
            if unresolved:
                raise AdaptationServiceError(
                    "Unresolved uncertainties: "
                    + ", ".join(unresolved)
                )

        confirmed = deepcopy(job.ai_analysis)

        if job.user_confirmations is not None:
            accepted_ids = job.user_confirmations.accepted_character_ids
            if accepted_ids:
                accepted_set = set(accepted_ids)

                def _filter_character_ids(
                    ids: list[str],
                ) -> list[str]:
                    return [cid for cid in ids if cid in accepted_set]

                confirmed = replace(
                    confirmed,
                    characters=[
                        c
                        for c in confirmed.characters
                        if c.id in accepted_set
                    ],
                    relationships=[
                        r
                        for r in confirmed.relationships
                        if r.source_character_id in accepted_set
                        and r.target_character_id in accepted_set
                    ],
                    key_events=[
                        replace(
                            e,
                            character_ids=_filter_character_ids(
                                e.character_ids
                            ),
                        )
                        for e in confirmed.key_events
                    ],
                    conflicts=[
                        replace(
                            c,
                            character_ids=_filter_character_ids(
                                c.character_ids
                            ),
                        )
                        for c in confirmed.conflicts
                    ],
                    candidate_scenes=[
                        replace(
                            s,
                            character_ids=_filter_character_ids(
                                s.character_ids
                            ),
                        )
                        for s in confirmed.candidate_scenes
                    ],
                )

        chapter_indexes = {chapter.index for chapter in job.chapters}
        validate_analysis(confirmed, chapter_indexes)

        return replace(
            job,
            state=AdaptationState.ANALYSIS_CONFIRMED,
            confirmed_analysis=confirmed,
        )

    def get_next_unanswered_uncertainty(
        self,
        job: AdaptationJob,
    ) -> Uncertainty | None:
        if job.state != AdaptationState.ANALYSIS_GENERATED:
            raise AdaptationServiceError(
                "get_next_unanswered_uncertainty requires "
                "ANALYSIS_GENERATED state"
            )
        if job.ai_analysis is None:
            return None

        resolved_ids: set[str] = set()
        if job.user_confirmations is not None:
            for resolution in (
                job.user_confirmations.uncertainty_resolutions
            ):
                resolved_ids.add(resolution.uncertainty_id)

        for uncertainty in job.ai_analysis.uncertainties:
            if uncertainty.id not in resolved_ids:
                return uncertainty

        return None

    def submit_uncertainty_answer(
        self,
        job: AdaptationJob,
        resolution: UncertaintyResolution,
    ) -> AdaptationJob:
        if job.state != AdaptationState.ANALYSIS_GENERATED:
            raise AdaptationServiceError(
                "submit_uncertainty_answer requires "
                "ANALYSIS_GENERATED state"
            )
        if job.ai_analysis is None:
            raise AdaptationServiceError(
                "No AI analysis to resolve uncertainties against"
            )

        existing_resolutions: list[UncertaintyResolution] = []
        if job.user_confirmations is not None:
            existing_resolutions = list(
                job.user_confirmations.uncertainty_resolutions
            )

        all_resolutions = existing_resolutions + [resolution]
        validate_uncertainty_resolutions(
            job.ai_analysis.uncertainties,
            all_resolutions,
        )

        if job.user_confirmations is None:
            user_confirmations = UserConfirmations(
                uncertainty_resolutions=[resolution],
            )
        else:
            user_confirmations = replace(
                job.user_confirmations,
                uncertainty_resolutions=all_resolutions,
            )

        return replace(
            job,
            user_confirmations=deepcopy(user_confirmations),
        )

    def generate_plan(self, job: AdaptationJob) -> AdaptationJob:
        ensure_transition_allowed(
            job.state, AdaptationState.PLAN_GENERATED
        )

        if self._plan_provider is None:
            raise AdaptationServiceError(
                "No plan provider configured"
            )

        if job.confirmed_analysis is None:
            raise AdaptationServiceError(
                "No confirmed analysis to generate plan from"
            )

        plan = self._plan_provider.generate_plan(
            job.confirmed_analysis,
            list(job.chapters),
            user_confirmations=job.user_confirmations,
        )

        return replace(
            job,
            state=AdaptationState.PLAN_GENERATED,
            adaptation_plan=deepcopy(plan),
        )

    def confirm_plan(
        self,
        job: AdaptationJob,
        confirmed_plan: AdaptationPlan,
    ) -> AdaptationJob:
        ensure_transition_allowed(
            job.state, AdaptationState.PLAN_CONFIRMED
        )

        validate_plan(confirmed_plan)

        return replace(
            job,
            state=AdaptationState.PLAN_CONFIRMED,
            adaptation_plan=deepcopy(confirmed_plan),
        )

    def generate_screenplay(self, job: AdaptationJob) -> AdaptationJob:
        ensure_transition_allowed(
            job.state, AdaptationState.SCREENPLAY_GENERATED
        )

        if self._screenplay_provider is None:
            raise AdaptationServiceError(
                "No screenplay provider configured"
            )

        if job.adaptation_plan is None:
            raise AdaptationServiceError(
                "No adaptation plan to generate screenplay from"
            )

        draft = self._screenplay_provider.generate_screenplay(
            job.adaptation_plan,
            list(job.chapters),
        )

        return replace(
            job,
            state=AdaptationState.SCREENPLAY_GENERATED,
            screenplay_draft=deepcopy(draft),
        )
