from __future__ import annotations

from typing import Protocol

from scriptweaver.domain.models import AIAnalysis, Chapter


class AIProviderInputError(ValueError):
    """Raised when an AI provider receives invalid input."""


class AIAnalysisProvider(Protocol):
    def analyze_chapters(self, chapters: list[Chapter]) -> AIAnalysis:
        """Analyze source chapters and return AI story analysis."""
