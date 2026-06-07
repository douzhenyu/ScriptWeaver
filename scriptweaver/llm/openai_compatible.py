from __future__ import annotations

import json
import time
from typing import Any

from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)

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

    # Retryable transient errors — not auth or bad-request
    _RETRYABLE = (RateLimitError, APITimeoutError, APIConnectionError,
                  InternalServerError)

    def _call_api(self, system_prompt: str, input_prompt: str, attempt: int):
        try:
            return self._sdk_client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": input_prompt},
                ],
                response_format={"type": "json_object"},
            )
        except self._RETRYABLE as error:
            if attempt < 3:
                delay = 2 ** (attempt - 1)  # 1s, 2s, 4s
                time.sleep(delay)
                return None  # signal to retry
            raise StructuredLLMError(
                f"LLM request failed after {attempt} attempts: {error}"
            ) from error
        except OpenAIError as error:
            raise StructuredLLMError(
                f"LLM request failed: {error}"
            ) from error

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

        response = None
        for attempt in range(1, 4):  # up to 3 attempts
            response = self._call_api(combined_system_prompt, input_prompt, attempt)
            if response is not None:
                break

        if response is None:
            raise StructuredLLMError(
                "LLM request failed after 3 attempts"
            )

        choices = getattr(response, "choices", None)
        if not choices:
            raise StructuredLLMError(
                "Structured LLM response has no choices"
            )

        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", None)
        if not isinstance(content, str) or not content.strip():
            raise StructuredLLMError(
                "Structured LLM response content is empty"
            )

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as error:
            raise StructuredLLMError(
                "Structured LLM response content is not valid JSON"
            ) from error

        if not isinstance(parsed, dict):
            raise StructuredLLMError(
                "Structured LLM response must be a JSON object"
            )

        return parsed
