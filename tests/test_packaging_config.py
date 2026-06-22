"""Verify the distribution only discovers ScriptWeaver Python packages."""

import tomllib
from pathlib import Path


def test_setuptools_only_discovers_scriptweaver_packages():
    config = tomllib.loads(
        (Path(__file__).parent.parent / "pyproject.toml").read_text()
    )

    package_find = config["tool"]["setuptools"]["packages"]["find"]
    assert package_find["include"] == ["scriptweaver*"]
