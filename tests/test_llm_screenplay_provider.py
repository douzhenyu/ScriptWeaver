"""Tests for LLMScreenplayProvider."""

import pytest

from scriptweaver.ai.provider import AIProviderInputError
from scriptweaver.domain.models import (
    AdaptationPlan,
    Beat,
    Chapter,
    SceneHeading,
    ScenePlan,
    ScreenplayDraft,
    ScreenplayScene,
)
from scriptweaver.llm.client import StructuredLLMError


class FakeLLMClient:
    def __init__(self, response: dict | None = None) -> None:
        self._response = response or {}
        self.last_input_prompt: str | None = None

    def generate_json(self, system_prompt: str, input_prompt: str) -> dict:
        self.last_input_prompt = input_prompt
        return self._response


class RaisingLLMClient:
    def generate_json(self, system_prompt: str, input_prompt: str) -> dict:
        raise StructuredLLMError("LLM unavailable")


def make_valid_response() -> dict:
    return {
        "scenes": [
            {
                "id": "scene_001",
                "heading": {
                    "location": "茶馆",
                    "time": "夜",
                    "interior_exterior": "INT",
                },
                "source_chapter_indexes": [1],
                "character_ids": ["char_001"],
                "beats": [
                    {
                        "type": "action",
                        "text": "林照拆开密信，手指微微颤抖。",
                    },
                    {
                        "type": "dialogue",
                        "text": "这不是父亲的笔迹。",
                        "character_id": "char_001",
                    },
                    {
                        "type": "action",
                        "text": "她将信纸翻到背面，发现一行小字。",
                    },
                    {
                        "type": "dialogue",
                        "text": "难道……他还活着？",
                        "character_id": "char_001",
                    },
                ],
            },
        ],
        "revision_notes": ["场景 1 需要审查节奏。"],
    }


def make_plan() -> AdaptationPlan:
    return AdaptationPlan(
        target_format="short_drama",
        structure="1 scene",
        scenes=[
            ScenePlan(
                id="scene_001",
                scene_order=1,
                title="密信出现",
                dramatic_purpose="建立目标。",
                character_ids=["char_001"],
                source_chapter_indexes=[1],
            ),
        ],
    )


def make_chapters() -> list[Chapter]:
    return [Chapter(index=1, title="第一章", content="林照收到密信。")]


# ── Tests ───────────────────────────────────────────────────────────


def test_generates_screenplay_from_valid_response():
    from scriptweaver.ai.llm_screenplay_provider import (
        LLMScreenplayProvider,
    )

    client = FakeLLMClient(make_valid_response())
    provider = LLMScreenplayProvider(client)

    draft = provider.generate_screenplay(make_plan(), make_chapters())

    assert isinstance(draft, ScreenplayDraft)
    assert len(draft.scenes) == 1
    assert draft.scenes[0].id == "scene_001"
    assert draft.scenes[0].heading.location == "茶馆"
    assert len(draft.scenes[0].beats) == 4


def test_parses_scene_heading():
    from scriptweaver.ai.llm_screenplay_provider import (
        LLMScreenplayProvider,
    )

    client = FakeLLMClient(make_valid_response())
    provider = LLMScreenplayProvider(client)

    draft = provider.generate_screenplay(make_plan(), make_chapters())
    heading = draft.scenes[0].heading

    assert isinstance(heading, SceneHeading)
    assert heading.interior_exterior == "INT"


def test_parses_beats_with_types():
    from scriptweaver.ai.llm_screenplay_provider import (
        LLMScreenplayProvider,
    )

    client = FakeLLMClient(make_valid_response())
    provider = LLMScreenplayProvider(client)

    draft = provider.generate_screenplay(make_plan(), make_chapters())
    beats = draft.scenes[0].beats

    assert beats[0].type == "action"
    assert isinstance(beats[0], Beat)
    assert beats[1].type == "dialogue"
    assert beats[1].character_id == "char_001"


def test_rejects_missing_scenes_key():
    from scriptweaver.ai.llm_screenplay_provider import (
        LLMScreenplayProvider,
    )

    client = FakeLLMClient({})
    provider = LLMScreenplayProvider(client)

    with pytest.raises(RuntimeError, match="scenes"):
        provider.generate_screenplay(make_plan(), make_chapters())


def test_wraps_llm_error():
    from scriptweaver.ai.llm_screenplay_provider import (
        LLMScreenplayProvider,
    )

    provider = LLMScreenplayProvider(RaisingLLMClient())

    with pytest.raises(RuntimeError, match="LLM unavailable"):
        provider.generate_screenplay(make_plan(), make_chapters())


def test_input_validation_empty_chapters():
    from scriptweaver.ai.llm_screenplay_provider import (
        LLMScreenplayProvider,
    )

    provider = LLMScreenplayProvider(FakeLLMClient())

    with pytest.raises(AIProviderInputError, match="chapter"):
        provider.generate_screenplay(make_plan(), [])


def test_passes_plan_info_to_llm():
    from scriptweaver.ai.llm_screenplay_provider import (
        LLMScreenplayProvider,
    )

    client = FakeLLMClient(make_valid_response())
    provider = LLMScreenplayProvider(client)

    provider.generate_screenplay(make_plan(), make_chapters())

    assert client.last_input_prompt is not None
    assert "密信出现" in client.last_input_prompt
    assert "林照收到密信" in client.last_input_prompt


def test_parses_revision_notes():
    from scriptweaver.ai.llm_screenplay_provider import (
        LLMScreenplayProvider,
    )

    client = FakeLLMClient(make_valid_response())
    provider = LLMScreenplayProvider(client)

    draft = provider.generate_screenplay(make_plan(), make_chapters())

    assert len(draft.revision_notes) == 1
    assert "审查节奏" in draft.revision_notes[0]
