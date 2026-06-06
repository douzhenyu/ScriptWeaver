"""Tests for declared runtime dependencies."""

import tomllib  # Python 3.11+


def test_pyyaml_is_declared_in_dependencies():
    """pyyaml must be declared in pyproject.toml [project].dependencies."""
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)

    deps = data["project"]["dependencies"]
    pyyaml_dep = next((d for d in deps if d.startswith("pyyaml")), None)

    assert pyyaml_dep is not None, (
        "pyyaml must be declared in project.dependencies"
    )


def test_yaml_exporter_imports_and_exports():
    """The YAML exporter must be importable and produce valid YAML."""
    from scriptweaver.export.yaml_exporter import export_job_to_yaml
    from scriptweaver.domain.models import AdaptationJob

    job = AdaptationJob(id="dep-test")
    result = export_job_to_yaml(
        job,
        metadata={
            "title": "测试",
            "author": "测试作者",
            "adapter": "ScriptWeaver",
            "target_format": "short_drama",
            "language": "zh-CN",
            "created_at": "2026-06-07T10:00:00",
        },
    )

    assert result is not None
    assert "schema_version" in result
    assert "测试" in result
