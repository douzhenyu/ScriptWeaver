import subprocess
import sys

from scriptweaver.cli import main


def test_cli_help_prints_usage(capsys):
    exit_code = main(["--help"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "usage:" in captured.out
    assert "ScriptWeaver" in captured.out


def test_module_help_prints_usage():
    result = subprocess.run(
        [sys.executable, "-m", "scriptweaver", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage:" in result.stdout
    assert "ScriptWeaver" in result.stdout
