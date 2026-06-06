import pytest
from fastapi.testclient import TestClient

from scriptweaver.api.app import create_app
from scriptweaver.ai.mock_provider import (
    MockAIAnalysisProvider,
    MockPlanProvider,
    MockScreenplayProvider,
)


@pytest.fixture
def client():
    app = create_app(
        MockAIAnalysisProvider(),
        plan_provider=MockPlanProvider(),
        screenplay_provider=MockScreenplayProvider(),
    )
    return TestClient(app)


# ── Health ───────────────────────────────────────────────────────


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ── Create job ───────────────────────────────────────────────────


def test_create_job(client):
    response = client.post("/jobs", json={"job_id": "job-001"})

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "job-001"
    assert data["state"] == "created"


def test_create_job_rejects_duplicate_id(client):
    client.post("/jobs", json={"job_id": "dup"})

    response = client.post("/jobs", json={"job_id": "dup"})

    assert response.status_code == 409


# ── Attach chapters ──────────────────────────────────────────────


def test_attach_chapters(client):
    client.post("/jobs", json={"job_id": "job-001"})

    response = client.post(
        "/jobs/job-001/chapters",
        json={
            "chapters": [
                {
                    "index": 1,
                    "title": "第一章",
                    "content": "林照收到密信。",
                },
                {
                    "index": 2,
                    "title": "第二章",
                    "content": "沈微阻止公开。",
                },
            ]
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "chapters_uploaded"
    assert len(data["chapters"]) == 2


def test_attach_chapters_rejects_empty_list(client):
    client.post("/jobs", json={"job_id": "job-001"})

    response = client.post(
        "/jobs/job-001/chapters",
        json={"chapters": []},
    )

    assert response.status_code == 400


def test_attach_chapters_requires_existing_job(client):
    response = client.post(
        "/jobs/nonexistent/chapters",
        json={
            "chapters": [
                {"index": 1, "title": "X", "content": "Y"}
            ]
        },
    )

    assert response.status_code == 404


# ── Generate analysis ────────────────────────────────────────────


def test_analyze(client):
    client.post("/jobs", json={"job_id": "job-001"})
    client.post(
        "/jobs/job-001/chapters",
        json={
            "chapters": [
                {"index": 1, "title": "第一章", "content": "密信。"},
            ]
        },
    )

    response = client.post("/jobs/job-001/analyze")

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "analysis_generated"
    assert data["ai_analysis"] is not None


def test_analyze_rejects_wrong_state(client):
    client.post("/jobs", json={"job_id": "job-001"})

    response = client.post("/jobs/job-001/analyze")

    assert response.status_code == 409


# ── Confirm analysis ─────────────────────────────────────────────


def test_confirm_analysis(client):
    client.post("/jobs", json={"job_id": "job-001"})
    client.post(
        "/jobs/job-001/chapters",
        json={
            "chapters": [
                {"index": 1, "title": "第一章", "content": "密信。"},
            ]
        },
    )
    client.post("/jobs/job-001/analyze")

    response = client.post("/jobs/job-001/confirm-analysis")

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "analysis_confirmed"


# ── Next uncertainty ─────────────────────────────────────────────


def test_next_uncertainty(client):
    _bootstrap_to_analysis_generated(client)

    response = client.get("/jobs/job-001/next-uncertainty")

    assert response.status_code == 200
    data = response.json()
    assert data is not None
    assert data["id"] == "uncertainty_001"


def test_next_uncertainty_returns_null_when_all_resolved(client):
    _bootstrap_to_analysis_generated(client)
    client.post(
        "/jobs/job-001/uncertainty-answer",
        json={
            "uncertainty_id": "uncertainty_001",
            "selected_option_id": "option_001",
        },
    )

    response = client.get("/jobs/job-001/next-uncertainty")

    assert response.status_code == 200
    assert response.json() is None


# ── Uncertainty answer ───────────────────────────────────────────


def test_submit_uncertainty_answer(client):
    _bootstrap_to_analysis_generated(client)

    response = client.post(
        "/jobs/job-001/uncertainty-answer",
        json={
            "uncertainty_id": "uncertainty_001",
            "selected_option_id": "option_001",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_confirmations"] is not None
    resolutions = data["user_confirmations"]["uncertainty_resolutions"]
    assert len(resolutions) == 1


def test_submit_answer_rejects_invalid_option(client):
    _bootstrap_to_analysis_generated(client)

    response = client.post(
        "/jobs/job-001/uncertainty-answer",
        json={
            "uncertainty_id": "uncertainty_001",
            "selected_option_id": "nonexistent",
        },
    )

    assert response.status_code == 400


# ── Generate plan ────────────────────────────────────────────────


def test_generate_plan(client):
    _bootstrap_to_analysis_confirmed(client)

    response = client.post("/jobs/job-001/generate-plan")

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "plan_generated"
    assert data["adaptation_plan"] is not None


def test_generate_plan_rejects_wrong_state(client):
    client.post("/jobs", json={"job_id": "job-001"})

    response = client.post("/jobs/job-001/generate-plan")

    assert response.status_code == 409


# ── Confirm plan ─────────────────────────────────────────────────


def test_confirm_plan(client):
    _bootstrap_to_plan_generated(client)

    response = client.post(
        "/jobs/job-001/confirm-plan",
        json={
            "target_format": "short_drama",
            "structure": "3 scenes",
            "scenes": [],
            "review_questions": [],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "plan_confirmed"


# ── Generate screenplay ──────────────────────────────────────────────


def test_generate_screenplay(client):
    """API must support advancing from plan_confirmed to screenplay_generated."""
    _bootstrap_to_plan_confirmed(client)

    response = client.post("/jobs/job-001/generate-screenplay")

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "screenplay_generated"
    screenplay = data["screenplay_draft"]
    assert screenplay is not None
    assert len(screenplay["scenes"]) >= 1


def test_generate_screenplay_rejects_wrong_state(client):
    """Cannot generate screenplay before plan is confirmed."""
    client.post("/jobs", json={"job_id": "job-001"})

    response = client.post("/jobs/job-001/generate-screenplay")

    assert response.status_code == 409


# ── Export YAML ────────────────────────────────────────────────────


def test_export_yaml_returns_yaml_content(client):
    """GET /jobs/{id}/export-yaml must return valid YAML."""
    _bootstrap_to_screenplay_generated(client)

    response = client.get("/jobs/job-001/export-yaml")

    assert response.status_code == 200
    import yaml

    parsed = yaml.safe_load(response.text)
    assert parsed["schema_version"] == "1.0"
    assert parsed["source"] is not None
    assert "scenes" in parsed["screenplay"]


def test_export_yaml_accepts_metadata_query_params(client):
    """Query params must be embedded in exported YAML metadata."""
    _bootstrap_to_screenplay_generated(client)

    params = {
        "title": "测试标题",
        "author": "测试作者",
        "adapter": "AI",
        "target_format": "short_drama",
        "language": "zh-CN",
    }
    response = client.get("/jobs/job-001/export-yaml", params=params)

    assert response.status_code == 200
    import yaml

    parsed = yaml.safe_load(response.text)
    assert parsed["metadata"]["title"] == "测试标题"
    assert parsed["metadata"]["author"] == "测试作者"


def test_export_yaml_returns_404_for_unknown_job(client):
    """Export must return 404 for non-existent job."""
    response = client.get("/jobs/nonexistent/export-yaml")
    assert response.status_code == 404


# ── Get job ──────────────────────────────────────────────────────


def test_get_job(client):
    client.post("/jobs", json={"job_id": "job-001"})

    response = client.get("/jobs/job-001")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "job-001"
    assert data["state"] == "created"


def test_get_job_returns_404_for_unknown(client):
    response = client.get("/jobs/nonexistent")
    assert response.status_code == 404


# ── Nested field validation: must return 400, not 500 ────────────


def test_confirm_plan_missing_scene_order(client):
    """Missing ScenePlan.scene_order must return 400, not 500."""
    _bootstrap_to_analysis_confirmed(client)
    client.post("/jobs/job-001/generate-plan")

    response = client.post(
        "/jobs/job-001/confirm-plan",
        json={
            "target_format": "short",
            "structure": "x",
            "scenes": [{"id": "s1"}],  # missing scene_order, title, dramatic_purpose
            "review_questions": [],
        },
    )

    assert response.status_code == 400


def test_confirm_plan_missing_decision_id(client):
    """Missing AdaptationDecision.id must return 400, not 500."""
    _bootstrap_to_analysis_confirmed(client)
    client.post("/jobs/job-001/generate-plan")

    response = client.post(
        "/jobs/job-001/confirm-plan",
        json={
            "target_format": "short",
            "structure": "x",
            "scenes": [
                {
                    "id": "s1",
                    "scene_order": 1,
                    "title": "Scene 1",
                    "dramatic_purpose": "purpose",
                    "compression_choices": [
                        {"description": "desc", "reason": "reason"}  # missing id
                    ],
                }
            ],
            "review_questions": [],
        },
    )

    assert response.status_code == 400


# ── Error recovery: job not mutated on error ─────────────────────


def test_job_state_preserved_after_error(client):
    _bootstrap_to_analysis_generated(client)

    # Try invalid confirm — should be rejected
    response = client.post("/jobs/job-001/analyze")
    assert response.status_code == 409

    # Job should still be in ANALYSIS_GENERATED
    response = client.get("/jobs/job-001")
    assert response.json()["state"] == "analysis_generated"


# ── Helpers ──────────────────────────────────────────────────────


def _bootstrap_to_analysis_generated(client):
    client.post("/jobs", json={"job_id": "job-001"})
    client.post(
        "/jobs/job-001/chapters",
        json={
            "chapters": [
                {"index": 1, "title": "第一章", "content": "密信。"},
            ]
        },
    )
    client.post("/jobs/job-001/analyze")


def _bootstrap_to_analysis_confirmed(client):
    _bootstrap_to_analysis_generated(client)
    client.post("/jobs/job-001/confirm-analysis")


def _bootstrap_to_plan_generated(client):
    _bootstrap_to_analysis_confirmed(client)
    client.post("/jobs/job-001/generate-plan")


def _bootstrap_to_plan_confirmed(client):
    _bootstrap_to_plan_generated(client)
    client.post(
        "/jobs/job-001/confirm-plan",
        json={
            "target_format": "short",
            "structure": "1 scene",
            "scenes": [
                {
                    "id": "scene_001",
                    "scene_order": 1,
                    "title": "Scene 1",
                    "dramatic_purpose": "purpose",
                    "character_ids": ["char_001"],
                    "source_chapter_indexes": [1],
                }
            ],
            "review_questions": [],
        },
    )


def _bootstrap_to_screenplay_generated(client):
    _bootstrap_to_plan_confirmed(client)
    client.post("/jobs/job-001/generate-screenplay")
