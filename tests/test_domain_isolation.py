"""Prove isolated domain behavior in a fresh source-only process."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "domain_isolation_probe.py"


def test_source_domain_runs_with_independent_infrastructure_guards(tmp_path):
    result = subprocess.run(
        [sys.executable, "-I", str(PROBE), str(ROOT / "src")],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
    assert list(tmp_path.iterdir()) == []
