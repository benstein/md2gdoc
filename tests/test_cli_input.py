"""CLI input validation tests for md2gdoc."""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "md2gdoc.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def test_directory_input_reports_directory(tmp_path: Path) -> None:
    proc = _run(str(tmp_path))
    assert proc.returncode != 0
    assert "is a directory" in proc.stderr


def test_missing_file_reports_not_found(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.md"
    proc = _run(str(missing))
    assert proc.returncode != 0
    assert "File not found" in proc.stderr
