import pytest

from scriptweaver.ai.llm_provider import (
    LLMAnalysisProvider,
    AIProviderError,
)
from scriptweaver.ai.provider import AIProviderInputError
from scriptweaver.domain.models import (
    AIAnalysis,
    Chapter,
    Character,
    Conflict,
    KeyEvent,
    Theme,
    CandidateScene,
    CharacterRelationship,
    Uncertainty,
    UncertaintyOption,
)
from scriptweaver.llm.client import StructuredLLMError


# ── Fake LLM clients ─────────────────────────────────────────────


class FakeStructuredLLMClient:
    def __init__(self, json_response: dict | None = None):
        self._json_response = json_response or {}
        self.last_system_prompt: str | None = None
        self.last_input_prompt: str | None = None

    def generate_json(self, system_prompt: str, input_prompt: str) -> dict:
        self.last_system_prompt = system_prompt
        self.last_input_prompt = input_prompt
        return self._json_response


class RaisingStructuredLLMClient:
    def __init__(self, error: Exception):
        self._error = error

    def generate_json(self, system_prompt: str, input_prompt: str) -> dict:
        raise self._error


# ── Helpers ──────────────────────────────────────────────────────


def make_chapters() -> list[Chapter]:
    return [
        Chapter(index=1, title="第一章", content="林照收到父亲留下的密信。"),
        Chapter(index=2, title="第二章", content="沈微出现并阻止林照公开密信。"),
    ]


def make_valid_llm_response() -> dict:
    return {
        "characters": [
            {
                "id": "char_001",
                "name": "林照",
                "role": "protagonist",
                "description": "调查旧案的年轻人。",
                "goal": "查明真相。",
                "motivation": "保护家人。",
            },
            {
                "id": "char_002",
                "name": "沈微",
                "role": "supporting",
                "description": "与主角合作的神秘人物。",
                "goal": "阻止真相公开。",
                "motivation": "避免更大代价。",
            },
        ],
        "relationships": [
            {
                "id": "rel_001",
                "source_character_id": "char_001",
                "target_character_id": "char_002",
                "description": "共同调查但对公开真相有分歧。",
                "source_chapter_indexes": [1, 2],
            }
        ],
        "key_events": [
            {
                "id": "event_001",
                "summary": "林照收到密信。",
                "character_ids": ["char_001"],
                "source_chapter_indexes": [1],
            },
            {
                "id": "event_002",
                "summary": "沈微阻止林照公开密信。",
                "character_ids": ["char_001", "char_002"],
                "source_chapter_indexes": [2],
            },
        ],
        "conflicts": [
            {
                "id": "conflict_001",
                "description": "公开真相还是保守秘密。",
                "stakes": "错误选择会破坏关键关系。",
                "character_ids": ["char_001", "char_002"],
                "source_chapter_indexes": [1, 2],
            }
        ],
        "themes": [
            {
                "id": "theme_001",
                "statement": "真相与代价的博弈。",
                "source_chapter_indexes": [1, 2],
            }
        ],
        "candidate_scenes": [
            {
                "id": "scene_001",
                "title": "收到密信",
                "summary": "林照在家中收到父亲留下的密信。",
                "dramatic_purpose": "建立核心悬念。",
                "location": "林照家中",
                "time_hint": "傍晚",
                "character_ids": ["char_001"],
                "source_chapter_indexes": [1],
            }
        ],
        "uncertainties": [
            {
                "id": "uncertainty_001",
                "question": "沈微是否提前知道密信内容？",
                "context": "影响人物动机可信度。",
                "source_chapter_indexes": [1, 2],
                "options": [
                    {
                        "id": "opt_001",
                        "label": "提前知情",
                        "description": "沈微一直知道密信存在。",
                        "impact": "强化隐瞒与信任冲突。",
                    },
                    {
                        "id": "opt_002",
                        "label": "刚刚得知",
                        "description": "沈微与林照同时发现密信。",
                        "impact": "强化共同调查关系。",
                    },
                ],
                "allow_custom_answer": True,
            }
        ],
    }


# ── Input validation ─────────────────────────────────────────────


