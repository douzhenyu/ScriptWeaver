"""Tests for the default app entrypoint and static file serving."""

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_app_importable():
    """The module-level `app` must be importable by uvicorn."""
    from scriptweaver.api.app import app

    assert app is not None


def test_app_is_fastapi():
    """The default app must be a FastAPI instance."""
    from scriptweaver.api.app import app

    assert isinstance(app, FastAPI)


def test_default_app_health():
    """The default app health endpoint must return 200."""
    from scriptweaver.api.app import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── PR 45: Static file serving ─────────────────────────────────────


def test_static_dir_serves_index_html():
    """create_app with a static dir must serve index.html at /."""
    from scriptweaver.api.app import create_app
    from scriptweaver.ai.mock_provider import MockAIAnalysisProvider

    with tempfile.TemporaryDirectory() as tmpdir:
        html = Path(tmpdir) / "index.html"
        html.write_text(
            "<!DOCTYPE html><html><body>ScriptWeaver</body></html>"
        )
        app = create_app(
            MockAIAnalysisProvider(), static_dir=tmpdir,
        )
        client = TestClient(app)

        r = client.get("/")
        assert r.status_code == 200
        assert "ScriptWeaver" in r.text

        r2 = client.get("/index.html")
        assert r2.status_code == 200


def test_create_app_without_static_dir_still_works():
    """When static_dir is None, the app must still start (no / route)."""
    from scriptweaver.api.app import create_app
    from scriptweaver.ai.mock_provider import MockAIAnalysisProvider

    app = create_app(MockAIAnalysisProvider())
    client = TestClient(app)
    assert client.get("/health").status_code == 200


# ── run.py configuration ───────────────────────────────────────────


def test_run_py_configures_mock_provider_by_default(monkeypatch):
    """run.py must create an app instance with mock providers."""
    monkeypatch.delenv("SW_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("SW_API_KEY", raising=False)

    import runpy
    import sys

    # Prevent uvicorn.run from actually starting
    monkeypatch.setattr("uvicorn.run", lambda *a, **kw: None)

    ns = runpy.run_path(
        str(Path(__file__).parent.parent / "run.py"),
    )
    app = ns.get("app")
    assert app is not None
    assert isinstance(app, FastAPI)


def test_run_py_create_app_has_static_dir(monkeypatch):
    """run.py's create_app call must include a static_dir kwarg."""
    monkeypatch.delenv("SW_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("SW_API_KEY", raising=False)

    # Check that run.py source mentions static_dir
    src = (Path(__file__).parent.parent / "run.py").read_text()
    assert "static_dir" in src, (
        "run.py must pass static_dir to create_app"
    )
