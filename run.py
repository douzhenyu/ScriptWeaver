"""ScriptWeaver demo server – start with `python run.py`."""
from scriptweaver.ai.mock_provider import (
    MockAIAnalysisProvider,
    MockPlanProvider,
    MockScreenplayProvider,
)
from scriptweaver.api.app import create_app
import uvicorn

app = create_app(
    ai_provider=MockAIAnalysisProvider(),
    plan_provider=MockPlanProvider(),
    screenplay_provider=MockScreenplayProvider(),
)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8137)
