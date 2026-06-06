from __future__ import annotations

from scriptweaver.llm.openai_compatible import (
    OpenAICompatibleStructuredLLMClient,
)


DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_DEFAULT_MODEL = "deepseek-v4-flash"


class DeepSeekStructuredLLMClient(OpenAICompatibleStructuredLLMClient):
    def __init__(
        self,
        api_key: str,
        base_url: str = DEEPSEEK_BASE_URL,
        model: str = DEEPSEEK_DEFAULT_MODEL,
        timeout_seconds: float = 120.0,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model,
            timeout_seconds=timeout_seconds,
        )
