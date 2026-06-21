"""Verify web frontend assets exist and are well-formed."""

import re
from pathlib import Path


def _index_html() -> str:
    return (
        Path(__file__).parent.parent
        / "scriptweaver"
        / "web"
        / "index.html"
    ).read_text()


def _function_body(content: str, name: str) -> str:
    match = re.search(
        rf"(?:async\s+)?function\s+{re.escape(name)}\s*\([^)]*\)\s*\{{"
        rf"(?P<body>.*?)(?=\n(?:async\s+)?function\s+\w+\s*\(|\Z)",
        content,
        re.DOTALL,
    )
    assert match, f"Missing JavaScript function: {name}"
    return match.group("body")


def test_index_html_exists_and_non_empty():
    html_path = Path(__file__).parent.parent / "scriptweaver" / "web" / "index.html"
    assert html_path.exists(), "index.html must exist"
    content = html_path.read_text()
    assert len(content) > 500, "index.html must be non-trivial"
    assert "<!DOCTYPE html>" in content
    assert "</html>" in content


def test_index_html_contains_key_elements():
    html_path = Path(__file__).parent.parent / "scriptweaver" / "web" / "index.html"
    content = html_path.read_text()

    # Must have workflow step containers
    for step in (
        "create-job",
        "upload-chapters",
        "analysis-result",
        "uncertainty-qa",
        "plan-result",
        "screenplay-result",
        "export-section",
    ):
        assert step in content, f"Missing element: {step}"


def test_index_html_has_api_config():
    html_path = Path(__file__).parent.parent / "scriptweaver" / "web" / "index.html"
    content = html_path.read_text()

    # Must reference an API base URL configuration
    assert "API_BASE" in content or "apiBase" in content or "127.0.0.1" in content


def test_plan_ui_builds_author_friendly_source_lookups():
    content = _index_html()
    lookup_body = _function_body(content, "hydrateSourceLookups")
    assert "chapterTitles" in lookup_body
    assert "eventSummaries" in lookup_body
    assert "来源事件未命名" in lookup_body

    hydration_call = re.compile(r"hydrateSourceLookups\s*\(\s*job\s*\)")
    for function_name in ("resumeJob", "doAnalyze", "confirmAnalysis"):
        function_body = _function_body(content, function_name)
        assert hydration_call.search(function_body), (
            f"{function_name} must hydrate source lookups after fetching the job"
        )


def test_plan_ui_renders_all_ai_decision_types():
    content = _index_html()
    render_body = _function_body(content, "renderSceneDecisions")
    for field in (
        "compression_choices",
        "merge_choices",
        "rewrite_choices",
    ):
        assert re.search(rf"scene\s*\.\s*{field}\b", render_body), (
            f"renderSceneDecisions must render scene.{field}"
        )
    for label in ("压缩", "合并", "改写", "AI 改编决策"):
        assert label in render_body, (
            f"renderSceneDecisions must include the {label!r} label"
        )

    refresh_body = _function_body(content, "refreshPlanUI")
    assert re.search(r"renderSceneDecisions\s*\(\s*s\s*\)", refresh_body), (
        "refreshPlanUI must render AI decisions for each scene"
    )


def test_plan_ui_escapes_ai_decision_content():
    render_body = _function_body(_index_html(), "renderSceneDecisions")
    for field in ("description", "reason"):
        assert re.search(
            rf"escapeHtml\s*\(\s*d\s*\.\s*{field}\s*\|\|\s*(['\"])\1\s*\)",
            render_body,
        ), f"renderSceneDecisions must escape decision {field} content"
    assert re.search(
        r"escapeHtml\s*\(\s*eventSummary\s*\(\s*id\s*\)\s*\)",
        render_body,
    ), "renderSceneDecisions must escape source event summaries"


def test_confirm_plan_preserves_ai_decision_fields():
    confirm_body = _function_body(_index_html(), "confirmPlan")
    for field in (
        "compression_choices",
        "merge_choices",
        "rewrite_choices",
        "source_candidate_scene_ids",
        "retained_event_ids",
    ):
        assert re.search(
            rf"['\"]?{field}['\"]?\s*:\s*s\s*\.\s*{field}"
            rf"\s*\|\|\s*\[\s*\]",
            confirm_body,
        ), f"confirmPlan must preserve scene.{field}"
