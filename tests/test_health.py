from fastapi.testclient import TestClient

from scriptweaver.ai.mock_provider import MockAIAnalysisProvider
from scriptweaver.api.app import create_app


def test_health_endpoint_returns_ok():
    client = TestClient(create_app(MockAIAnalysisProvider()))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
