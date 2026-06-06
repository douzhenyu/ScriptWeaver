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
    description: str
    goal: str
    motivation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CharacterRelationship:
    id: str
    source_character_id: str
    target_character_id: str
    description: str
    source_chapter_indexes: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KeyEvent:
    id: str
    summary: str
    character_ids: list[str] = field(default_factory=list)
    source_chapter_indexes: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Conflict:
    id: str
    description: str
    stakes: str
    character_ids: list[str] = field(default_factory=list)
    source_chapter_indexes: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Theme:
    id: str
    statement: str
    source_chapter_indexes: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CandidateScene:
    id: str
    title: str
    summary: str
    dramatic_purpose: str
    location: str
    time_hint: str
    character_ids: list[str] = field(default_factory=list)
    source_chapter_indexes: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UncertaintyOption:
    id: str
    label: str
    description: str
    impact: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Uncertainty:
    id: str
    question: str
    context: str
    options: list[UncertaintyOption] = field(default_factory=list)
    allow_custom_answer: bool = True
    source_chapter_indexes: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AIAnalysis:
    characters: list[Character] = field(default_factory=list)
    relationships: list[CharacterRelationship] = field(default_factory=list)
    key_events: list[KeyEvent] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    themes: list[Theme] = field(default_factory=list)
    candidate_scenes: list[CandidateScene] = field(default_factory=list)
    uncertainties: list[Uncertainty] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "characters": [item.to_dict() for item in self.characters],
            "relationships": [item.to_dict() for item in self.relationships],
            "key_events": [item.to_dict() for item in self.key_events],
            "conflicts": [item.to_dict() for item in self.conflicts],
            "themes": [item.to_dict() for item in self.themes],
            "candidate_scenes": [
                item.to_dict() for item in self.candidate_scenes
            ],
            "uncertainties": [item.to_dict() for item in self.uncertainties],
        }


@dataclass(frozen=True)
class UncertaintyResolution:
    uncertainty_id: str
    selected_option_id: str | None = None
    custom_answer: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UserConfirmations:
    accepted_character_ids: list[str] = field(default_factory=list)
    required_plot_points: list[str] = field(default_factory=list)
    uncertainty_resolutions: list[UncertaintyResolution] = field(
        default_factory=list
    )
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AdaptationDecision:
    id: str
    description: str
    reason: str
    source_event_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PlanReviewQuestion:
    id: str
    question: str
    context: str
    related_scene_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScenePlan:
    id: str
    scene_order: int
    title: str
    dramatic_purpose: str
    character_ids: list[str] = field(default_factory=list)
    source_chapter_indexes: list[int] = field(default_factory=list)
    retained_event_ids: list[str] = field(default_factory=list)
    source_candidate_scene_ids: list[str] = field(default_factory=list)
    compression_choices: list[AdaptationDecision] = field(default_factory=list)
    merge_choices: list[AdaptationDecision] = field(default_factory=list)
    rewrite_choices: list[AdaptationDecision] = field(default_factory=list)
    review_questions: list[PlanReviewQuestion] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AdaptationPlan:
    target_format: str
    structure: str
    scenes: list[ScenePlan] = field(default_factory=list)
    review_questions: list[PlanReviewQuestion] = field(default_factory=list)

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
    confirmed_analysis: AIAnalysis | None = None
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
            "confirmed_analysis": (
                self.confirmed_analysis.to_dict()
                if self.confirmed_analysis is not None
                else None
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
