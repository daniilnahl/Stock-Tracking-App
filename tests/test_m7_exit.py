"""Fresh source-process M7 REST/service/provider/cache preservation audit."""

from pathlib import Path
import subprocess
import sys


def test_source_api_combined_exit(tmp_path):
    root = Path(__file__).resolve().parents[1]
    for mode in ("write", "read", "expired"):
        result = subprocess.run([sys.executable, "-I", "-B", str(root / "tests/m7_exit_probe.py"), str(root / "src"), mode],
                                cwd=tmp_path, capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, result.stderr
        assert result.stdout == result.stderr == ""
