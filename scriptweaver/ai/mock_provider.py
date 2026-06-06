from __future__ import annotations

from scriptweaver.ai.provider import AIProviderInputError
from scriptweaver.domain.models import AIAnalysis, Chapter, Character


class MockAIAnalysisProvider:
    """Deterministic AI analysis provider for tests and demos."""

    def analyze_chapters(self, chapters: list[Chapter]) -> AIAnalysis:
        if not chapters:
            raise AIProviderInputError(
                "At least 1 chapter is required for analysis"
            )

        for chapter in chapters:
            if not chapter.content.strip():
                raise AIProviderInputError(f"{chapter.title} is empty")

        return AIAnalysis(
            characters=[
                Character(id="char_001", name="主角", role="protagonist"),
                Character(id="char_002", name="关键关系人", role="supporting"),
            ],
            conflicts=[
                f"主角需要理解《{chapters[0].title}》中的关键事件，"
                "但后续章节不断提高代价。"
            ],
            key_events=[
                f"{chapter.title}: {chapter.content}"
                for chapter in chapters
            ],
        )
