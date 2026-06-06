"""Tests for the default app entrypoint."""

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
