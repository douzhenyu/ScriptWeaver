# ScriptWeaver

ScriptWeaver is a human-in-the-loop AI backend for helping novel authors adapt three or more novel chapters into editable screenplay drafts.

## Development

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the backend with development dependencies:

```bash
python3 -m pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run the backend locally:

```bash
uvicorn scriptweaver.api.app:app --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Current Scope

This backend skeleton only provides a health check. Future PRs will add adaptation jobs, chapter intake, AI analysis, user confirmations, adaptation planning, and screenplay YAML generation.
