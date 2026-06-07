"""ScriptWeaver demo server — start with `python run.py`.

Environment variables:
  SW_LLM_PROVIDER   mock (default) | deepseek | qwen
  SW_API_KEY        API key for the selected provider
  SW_PORT           Listen port (default 8000)
"""

import os
from pathlib import Path
import uvicorn

from scriptweaver.ai.mock_provider import (
    MockAIAnalysisProvider,
    MockPlanProvider,
    MockScreenplayProvider,
)
from scriptweaver.api.app import create_app

PROVIDER = os.getenv("SW_LLM_PROVIDER", "mock").lower()
API_KEY = os.getenv("SW_API_KEY", "")
PORT = int(os.getenv("SW_PORT", "8000"))

if PROVIDER == "mock" or not API_KEY:
    ai = MockAIAnalysisProvider()
    plan = MockPlanProvider()
    screenplay = MockScreenplayProvider()
elif PROVIDER == "deepseek":
    from scriptweaver.llm.deepseek import DeepSeekStructuredLLMClient
    from scriptweaver.ai.llm_provider import LLMAnalysisProvider
    from scriptweaver.ai.llm_plan_provider import LLMPlanProvider
    from scriptweaver.ai.llm_screenplay_provider import LLMScreenplayProvider

    client = DeepSeekStructuredLLMClient(api_key=API_KEY)
    ai = LLMAnalysisProvider(client)
    plan = LLMPlanProvider(client)
    screenplay = LLMScreenplayProvider(client)
elif PROVIDER == "qwen":
    from scriptweaver.llm.qwen import QwenStructuredLLMClient
    from scriptweaver.ai.llm_provider import LLMAnalysisProvider
    from scriptweaver.ai.llm_plan_provider import LLMPlanProvider
    from scriptweaver.ai.llm_screenplay_provider import LLMScreenplayProvider

    client = QwenStructuredLLMClient(api_key=API_KEY)
    ai = LLMAnalysisProvider(client)
    plan = LLMPlanProvider(client)
    screenplay = LLMScreenplayProvider(client)
else:
    raise ValueError(f"Unknown SW_LLM_PROVIDER: {PROVIDER}")

_web_dir = Path(__file__).parent / "scriptweaver" / "web"
app = create_app(
    ai_provider=ai,
    plan_provider=plan,
    screenplay_provider=screenplay,
    static_dir=str(_web_dir) if _web_dir.is_dir() else None,
)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT)
