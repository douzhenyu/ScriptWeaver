from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from scriptweaver.llm.client import StructuredLLMError


JSON_OBJECT_INSTRUCTION = (
    "Return exactly one valid JSON object. "
    "Do not include Markdown fences or explanatory text."
)


class OpenAICompatibleStructuredLLMClient:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float = 120.0,
    ) -> None:
        self._validate_configuration(
            api_key=api_key,
            base_url=base_url,
            model=model,
            timeout_seconds=timeout_seconds,
        )
        self._model = model
        self._sdk_client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_seconds,
            max_retries=0,
        )

    @staticmethod
    def _validate_configuration(
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float,
    ) -> None:
        for field_name, value in (
            ("api_key", api_key),
            ("base_url", base_url),
            ("model", model),
        ):
            if not value.strip():
                raise StructuredLLMError(f"{field_name} must not be blank")
        if timeout_seconds <= 0:
            raise StructuredLLMError(
                "timeout_seconds must be greater than 0"
            )

    def generate_json(
        self,
        system_prompt: str,
        input_prompt: str,
    ) -> dict[str, Any]:
        if not input_prompt.strip():
            raise StructuredLLMError("input_prompt must not be blank")

        normalized_system_prompt = system_prompt.strip()
        combined_system_prompt = (
            f"{normalized_system_prompt}\n\n{JSON_OBJECT_INSTRUCTION}"
            if normalized_system_prompt
            else JSON_OBJECT_INSTRUCTION
        )

        response = self._sdk_client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": combined_system_prompt},
                {"role": "user", "content": input_prompt},
            ],
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