def test_llm_provider_rejects_empty_chapter_list():
    provider = LLMAnalysisProvider(FakeStructuredLLMClient())

    with pytest.raises(
        AIProviderInputError,
        match="At least 1 chapter is required",
    ):
        provider.analyze_chapters([])


def test_llm_provider_rejects_empty_chapter_content():
    provider = LLMAnalysisProvider(FakeStructuredLLMClient())
    chapters = [
        Chapter(index=1, title="第一章", content="正常内容。"),
        Chapter(index=2, title="空章节", content=" \n\t "),
    ]

    with pytest.raises(AIProviderInputError, match="空章节 is empty"):
        provider.analyze_chapters(chapters)


# ── LLM interaction ──────────────────────────────────────────────


def test_llm_provider_calls_client_with_chapters():
    fake_client = FakeStructuredLLMClient(make_valid_llm_response())
    provider = LLMAnalysisProvider(fake_client)
    chapters = make_chapters()

    provider.analyze_chapters(chapters)

    assert fake_client.last_system_prompt is not None
    assert "story" in fake_client.last_system_prompt.lower()
    assert "林照" in fake_client.last_input_prompt
    assert "沈微" in fake_client.last_input_prompt
    assert "第一章" in fake_client.last_input_prompt
    assert "第二章" in fake_client.last_input_prompt


# ── Response parsing ─────────────────────────────────────────────


def test_llm_provider_parses_valid_response():
    fake_client = FakeStructuredLLMClient(make_valid_llm_response())
    provider = LLMAnalysisProvider(fake_client)
    chapters = make_chapters()

    analysis = provider.analyze_chapters(chapters)

    assert isinstance(analysis, AIAnalysis)
    assert len(analysis.characters) == 2
    assert analysis.characters[0].id == "char_001"
    assert analysis.characters[0].name == "林照"
    assert len(analysis.relationships) == 1
    assert analysis.relationships[0].id == "rel_001"
    assert len(analysis.key_events) == 2
    assert len(analysis.conflicts) == 1
    assert len(analysis.themes) == 1
    assert len(analysis.candidate_scenes) == 1
    assert len(analysis.uncertainties) == 1
    assert analysis.uncertainties[0].options[0].id == "opt_001"


def test_llm_provider_handles_zero_items_in_category():
    fake_client = FakeStructuredLLMClient({
        "characters": [],
        "relationships": [],
        "key_events": [],
        "conflicts": [],
        "themes": [],
        "candidate_scenes": [],
        "uncertainties": [],
    })
    provider = LLMAnalysisProvider(fake_client)

    analysis = provider.analyze_chapters(make_chapters())

    assert isinstance(analysis, AIAnalysis)
    assert analysis.characters == []
    assert analysis.relationships == []
    assert analysis.key_events == []


def test_llm_provider_accepts_fields_with_defaults_missing():
    fake_client = FakeStructuredLLMClient({
        "characters": [
            {
                "id": "char_001",
                "name": "林照",
                "role": "protagonist",
                "description": "描述",
                "goal": "目标",
                "motivation": "动机",
            }
        ],
        "relationships": [
            {
                "id": "rel_001",
                "source_character_id": "char_001",
                "target_character_id": "char_002",
                "description": "关系描述",
            }
        ],
        "key_events": [{"id": "ev_001", "summary": "事件摘要"}],
        "conflicts": [
            {"id": "cn_001", "description": "冲突描述", "stakes": "赌注"}
        ],
        "themes": [{"id": "th_001", "statement": "主题陈述"}],
        "candidate_scenes": [
            {
                "id": "sc_001",
                "title": "场景标题",
                "summary": "场景摘要",
                "dramatic_purpose": "戏剧目的",
                "location": "地点",
                "time_hint": "时间",
            }
        ],
        "uncertainties": [
            {
                "id": "un_001",
                "question": "问题？",
                "context": "上下文",
            }
        ],
    })

    provider = LLMAnalysisProvider(fake_client)
    analysis = provider.analyze_chapters(make_chapters())

    assert analysis.relationships[0].source_chapter_indexes == []
    assert analysis.key_events[0].character_ids == []
    assert analysis.uncertainties[0].options == []
    assert analysis.uncertainties[0].allow_custom_answer is True


