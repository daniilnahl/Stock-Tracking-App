"""Fresh source processes prove the service boundary and SQLite restart."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_source_service_isolation_and_restart(tmp_path):
    for mode in ("isolation", "write", "read"):
        if mode == "read":
            (tmp_path / "opaque.pkl").write_bytes(b"opaque synthetic legacy; never deserialize")
            before = (tmp_path / "service.sqlite3").read_bytes()
        result = subprocess.run(
            [sys.executable, "-I", str(ROOT / "tests/watchlist_service_probe.py"), str(ROOT / "src"), mode],
            cwd=tmp_path, capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout == result.stderr == ""
        if mode == "isolation":
            assert not (tmp_path / "service.sqlite3").exists()
            assert not (tmp_path / "service-probe").exists()
        if mode == "read":
            assert (tmp_path / "service.sqlite3").read_bytes() == before
            assert (tmp_path / "opaque.pkl").read_bytes() == b"opaque synthetic legacy; never deserialize"
