from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from scriptweaver.domain.workflow import AdaptationState


@dataclass(frozen=True)
class Chapter:
    index: int
    title: str
    content: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Character:
    id: str
    name: str
    role: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AIAnalysis:
    characters: list[Character] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    key_events: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "characters": [character.to_dict() for character in self.characters],
            "conflicts": list(self.conflicts),
            "key_events": list(self.key_events),
        }


@dataclass(frozen=True)
class UserConfirmations:
    accepted_character_ids: list[str] = field(default_factory=list)
    required_plot_points: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AdaptationPlan:
    target_format: str
    structure: str
    scene_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScreenplayDraft:
    scene_ids: list[str] = field(default_factory=list)
    revision_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AdaptationJob:
    id: str
    state: AdaptationState = AdaptationState.CREATED
    chapters: list[Chapter] = field(default_factory=list)
    ai_analysis: AIAnalysis | None = None
    user_confirmations: UserConfirmations | None = None
    adaptation_plan: AdaptationPlan | None = None
    screenplay_draft: ScreenplayDraft | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "state": self.state.value,
            "chapters": [chapter.to_dict() for chapter in self.chapters],
            "ai_analysis": (
                self.ai_analysis.to_dict() if self.ai_analysis is not None else None
            ),
            "user_confirmations": (
                self.user_confirmations.to_dict()
                if self.user_confirmations is not None
                else None
            ),
            "adaptation_plan": (
                self.adaptation_plan.to_dict()
                if self.adaptation_plan is not None
                else None
            ),
            "screenplay_draft": (
                self.screenplay_draft.to_dict()
                if self.screenplay_draft is not None
                else None
            ),
        }
