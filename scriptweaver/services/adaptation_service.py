from __future__ import annotations

from dataclasses import replace

from scriptweaver.ai.provider import AIAnalysisProvider
from scriptweaver.domain.models import AIAnalysis, AdaptationJob, Chapter
from scriptweaver.domain.workflow import AdaptationState, ensure_transition_allowed


class AdaptationServiceError(ValueError):
    """Raised when an adaptation service request is invalid."""


class AdaptationService:
    def __init__(self, ai_provider: AIAnalysisProvider) -> None:
        self._ai_provider = ai_provider

    def create_job(self, job_id: str) -> AdaptationJob:
        return AdaptationJob(id=job_id)

    def attach_chapters(
        self,
        job: AdaptationJob,
        chapters: list[Chapter],
    ) -> AdaptationJob:
        if len(chapters) < 3:
            raise AdaptationServiceError("At least 3 chapters are required")

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
        analysis = AIAnalysis(
            characters=list(provider_analysis.characters),
            conflicts=list(provider_analysis.conflicts),
            key_events=list(provider_analysis.key_events),
        )

        return replace(
            job,
            state=AdaptationState.ANALYSIS_GENERATED,
            ai_analysis=analysis,
        )
