from dataclasses import replace

import pytest
import yaml

from scriptweaver.ai.mock_provider import (
    MockAIAnalysisProvider,
    MockPlanProvider,
)
from scriptweaver.domain.models import (
    AIAnalysis,
    AdaptationPlan,
    Beat,
    Chapter,
    SceneHeading,
    ScenePlan,
    ScreenplayDraft,
    ScreenplayScene,
    UncertaintyResolution,
    UserConfirmations,
)
from scriptweaver.domain.workflow import AdaptationState
from scriptweaver.export.yaml_exporter import export_job_to_yaml
from scriptweaver.services.adaptation_service import AdaptationService


def make_chapters() -> list[Chapter]:
    return [
        Chapter(index=1, title="第一章", content="林照收到父亲留下的密信。"),
        Chapter(index=2, title="第二章", content="沈微出现并阻止林照公开密信。"),
    ]


def make_metadata() -> dict:
    return {
        "title": "密信",
        "author": "测试作者",
        "adapter": "ScriptWeaver AI",
        "target_format": "short_drama",
        "language": "zh-CN",
        "created_at": "2026-06-07T10:00:00",
    }


def make_full_job():
    """Build a job with all fields populated, simulating full workflow."""
    service = AdaptationService(
        MockAIAnalysisProvider(),
        plan_provider=MockPlanProvider(),
    )
    job = service.create_job("job-001")
    job = service.attach_chapters(job, make_chapters())
    job = service.generate_analysis(job)
    job = service.submit_uncertainty_answer(
        job,
        UncertaintyResolution(
            uncertainty_id="uncertainty_001",
            selected_option_id="option_001",
        ),
    )
    job = service.confirm_analysis(job)
    job = service.generate_plan(job)
    job = service.confirm_plan(job, job.adaptation_plan)
    # Manually add screenplay_draft in SCREENPLAY_GENERATED state
    job = replace(
        job,
        state=AdaptationState.SCREENPLAY_GENERATED,
        screenplay_draft=ScreenplayDraft(
            scenes=[
                ScreenplayScene(
                    id="scene_001",
                    heading=SceneHeading(
                        location="茶馆", time="夜", interior_exterior="INT"
                    ),
                    beats=[
                        Beat(type="action", text="开场动作。"),
                    ],
                ),
                ScreenplayScene(
                    id="scene_002",
                    heading=SceneHeading(
                        location="街道", time="日", interior_exterior="EXT"
                    ),
                    beats=[
                        Beat(type="action", text="过渡动作。"),
                    ],
                ),
            ],
            revision_notes=[
                "场景 1 需要审查节奏。",
                "场景 2 对话需要润色。",
            ],
        ),
    )
    return job


# ── Top-level structure ──────────────────────────────────────────


def test_export_produces_valid_yaml():
    job = make_full_job()
    metadata = make_metadata()

    yaml_str = export_job_to_yaml(job, metadata)
    parsed = yaml.safe_load(yaml_str)

    assert isinstance(parsed, dict)
    assert parsed["schema_version"] == "1.0"


def test_export_includes_all_top_level_keys():
    job = make_full_job()
    metadata = make_metadata()

    yaml_str = export_job_to_yaml(job, metadata)
    parsed = yaml.safe_load(yaml_str)

    expected_keys = {
        "schema_version",
        "metadata",
        "source",
        "ai_analysis",
        "confirmed_analysis",
        "user_confirmations",
        "adaptation_plan",
        "screenplay",
        "revision_notes",
    }
    assert set(parsed.keys()) == expected_keys


# ── schema_version ───────────────────────────────────────────────


def test_export_sets_schema_version():
    yaml_str = export_job_to_yaml(make_full_job(), make_metadata())
    parsed = yaml.safe_load(yaml_str)
    assert parsed["schema_version"] == "1.0"


# ── metadata ─────────────────────────────────────────────────────


