"""M4 combined exit evidence from independent source processes."""

from pathlib import Path
import subprocess
import sys


def test_source_history_exit_transport_cache_restore_chart_cli(tmp_path):
    root = Path(__file__).resolve().parents[1]
    for mode in ("write", "read", "expired"):
        result = subprocess.run(
            [sys.executable, "-I", str(root / "tests/history_exit_probe.py"), str(root / "src"), mode],
            cwd=tmp_path, capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout == result.stderr == ""
    assert (tmp_path / "watchlist.pkl").read_bytes() == b"opaque synthetic legacy; do not deserialize"
