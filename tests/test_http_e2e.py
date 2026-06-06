"""End-to-end acceptance tests using only the HTTP API."""

import yaml
import pytest
from fastapi.testclient import TestClient

from scriptweaver.ai.mock_provider import (
    MockAIAnalysisProvider,
    MockPlanProvider,
    MockScreenplayProvider,
)
from scriptweaver.api.app import create_app


@pytest.fixture
def client():
    app = create_app(
        MockAIAnalysisProvider(),
        plan_provider=MockPlanProvider(),
        screenplay_provider=MockScreenplayProvider(),
    )
    return TestClient(app)


def test_full_workflow_via_http_with_three_chapters(client):
    """Walk the complete 9-stage workflow using only HTTP calls."""

    # ── Stage 1: Create job ──────────────────────────────────
    r = client.post("/jobs", json={"job_id": "http-e2e-001"})
    assert r.status_code == 201
    assert r.json()["state"] == "created"

    # ── Stage 2: Attach 3 chapters ───────────────────────────
    r = client.post(
        "/jobs/http-e2e-001/chapters",
        json={
            "chapters": [
                {
                    "index": 1,
                    "title": "第一章",
                    "content": "林照收到父亲留下的密信。",
                },
                {
                    "index": 2,
                    "title": "第二章",
                    "content": "沈微出现并阻止林照公开密信。",
                },
                {
                    "index": 3,
                    "title": "第三章",
                    "content": "两人发现密信指向旧案。",
                },
            ]
        },
    )
    assert r.status_code == 200
    assert r.json()["state"] == "chapters_uploaded"
    assert len(r.json()["chapters"]) == 3

    # ── Stage 3: Generate AI analysis ────────────────────────
    r = client.post("/jobs/http-e2e-001/analyze")
    assert r.status_code == 200
    assert r.json()["state"] == "analysis_generated"
    analysis = r.json()["ai_analysis"]
    assert analysis is not None
    assert len(analysis["characters"]) == 2
    assert len(analysis["uncertainties"]) == 1

    # ── Stage 4: Answer uncertainty ──────────────────────────
    r = client.get("/jobs/http-e2e-001/next-uncertainty")
    assert r.status_code == 200
    uncertainty = r.json()
    assert uncertainty["id"] == "uncertainty_001"

    r = client.post(
        "/jobs/http-e2e-001/uncertainty-answer",
        json={
            "uncertainty_id": "uncertainty_001",
            "selected_option_id": "option_001",
        },
    )
    assert r.status_code == 200
    confirmations = r.json()["user_confirmations"]
    assert len(confirmations["uncertainty_resolutions"]) == 1

    # All answered
    r = client.get("/jobs/http-e2e-001/next-uncertainty")
    assert r.json() is None

    # ── Stage 5: Confirm analysis ────────────────────────────
    r = client.post("/jobs/http-e2e-001/confirm-analysis")
    assert r.status_code == 200
    assert r.json()["state"] == "analysis_confirmed"
    assert r.json()["confirmed_analysis"] is not None

    # ── Stage 6: Generate adaptation plan ────────────────────
    r = client.post("/jobs/http-e2e-001/generate-plan")
    assert r.status_code == 200
    assert r.json()["state"] == "plan_generated"
    plan = r.json()["adaptation_plan"]
    assert plan is not None
    assert len(plan["scenes"]) == 3

    # ── Stage 7: Confirm plan ────────────────────────────────
    r = client.post(
        "/jobs/http-e2e-001/confirm-plan",
        json={
            "target_format": "short_drama",
            "structure": "3 scenes",
            "scenes": [
                {
                    "id": "scene_001",
                    "scene_order": 1,
                    "title": "Scene 1",
                    "dramatic_purpose": "purpose",
                    "character_ids": ["char_001"],
                    "source_chapter_indexes": [1],
                },
                {
                    "id": "scene_002",
                    "scene_order": 2,
                    "title": "Scene 2",
                    "dramatic_purpose": "purpose",
                    "character_ids": ["char_001"],
                    "source_chapter_indexes": [2],
                },
                {
                    "id": "scene_003",
                    "scene_order": 3,
                    "title": "Scene 3",
                    "dramatic_purpose": "purpose",
                    "character_ids": ["char_001"],
                    "source_chapter_indexes": [3],
                },
            ],
            "review_questions": [],
        },
    )
    assert r.status_code == 200
    assert r.json()["state"] == "plan_confirmed"

    # ── Stage 8: Generate screenplay ─────────────────────────
    r = client.post("/jobs/http-e2e-001/generate-screenplay")
    assert r.status_code == 200
    assert r.json()["state"] == "screenplay_generated"
    screenplay = r.json()["screenplay_draft"]
    assert screenplay is not None
    assert len(screenplay["scenes"]) == 3
    # Each scene must have beats
    for scene in screenplay["scenes"]:
        assert len(scene["beats"]) >= 2

    # ── Stage 9: Export YAML ─────────────────────────────────
    r = client.get(
        "/jobs/http-e2e-001/export-yaml",
        params={
            "title": "密信",
            "author": "测试作者",
            "adapter": "ScriptWeaver AI",
            "target_format": "short_drama",
            "language": "zh-CN",
        },
    )
    assert r.status_code == 200
    parsed = yaml.safe_load(r.text)

    assert parsed["schema_version"] == "1.0"
    assert parsed["metadata"]["title"] == "密信"
    assert parsed["source"]["chapter_count"] == 3
    assert len(parsed["source"]["chapters"]) == 3
    assert len(parsed["ai_analysis"]["characters"]) == 2
    assert parsed["confirmed_analysis"] is not None
    assert len(parsed["adaptation_plan"]["scenes"]) == 3
    assert len(parsed["screenplay"]["scenes"]) == 3
    assert len(parsed["revision_notes"]) == 3


def test_full_workflow_data_integrity(client):
    """Verify GET /jobs/{id} returns complete state at each stage."""
    # Setup through screenplay_generated
    client.post("/jobs", json={"job_id": "http-e2e-002"})
    client.post(
        "/jobs/http-e2e-002/chapters",
        json={
            "chapters": [
                {"index": 1, "title": "第一章", "content": "密信。"},
            ]
        },
    )
    client.post("/jobs/http-e2e-002/analyze")
    client.post("/jobs/http-e2e-002/confirm-analysis")
    client.post("/jobs/http-e2e-002/generate-plan")
    client.post(
        "/jobs/http-e2e-002/confirm-plan",
        json={
            "target_format": "short",
            "structure": "1 scene",
            "scenes": [
                {
                    "id": "scene_001",
                    "scene_order": 1,
                    "title": "S1",
                    "dramatic_purpose": "p",
                    "character_ids": ["char_001"],
                    "source_chapter_indexes": [1],
                }
            ],
            "review_questions": [],
        },
    )
    client.post("/jobs/http-e2e-002/generate-screenplay")

    # GET should return complete state
    r = client.get("/jobs/http-e2e-002")
    data = r.json()

    assert data["state"] == "screenplay_generated"
    assert data["ai_analysis"] is not None
    assert data["confirmed_analysis"] is not None
    assert data["adaptation_plan"] is not None
    assert data["screenplay_draft"] is not None
    assert len(data["chapters"]) == 1


def test_health_endpoint_accessible(client):
    """Health check must return 200."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
