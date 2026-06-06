from __future__ import annotations

from scriptweaver.ai.provider import AIProviderInputError
from scriptweaver.domain.models import (
    AIAnalysis,
    AdaptationDecision,
    AdaptationPlan,
    CandidateScene,
    Chapter,
    Character,
    CharacterRelationship,
    Conflict,
    KeyEvent,
    PlanReviewQuestion,
    ScenePlan,
    ScreenplayDraft,
    Theme,
    Uncertainty,
    UncertaintyOption,
)


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

        chapter_indexes = [chapter.index for chapter in chapters]
        character_ids = ["char_001", "char_002"]

        return AIAnalysis(
            characters=[
                Character(
                    id="char_001",
                    name="主角",
                    role="protagonist",
                    description="推动调查并承担主要风险的人物。",
                    goal="理解所有章节中的关键事件。",
                    motivation="找到事件背后的真相。",
                ),
                Character(
                    id="char_002",
                    name="关键关系人",
                    role="supporting",
                    description="与主角合作但保留关键信息的人物。",
                    goal="影响主角对真相的选择。",
                    motivation="避免关键事件造成更大代价。",
                ),
            ],
            relationships=[
                CharacterRelationship(
                    id="relationship_001",
                    source_character_id="char_001",
                    target_character_id="char_002",
                    description="双方共同调查，但对是否公开真相存在分歧。",
                    source_chapter_indexes=list(chapter_indexes),
                )
            ],
            key_events=[
                KeyEvent(
                    id=f"event_{position:03d}",
                    summary=f"{chapter.title}: {chapter.content}",
                    character_ids=list(character_ids),
                    source_chapter_indexes=[chapter.index],
                )
                for position, chapter in enumerate(chapters, start=1)
            ],
            conflicts=[
                Conflict(
                    id="conflict_001",
                    description=(
                        f"主角需要理解《{chapters[0].title}》中的关键事件，"
                        "但后续章节不断提高代价。"
                    ),
                    stakes="如果主角无法理解真相，关键关系和后续选择都会受到影响。",
                    character_ids=list(character_ids),
                    source_chapter_indexes=list(chapter_indexes),
                )
            ],
            themes=[
                Theme(
                    id="theme_001",
                    statement="理解真相需要面对不断提高的代价。",
                    source_chapter_indexes=list(chapter_indexes),
                )
            ],
            candidate_scenes=[
                CandidateScene(
                    id=f"candidate_scene_{position:03d}",
                    title=chapter.title,
                    summary=chapter.content,
                    dramatic_purpose=(
                        f"将{chapter.title}的关键事件转化为可见的戏剧行动。"
                    ),
                    location="待作者确认",
                    time_hint="待作者确认",
                    character_ids=list(character_ids),
                    source_chapter_indexes=[chapter.index],
                )
                for position, chapter in enumerate(chapters, start=1)
            ],
            uncertainties=[
                Uncertainty(
                    id="uncertainty_001",
                    question="关键关系人是否提前知道主角发现的线索？",
                    context="人物动机将影响后续场景冲突。",
                    options=[
                        UncertaintyOption(
                            id="option_001",
                            label="提前知情",
                            description="关键关系人一直知道主角发现的线索。",
                            impact="强化隐瞒与信任冲突。",
                        ),
                        UncertaintyOption(
                            id="option_002",
                            label="刚刚得知",
                            description="关键关系人与主角同时发现线索。",
                            impact="强化共同调查关系。",
                        ),
                    ],
                    allow_custom_answer=True,
                    source_chapter_indexes=list(chapter_indexes),
                )
            ],
        )


class MockPlanProvider:
    """Deterministic adaptation plan provider for tests and demos."""

    def generate_plan(
        self,
        confirmed_analysis: AIAnalysis,
        chapters: list[Chapter],
    ) -> AdaptationPlan:
        chapter_indexes = [c.index for c in chapters]
        character_ids = [c.id for c in confirmed_analysis.characters]
        event_ids = [e.id for e in confirmed_analysis.key_events]

        return AdaptationPlan(
            target_format="1-3 minute short drama",
            structure=f"{len(chapters)} scenes, linear narrative",
            scenes=[
                ScenePlan(
                    id=f"scene_{i:03d}",
                    scene_order=i,
                    title=chapter.title,
                    dramatic_purpose=(
                        f"将{chapter.title}的关键事件转化为可见的戏剧行动。"
                    ),
                    character_ids=list(character_ids),
                    source_chapter_indexes=[chapter.index],
                    retained_event_ids=[
                        eid
                        for eid in event_ids
                        if chapter.index in (
                            e.source_chapter_indexes
                            for e in confirmed_analysis.key_events
                            if e.id == eid
                        )
                    ]
                    or [event_ids[(i - 1) % len(event_ids)]]
                    if event_ids
                    else [],
                    source_candidate_scene_ids=[
                        f"candidate_scene_{i:03d}"
                    ],
                    compression_choices=[
                        AdaptationDecision(
                            id=f"compression_{i:03d}",
                            description=(
                                f"将{chapter.title}的时间线压缩为单一场"
                                "景。"
                            ),
                            reason="短剧需要在有限时间内展现核心冲突。",
                            source_event_ids=(
                                [event_ids[(i - 1) % len(event_ids)]]
                                if event_ids
                                else []
                            ),
                        )
                    ],
                    merge_choices=[],
                    rewrite_choices=[],
                    review_questions=[
                        PlanReviewQuestion(
                            id=f"review_{i:03d}",
                            question=(
                                f"场景 {i} 的{chapter.title}改编是否"
                                "保留了核心冲突？"
                            ),
                            context=(
                                f"原始章节包含{len(chapter.content)}"
                                "字内容。"
                            ),
                            related_scene_ids=[f"scene_{i:03d}"],
                        )
                    ],
                )
                for i, chapter in enumerate(chapters, start=1)
            ],
            review_questions=[
                PlanReviewQuestion(
                    id="review_overall",
                    question="整体结构是否符合短剧节奏要求？",
                    context=f"共 {len(chapters)} 个章节改编为场景。",
                    related_scene_ids=[
                        f"scene_{i:03d}"
                        for i in range(1, len(chapters) + 1)
                    ],
                )
            ],
        )


class MockScreenplayProvider:
    """Deterministic screenplay provider for tests and demos."""

    def generate_screenplay(
        self,
        confirmed_plan: AdaptationPlan,
        chapters: list[Chapter],
    ) -> ScreenplayDraft:
        scene_ids = [scene.id for scene in confirmed_plan.scenes]
        return ScreenplayDraft(
            scene_ids=list(scene_ids),
            revision_notes=[
                f"场景 {scene.scene_order}「{scene.title}」需要导演审查节奏。"
                for scene in confirmed_plan.scenes
            ],
        )
