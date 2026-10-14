"""Independent process boundary evidence, separate from parent pytest guards."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_cold_source_api_foundation_boundary(tmp_path):
    result = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "tests/api_foundation_probe.py"), str(ROOT / "src")],
                            cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
    assert list(tmp_path.iterdir()) == []