# ── Error handling ───────────────────────────────────────────────


def test_llm_provider_wraps_structured_llm_error():
    fake_client = RaisingStructuredLLMClient(
        StructuredLLMError("API request timed out")
    )
    provider = LLMAnalysisProvider(fake_client)

    with pytest.raises(AIProviderError, match="API request timed out"):
        provider.analyze_chapters(make_chapters())


def test_llm_provider_wraps_unexpected_error():
    fake_client = RaisingStructuredLLMClient(ValueError("unexpected"))
    provider = LLMAnalysisProvider(fake_client)

    with pytest.raises(AIProviderError, match="LLM analysis failed"):
        provider.analyze_chapters(make_chapters())


def test_llm_provider_rejects_missing_category():
    response = make_valid_llm_response()
    del response["themes"]
    fake_client = FakeStructuredLLMClient(response)
    provider = LLMAnalysisProvider(fake_client)

    with pytest.raises(AIProviderError, match="themes"):
        provider.analyze_chapters(make_chapters())


def test_llm_provider_rejects_non_list_category():
    fake_client = FakeStructuredLLMClient({
        "characters": "not a list",
        "relationships": [],
        "key_events": [],
        "conflicts": [],
        "themes": [],
        "candidate_scenes": [],
        "uncertainties": [],
    })
    provider = LLMAnalysisProvider(fake_client)

    with pytest.raises(AIProviderError, match="characters"):
        provider.analyze_chapters(make_chapters())


def test_llm_provider_rejects_item_missing_required_field():
    # KeyEvent requires 'summary' — missing it should raise an error
    fake_client = FakeStructuredLLMClient({
        "characters": [],
        "relationships": [],
        "key_events": [
            {
                "id": "evt_001",
                # missing required 'summary' field
            }
        ],
        "conflicts": [],
        "themes": [],
        "candidate_scenes": [],
        "uncertainties": [],
    })
    provider = LLMAnalysisProvider(fake_client)

    with pytest.raises(AIProviderError, match="Failed to parse key_events"):
        provider.analyze_chapters(make_chapters())


def test_llm_provider_character_defaults_for_missing_fields():
    # Character missing role/description/goal/motivation gets empty defaults
    fake_client = FakeStructuredLLMClient({
        "characters": [
            {"id": "char_001", "name": "林照"}
        ],
        "relationships": [],
        "key_events": [],
        "conflicts": [],
        "themes": [],
        "candidate_scenes": [],
        "uncertainties": [],
    })
    provider = LLMAnalysisProvider(fake_client)
    analysis = provider.analyze_chapters(make_chapters())
    c = analysis.characters[0]
    assert c.name == "林照"
    assert c.role == ""
    assert c.goal == ""
    assert c.motivation == ""


def test_llm_provider_ignores_extra_fields():
    fake_client = FakeStructuredLLMClient({
        "characters": [
            {
                "id": "char_001",
                "name": "林照",
                "role": "protagonist",
                "description": "描述",
                "goal": "目标",
                "motivation": "动机",
                "extra_field": "should be ignored",
            }
        ],
        "relationships": [],
        "key_events": [],
        "conflicts": [],
        "themes": [],
        "candidate_scenes": [],
        "uncertainties": [],
        "extra_category": "should be ignored",
    })

    provider = LLMAnalysisProvider(fake_client)
    analysis = provider.analyze_chapters(make_chapters())

    assert len(analysis.characters) == 1
    assert analysis.characters[0].name == "林照"


def test_llm_provider_accepts_single_chapter():
    fake_client = FakeStructuredLLMClient(make_valid_llm_response())
    provider = LLMAnalysisProvider(fake_client)
    chapters = make_chapters()[:1]

    analysis = provider.analyze_chapters(chapters)

    assert isinstance(analysis, AIAnalysis)
    assert "第一章" in fake_client.last_input_prompt
    assert "第二章" not in fake_client.last_input_prompt
