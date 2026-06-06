from typing import Any

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
