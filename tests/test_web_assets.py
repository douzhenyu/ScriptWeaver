"""Verify web frontend assets exist and are well-formed."""

from pathlib import Path


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
