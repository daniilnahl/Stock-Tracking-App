"""Combined source restart audit with child-owned domain isolation guards."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_snapshot_analytics_recomputes_after_exact_sqlite_restart(tmp_path):
    database = tmp_path / "holdings.sqlite3"
    original = None
    for mode in ("write", "read", "read"):
        result = subprocess.run(
            [sys.executable, "-I", str(ROOT / "tests/analytics_exit_probe.py"),
             str(ROOT / "src"), str(database), mode],
            cwd=tmp_path, capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout == result.stderr == ""
        if original is None:
            original = database.read_bytes()
        assert database.read_bytes() == original
    assert list(tmp_path.iterdir()) == [database]
