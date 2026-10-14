"""Combined M6 audit executes actual source commands in independent processes."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_source_m6_combined_exit(tmp_path):
    for mode in ("write", "read", "failures", "read"):
        result = subprocess.run(
            [sys.executable, "-I", "-B", str(ROOT / "tests/m6_exit_probe.py"), str(ROOT / "src"), mode],
            cwd=tmp_path, capture_output=True, text=True, timeout=45,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout == result.stderr == ""
