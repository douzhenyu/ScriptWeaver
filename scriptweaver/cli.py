from __future__ import annotations

import argparse
from collections.abc import Sequence

from scriptweaver import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scriptweaver",
        description="ScriptWeaver converts novel chapters into editable screenplay drafts.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"ScriptWeaver {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)
    return 0
