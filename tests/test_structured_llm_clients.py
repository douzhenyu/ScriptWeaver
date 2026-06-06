from types import SimpleNamespace
from typing import Any

import pytest

from scriptweaver.llm import StructuredLLMClient, StructuredLLMError


class RecordingStructuredLLMClient:
    def generate_json(
        self,
        system_prompt: str,
        input_prompt: str,
    ) -> dict[str, Any]:
        return {
            "system_prompt": system_prompt,
            "input_prompt": input_prompt,
        }


def use_structured_client(
    client: StructuredLLMClient,
) -> dict[str, Any]:
    return client.generate_json("system rules", "task input")


def test_structured_llm_protocol_accepts_compatible_client():
    result = use_structured_client(RecordingStructuredLLMClient())

    assert result == {
        "system_prompt": "system rules",
        "input_prompt": "task input",
    }


def test_structured_llm_error_is_runtime_error():
    assert issubclass(StructuredLLMError, RuntimeError)


# ---- Fake SDK helpers ----

class FakeCompletions:
    def __init__(self, content: str = '{"status": "ok"}') -> None:
        self.content = content
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self.content),
                )
            ]
        )


class FakeOpenAIFactory:
    def __init__(self, completions: FakeCompletions | None = None) -> None:
        self.completions = completions or FakeCompletions()
        self.calls: list[dict[str, Any]] = []

    def __call__(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return SimpleNamespace(
            chat=SimpleNamespace(completions=self.completions),
        )


# ---- Happy-path and request-construction tests ----

def test_openai_compatible_client_generates_json_object(monkeypatch):
    from scriptweaver.llm import openai_compatible
    from scriptweaver.llm.openai_compatible import (
        JSON_OBJECT_INSTRUCTION,
        OpenAICompatibleStructuredLLMClient,
    )

    completions = FakeCompletions('{"characters": ["林照"]}')
    factory = FakeOpenAIFactory(completions)
    monkeypatch.setattr(openai_compatible, "OpenAI", factory)

    client = OpenAICompatibleStructuredLLMClient(
        api_key="secret-key",
        base_url="https://example.test/v1",
        model="example-model",
        timeout_seconds=45.0,
    )

    result = client.generate_json(
        system_prompt="Analyze the supplied novel.",
        input_prompt="第一章：林照收到密信。",
    )

    assert result == {"characters": ["林照"]}
    assert factory.calls == [
        {
            "api_key": "secret-key",
            "base_url": "https://example.test/v1",
            "timeout": 45.0,
            "max_retries": 0,
        }
    ]
    assert completions.calls == [
        {
            "model": "example-model",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Analyze the supplied novel.\n\n"
                        f"{JSON_OBJECT_INSTRUCTION}"
                    ),
                },
                {
                    "role": "user",
                    "content": "第一章：林照收到密信。",
                },
            ],
            "response_format": {"type": "json_object"},
        }
    ]


def test_openai_compatible_client_uses_json_instruction_as_empty_system_prompt(
    monkeypatch,
):
    from scriptweaver.llm import openai_compatible
    from scriptweaver.llm.openai_compatible import (
        JSON_OBJECT_INSTRUCTION,
        OpenAICompatibleStructuredLLMClient,
    )

    completions = FakeCompletions()
    monkeypatch.setattr(
        openai_compatible,
        "OpenAI",
        FakeOpenAIFactory(completions),
    )
    client = OpenAICompatibleStructuredLLMClient(
        api_key="secret-key",
        base_url="https://example.test/v1",
        model="example-model",
    )

    client.generate_json(system_prompt=" \n ", input_prompt="Task input")

    assert completions.calls[0]["messages"][0] == {
        "role": "system",
        "content": JSON_OBJECT_INSTRUCTION,
    }


# ---- Configuration and input-validation tests ----

@pytest.mark.parametrize(
    ("field_name", "overrides"),
    [
        ("api_key", {"api_key": " \n "}),
        ("base_url", {"base_url": ""}),
        ("model", {"model": "\t"}),
        ("timeout_seconds", {"timeout_seconds": 0}),
        ("timeout_seconds", {"timeout_seconds": -1}),
    ],
)
def test_openai_compatible_client_rejects_invalid_configuration(
    monkeypatch,
    field_name,
    overrides,
):
    from scriptweaver.llm import openai_compatible
    from scriptweaver.llm.openai_compatible import (
        OpenAICompatibleStructuredLLMClient,
    )

    factory = FakeOpenAIFactory()
    monkeypatch.setattr(openai_compatible, "OpenAI", factory)
    values = {
        "api_key": "secret-key",
        "base_url": "https://example.test/v1",
        "model": "example-model",
        "timeout_seconds": 120.0,
        **overrides,
    }

    with pytest.raises(StructuredLLMError, match=field_name):
        OpenAICompatibleStructuredLLMClient(**values)

    assert factory.calls == []


@pytest.mark.parametrize("input_prompt", ["", " ", "\n\t"])
def test_openai_compatible_client_rejects_blank_input_without_request(
    monkeypatch,
    input_prompt,
):
    from scriptweaver.llm import openai_compatible
    from scriptweaver.llm.openai_compatible import (
        OpenAICompatibleStructuredLLMClient,
    )

    completions = FakeCompletions()
    monkeypatch.setattr(
        openai_compatible,
        "OpenAI",
        FakeOpenAIFactory(completions),
    )
    client = OpenAICompatibleStructuredLLMClient(
        api_key="secret-key",
        base_url="https://example.test/v1",
        model="example-model",
    )

    with pytest.raises(StructuredLLMError, match="input_prompt"):
        client.generate_json("system", input_prompt)

    assert completions.calls == []