def test_export_includes_metadata_fields():
    yaml_str = export_job_to_yaml(make_full_job(), make_metadata())
    parsed = yaml.safe_load(yaml_str)

    assert parsed["metadata"]["title"] == "密信"
    assert parsed["metadata"]["author"] == "测试作者"
    assert parsed["metadata"]["target_format"] == "short_drama"
    assert parsed["metadata"]["language"] == "zh-CN"


# ── source ───────────────────────────────────────────────────────


def test_export_includes_source_chapters():
    yaml_str = export_job_to_yaml(make_full_job(), make_metadata())
    parsed = yaml.safe_load(yaml_str)

    assert parsed["source"]["source_type"] == "novel_chapters"
    assert parsed["source"]["chapter_count"] == 2
    assert len(parsed["source"]["chapters"]) == 2
    assert parsed["source"]["chapters"][0]["index"] == 1
    assert parsed["source"]["chapters"][0]["title"] == "第一章"


# ── ai_analysis ──────────────────────────────────────────────────


def test_export_includes_ai_analysis():
    yaml_str = export_job_to_yaml(make_full_job(), make_metadata())
    parsed = yaml.safe_load(yaml_str)
    analysis = parsed["ai_analysis"]

    for key in (
        "characters", "relationships", "key_events", "conflicts",
        "themes", "candidate_scenes", "uncertainties",
    ):
        assert key in analysis


def test_export_ai_analysis_serializes_nested_models():
    yaml_str = export_job_to_yaml(make_full_job(), make_metadata())
    parsed = yaml.safe_load(yaml_str)

    characters = parsed["ai_analysis"]["characters"]
    assert len(characters) == 2
    assert characters[0]["id"] == "char_001"
    assert characters[0]["name"] == "主角"


# ── confirmed_analysis ───────────────────────────────────────────


def test_export_includes_confirmed_analysis():
    yaml_str = export_job_to_yaml(make_full_job(), make_metadata())
    parsed = yaml.safe_load(yaml_str)
    assert "characters" in parsed["confirmed_analysis"]


# ── adaptation_plan ──────────────────────────────────────────────


def test_export_includes_adaptation_plan():
    yaml_str = export_job_to_yaml(make_full_job(), make_metadata())
    parsed = yaml.safe_load(yaml_str)

    plan = parsed["adaptation_plan"]
    assert plan["target_format"] is not None
    assert len(plan["scenes"]) == 2
    assert plan["scenes"][0]["id"] == "scene_001"


# ── screenplay ───────────────────────────────────────────────────


def test_export_includes_screenplay_draft():
    yaml_str = export_job_to_yaml(make_full_job(), make_metadata())
    parsed = yaml.safe_load(yaml_str)

    screenplay = parsed["screenplay"]
    assert "scenes" in screenplay
    assert len(screenplay["scenes"]) == 2
    # Verify nested structure
    first_scene = screenplay["scenes"][0]
    assert first_scene["id"] == "scene_001"
    assert first_scene["heading"]["location"] == "茶馆"
    assert len(first_scene["beats"]) == 1


# ── revision_notes ───────────────────────────────────────────────


def test_export_includes_revision_notes():
    yaml_str = export_job_to_yaml(make_full_job(), make_metadata())
    parsed = yaml.safe_load(yaml_str)

    assert isinstance(parsed["revision_notes"], list)
    assert len(parsed["revision_notes"]) == 2


# ── Null safety ──────────────────────────────────────────────────


def test_export_handles_null_fields():
    service = AdaptationService(MockAIAnalysisProvider())
    job = service.create_job("minimal")
    job = service.attach_chapters(job, make_chapters())
    job = service.generate_analysis(job)

    yaml_str = export_job_to_yaml(job, make_metadata())
    parsed = yaml.safe_load(yaml_str)

    assert parsed["confirmed_analysis"] is None
    assert parsed["adaptation_plan"] is None
    assert parsed["screenplay"] is None
    assert parsed["revision_notes"] == []


# ── YAML is readable ─────────────────────────────────────────────


def test_export_yaml_is_multiline_and_readable():
    yaml_str = export_job_to_yaml(make_full_job(), make_metadata())

    assert "\n" in yaml_str
    assert "schema_version" in yaml_str
    assert "!!" not in yaml_str
