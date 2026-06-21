"""Verify web frontend assets exist and are well-formed."""

from pathlib import Path


def _index_html() -> str:
    return (
        Path(__file__).parent.parent
        / "scriptweaver"
        / "web"
        / "index.html"
    ).read_text()


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
    assert "function hydrateSourceLookups(job)" in content
    assert "chapterTitles" in content
    assert "eventSummaries" in content
    assert "来源事件未命名" in content


def test_plan_ui_renders_all_ai_decision_types():
    content = _index_html()
    for field in (
        "compression_choices",
        "merge_choices",
        "rewrite_choices",
    ):
        assert field in content
    for label in ("压缩", "合并", "改写", "AI 改编决策"):
        assert label in content


def test_plan_ui_escapes_ai_decision_content():
    content = _index_html()
    assert "escapeHtml(d.description||'')" in content
    assert "escapeHtml(d.reason||'')" in content
    assert "escapeHtml(eventSummary(id))" in content


def test_confirm_plan_preserves_ai_decision_fields():
    content = _index_html()
    assert "compression_choices:s.compression_choices||[]" in content
    assert "merge_choices:s.merge_choices||[]" in content
    assert "rewrite_choices:s.rewrite_choices||[]" in content
    assert "source_candidate_scene_ids:s.source_candidate_scene_ids||[]" in content
    assert "retained_event_ids:s.retained_event_ids||[]" in content
