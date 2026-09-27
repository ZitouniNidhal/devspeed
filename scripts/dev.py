"""Cross-platform development task runner for devspeed.

Examples:
    python scripts/dev.py format
    python scripts/dev.py check
    python scripts/dev.py build
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "devspeed"
TESTS_DIR = ROOT / "tests"
BUILD_DIRS = (ROOT / "build", ROOT / "dist", ROOT / "devspeed.egg-info")


def run(command: Sequence[str], *, check: bool = True) -> int:
    """Run a repository command from the project root.

    Args:
        command: Executable and arguments to run.
        check: Raise ``SystemExit`` when the command fails.

    Returns:
        The subprocess return code.

    Raises:
        SystemExit: If ``check`` is true and the command fails.
        FileNotFoundError: If the executable cannot be found.
    """
    printable = " ".join(command)
    print(f"\n$ {printable}")
    completed = subprocess.run(list(command), cwd=ROOT, check=False)
    if check and completed.returncode != 0:
        raise SystemExit(completed.returncode)
    return completed.returncode


def python_module(module: str, *arguments: str) -> list[str]:
    """Build a command using the current Python interpreter.

    Args:
        module: Module passed to ``python -m``.
        arguments: Additional module arguments.

    Returns:
        A command suitable for :func:`run`.
    """
    return [sys.executable, "-m", module, *arguments]


def format_code() -> None:
    """Format all Python source and test files with Black."""
    run(python_module("black", "devspeed", "tests", "scripts"))


def check_format() -> None:
    """Verify that Black would not modify the repository."""
    run(python_module("black", "--check", "devspeed", "tests", "scripts"))


def lint() -> None:
    """Run Ruff over application, test, and development script code."""
    run(python_module("ruff", "check", "devspeed", "tests", "scripts"))


def typecheck() -> None:
    """Run mypy using the project's supported Python compatibility settings."""
    run(python_module("mypy", "devspeed", "--ignore-missing-imports"))


def test() -> None:
    """Run the complete unittest suite with verbose output."""
    run(python_module("unittest", "discover", "-s", "tests", "-v"))


def compile_package() -> None:
    """Compile package sources to catch syntax errors early."""
    run(python_module("compileall", "-q", "devspeed"))


def check() -> None:
    """Run all local quality gates in the same order as CI."""
    check_format()
    lint()
    typecheck()
    compile_package()
    test()


def build() -> None:
    """Build a source distribution and wheel using Python build."""
    if shutil.which("python") is None:
        raise SystemExit("Python executable not found")
    run(python_module("build"))


def clean() -> None:
    """Remove local build outputs and Python bytecode caches."""
    for path in BUILD_DIRS:
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            print(f"Removed {path}")
    for path in ROOT.rglob("__pycache__"):
        if path.is_dir():
            shutil.rmtree(path)
            print(f"Removed {path}")
    for path in ROOT.rglob("*.pyc"):
        if path.is_file():
            path.unlink()
            print(f"Removed {path}")


def build_parser() -> argparse.ArgumentParser:
    """Create the development task command-line parser."""
    parser = argparse.ArgumentParser(description="Run devspeed development tasks.")
    subparsers = parser.add_subparsers(dest="task", required=True)
    commands = {
        "format": (format_code, "Format Python source with Black"),
        "format-check": (check_format, "Verify Black formatting"),
        "lint": (lint, "Run Ruff"),
        "typecheck": (typecheck, "Run mypy"),
        "test": (test, "Run unittest discovery"),
        "compile": (compile_package, "Compile Python sources"),
        "check": (check, "Run all local quality gates"),
        "build": (build, "Build wheel and source distribution"),
        "clean": (clean, "Remove build and cache outputs"),
    }
    for name, (function, help_text) in commands.items():
        subparser = subparsers.add_parser(name, help=help_text)
        subparser.set_defaults(function=function)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:  # noqa: UP045
    """Run one development task.

    Args:
        argv: Optional argument list; defaults to command-line arguments.

    Returns:
        Zero after the selected task completes successfully.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    args.function()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
