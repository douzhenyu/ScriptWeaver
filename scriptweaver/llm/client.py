from __future__ import annotations

from typing import Any, Protocol


class StructuredLLMError(RuntimeError):
    """Raised when a structured LLM request cannot produce a JSON object."""


class StructuredLLMClient(Protocol):
    def generate_json(
        self,
        system_prompt: str,
        input_prompt: str,
    ) -> dict[str, Any]:
        """Generate exactly one parsed JSON object."""
