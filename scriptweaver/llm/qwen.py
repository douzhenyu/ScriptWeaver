from __future__ import annotations

from scriptweaver.llm.openai_compatible import (
    OpenAICompatibleStructuredLLMClient,
)


QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_DEFAULT_MODEL = "qwen-plus"


class QwenStructuredLLMClient(OpenAICompatibleStructuredLLMClient):
    def __init__(
        self,
        api_key: str,
        base_url: str = QWEN_BASE_URL,
        model: str = QWEN_DEFAULT_MODEL,
        timeout_seconds: float = 120.0,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            model=model,
            timeout_seconds=timeout_seconds,
        )
