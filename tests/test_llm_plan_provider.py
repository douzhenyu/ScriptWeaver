"""Tests for LLMPlanProvider."""

import pytest

from scriptweaver.ai.provider import AIProviderInputError
from scriptweaver.domain.models import (
    AIAnalysis,
    AdaptationDecision,
    AdaptationPlan,
    Chapter,
    Character,
    KeyEvent,
    PlanReviewQuestion,
    ScenePlan,
)
from scriptweaver.llm.client import StructuredLLMError


class FakeLLMClient:
    """Returns a pre-configured JSON response for deterministic tests."""

    def __init__(self, response: dict | None = None) -> None:
        self._response = response or {}
        self.last_system_prompt: str | None = None
        self.last_input_prompt: str | None = None

    def generate_json(
        self,
        system_prompt: str,
        input_prompt: str,
    ) -> dict:
        self.last_system_prompt = system_prompt
        self.last_input_prompt = input_prompt
        return self._response


class RaisingLLMClient:
    """Raises StructuredLLMError on every call."""

    def generate_json(
        self,
        system_prompt: str,
        input_prompt: str,
    ) -> dict:
        raise StructuredLLMError("LLM unavailable")


def make_valid_llm_response() -> dict:
    return {
        "target_format": "1-3 minute short drama",
        "structure": "3 scenes, linear narrative",
        "scenes": [
            {
                "id": "scene_001",
                "scene_order": 1,
                "title": "密信出现",
                "dramatic_purpose": "建立调查目标。",
                "character_ids": ["char_001"],
                "source_chapter_indexes": [1],
                "retained_event_ids": ["event_001"],
                "source_candidate_scene_ids": ["candidate_scene_001"],
                "compression_choices": [
                    {
                        "id": "comp_001",
                        "description": "压缩第一章时间线。",
                        "reason": "短剧需要紧凑开场。",
                        "source_event_ids": ["event_001"],
                    }
                ],
                "merge_choices": [],
                "rewrite_choices": [],
                "review_questions": [
                    {
                        "id": "review_001",
                        "question": "开场是否足够吸引观众？",
                        "context": "第一章以密信为核心悬念。",
                        "related_scene_ids": ["scene_001"],
                    }
                ],
            },
        ],
        "review_questions": [
            {
                "id": "review_overall",
                "question": "整体结构是否符合短剧节奏？",
                "context": "共 1 个场景。",
                "related_scene_ids": ["scene_001"],
            }
        ],
    }


def make_chapters() -> list[Chapter]:
    return [
        Chapter(index=1, title="第一章", content="林照收到密信。"),
    ]


def make_confirmed_analysis() -> AIAnalysis:
    return AIAnalysis(
        characters=[
            Character(
                id="char_001",
                name="林照",
                role="protagonist",
                description="调查旧案的人。",
                goal="查明真相。",
                motivation="保护家人。",
            )
        ],
        key_events=[
            KeyEvent(
                id="event_001",
                summary="林照收到密信。",
                character_ids=["char_001"],
                source_chapter_indexes=[1],
            )
        ],
    )


# ── Tests ───────────────────────────────────────────────────────────


def test_generates_plan_from_valid_response():
    from scriptweaver.ai.llm_plan_provider import LLMPlanProvider

    client = FakeLLMClient(make_valid_llm_response())
    provider = LLMPlanProvider(client)

    plan = provider.generate_plan(make_confirmed_analysis(), make_chapters())

    assert isinstance(plan, AdaptationPlan)
    assert plan.target_format == "1-3 minute short drama"
    assert len(plan.scenes) == 1
    assert plan.scenes[0].id == "scene_001"
    assert plan.scenes[0].scene_order == 1


def test_validates_plan_after_parsing():
    from scriptweaver.ai.llm_plan_provider import LLMPlanProvider

    response = make_valid_llm_response()
    # Duplicate scene id
    response["scenes"].append(response["scenes"][0].copy())
    client = FakeLLMClient(response)
    provider = LLMPlanProvider(client)

    with pytest.raises(RuntimeError):
        provider.generate_plan(make_confirmed_analysis(), make_chapters())


def test_rejects_missing_scenes_key():
    from scriptweaver.ai.llm_plan_provider import LLMPlanProvider

    client = FakeLLMClient({"target_format": "x", "structure": "y"})
    provider = LLMPlanProvider(client)

    with pytest.raises(RuntimeError, match="scenes"):
        provider.generate_plan(make_confirmed_analysis(), make_chapters())


def test_passes_chapters_to_llm():
    from scriptweaver.ai.llm_plan_provider import LLMPlanProvider

    client = FakeLLMClient(make_valid_llm_response())
    provider = LLMPlanProvider(client)
    chapters = make_chapters()

    provider.generate_plan(make_confirmed_analysis(), chapters)

    assert client.last_input_prompt is not None
    assert "林照收到密信" in client.last_input_prompt


def test_wraps_llm_error():
    from scriptweaver.ai.llm_plan_provider import LLMPlanProvider

    provider = LLMPlanProvider(RaisingLLMClient())

    with pytest.raises(RuntimeError, match="LLM unavailable"):
        provider.generate_plan(make_confirmed_analysis(), make_chapters())


def test_input_validation_empty_chapters():
    from scriptweaver.ai.llm_plan_provider import LLMPlanProvider

    provider = LLMPlanProvider(FakeLLMClient())

    with pytest.raises(AIProviderInputError, match="At least 1 chapter"):
        provider.generate_plan(make_confirmed_analysis(), [])


def test_parses_nested_decisions():
    from scriptweaver.ai.llm_plan_provider import LLMPlanProvider

    client = FakeLLMClient(make_valid_llm_response())
    provider = LLMPlanProvider(client)

    plan = provider.generate_plan(make_confirmed_analysis(), make_chapters())

    scene = plan.scenes[0]
    assert len(scene.compression_choices) == 1
    assert isinstance(scene.compression_choices[0], AdaptationDecision)
    assert scene.compression_choices[0].id == "comp_001"


def test_parses_review_questions():
    from scriptweaver.ai.llm_plan_provider import LLMPlanProvider

    client = FakeLLMClient(make_valid_llm_response())
    provider = LLMPlanProvider(client)

    plan = provider.generate_plan(make_confirmed_analysis(), make_chapters())

    assert len(plan.review_questions) == 1
    assert isinstance(plan.review_questions[0], PlanReviewQuestion)
    assert plan.review_questions[0].id == "review_overall"
    # Scene-level review questions
    assert len(plan.scenes[0].review_questions) == 1
