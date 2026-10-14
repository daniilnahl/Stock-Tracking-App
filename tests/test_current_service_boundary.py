"""Source subprocess verifies cold current-service imports and actual behavior."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_source_current_service_boundary(tmp_path):
    result = subprocess.run(
        [sys.executable, "-I", str(ROOT / "tests/current_data_service_probe.py"), str(ROOT / "src")],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
    assert not (tmp_path / "current-service-probe").exists()
