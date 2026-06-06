# ScriptWeaver

Human-in-the-loop AI backend for adapting novel chapters into structured screenplay drafts.

## Quick Start

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install with dependencies
python3 -m pip install -e ".[dev]"

# Run the backend
uvicorn scriptweaver.api.app:app --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok"}
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/jobs` | Create adaptation job |
| `GET` | `/jobs/{id}` | Get job state |
| `POST` | `/jobs/{id}/chapters` | Upload novel chapters |
| `POST` | `/jobs/{id}/analyze` | Run AI story analysis |
| `GET` | `/jobs/{id}/next-uncertainty` | Get next unanswered uncertainty |
| `POST` | `/jobs/{id}/uncertainty-answer` | Submit uncertainty answer |
| `POST` | `/jobs/{id}/confirm-analysis` | Confirm analysis (derives from AI analysis + answers) |
| `POST` | `/jobs/{id}/generate-plan` | Generate adaptation plan |
| `POST` | `/jobs/{id}/confirm-plan` | Confirm adaptation plan |
| `POST` | `/jobs/{id}/generate-screenplay` | Generate screenplay draft |
| `GET` | `/jobs/{id}/export-yaml` | Export screenplay as YAML |

## Full Workflow (curl)

```bash
JOB="demo-001"
BASE="http://127.0.0.1:8000"

# 1. Create job
curl -s -X POST "$BASE/jobs" -H "Content-Type: application/json" \
  -d "{\"job_id\": \"$JOB\"}"

# 2. Upload chapters
curl -s -X POST "$BASE/jobs/$JOB/chapters" -H "Content-Type: application/json" \
  -d '{"chapters": [{"index":1,"title":"第一章","content":"林照收到密信。"},{"index":2,"title":"第二章","content":"沈微阻止公开。"},{"index":3,"title":"第三章","content":"密信指向旧案。"}]}'

# 3. Generate AI analysis
curl -s -X POST "$BASE/jobs/$JOB/analyze"

# 4. Answer uncertainty
curl -s -X POST "$BASE/jobs/$JOB/uncertainty-answer" -H "Content-Type: application/json" \
  -d '{"uncertainty_id":"uncertainty_001","selected_option_id":"option_001"}'

# 5. Confirm analysis
curl -s -X POST "$BASE/jobs/$JOB/confirm-analysis"

# 6. Generate plan
curl -s -X POST "$BASE/jobs/$JOB/generate-plan"

# 7. Confirm plan
curl -s -X POST "$BASE/jobs/$JOB/confirm-plan" -H "Content-Type: application/json" \
  -d '{"target_format":"short_drama","structure":"3 scenes","scenes":[{"id":"scene_001","scene_order":1,"title":"Scene 1","dramatic_purpose":"建立目标"},{"id":"scene_002","scene_order":2,"title":"Scene 2","dramatic_purpose":"升级冲突"},{"id":"scene_003","scene_order":3,"title":"Scene 3","dramatic_purpose":"揭示真相"}],"review_questions":[]}'

# 8. Generate screenplay
curl -s -X POST "$BASE/jobs/$JOB/generate-screenplay"

# 9. Export YAML
curl -s "$BASE/jobs/$JOB/export-yaml?title=密信&author=测试&target_format=short_drama&language=zh-CN"
```

## Workflow States

```
created → chapters_uploaded → analysis_generated → analysis_confirmed
         → plan_generated → plan_confirmed → screenplay_generated
```

## AI Providers

The default app uses Mock providers for development. For production, inject LLM-backed providers:

```python
from scriptweaver.ai.llm_provider import LLMAnalysisProvider
from scriptweaver.ai.llm_plan_provider import LLMPlanProvider
from scriptweaver.ai.llm_screenplay_provider import LLMScreenplayProvider
from scriptweaver.llm.qwen import QwenStructuredLLMClient
from scriptweaver.api.app import create_app

client = QwenStructuredLLMClient(api_key="...")
app = create_app(
    ai_provider=LLMAnalysisProvider(client),
    plan_provider=LLMPlanProvider(client),
    screenplay_provider=LLMScreenplayProvider(client),
)
```

## Development

```bash
# Run tests
.venv/bin/python -m pytest -q

# Compile check
.venv/bin/python -m compileall -q scriptweaver
```

## YAML Output Schema

See [docs/screenplay-yaml-schema.md](docs/screenplay-yaml-schema.md) for the full YAML output specification.
