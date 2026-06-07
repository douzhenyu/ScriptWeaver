from __future__ import annotations

from typing import Protocol

from scriptweaver.domain.models import (
    AIAnalysis,
    AdaptationPlan,
    Chapter,
    ScreenplayDraft,
    UserConfirmations,
)


class AIProviderInputError(ValueError):
    """Raised when an AI provider receives invalid input."""


class AIAnalysisProvider(Protocol):
    def analyze_chapters(self, chapters: list[Chapter]) -> AIAnalysis:
        """Analyze source chapters and return AI story analysis."""


class AdaptationPlanProvider(Protocol):
    def generate_plan(
        self,
        confirmed_analysis: AIAnalysis,
        chapters: list[Chapter],
        user_confirmations: UserConfirmations | None = None,
    ) -> AdaptationPlan:
        """Generate adaptation plan from confirmed analysis, chapters, and
        author confirmations."""


class ScreenplayProvider(Protocol):
    def generate_screenplay(
        self,
        confirmed_plan: AdaptationPlan,
        chapters: list[Chapter],
    ) -> ScreenplayDraft:
        """Generate screenplay draft from confirmed plan and chapters."""
