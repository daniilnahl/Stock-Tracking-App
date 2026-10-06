"""Final source M3 combined transition and restored-CLI process audit."""

from pathlib import Path
import subprocess
import sys


def test_combined_source_import_backup_restore_restart(tmp_path):
    root = Path(__file__).resolve().parents[1]
    original, restored = tmp_path / "original", tmp_path / "restored"
    original.mkdir()
    restored.mkdir()
    legacy = {name: b"opaque fictional original; never deserialize" for name in (
        "watchlist.pkl", "daniils_stock_methodd.pkl")}
    for name, content in legacy.items():
        (original / name).write_bytes(content)
        (restored / name).write_bytes(content)
    for mode, directory in (("prepare", original), ("verify", original),
                            ("copy", original), ("verify", restored)):
        result = subprocess.run(
            [sys.executable, "-I", str(root / "tests" / "persistence_exit_probe.py"),
             str(root), str(root / "src"), mode, str(restored)],
            cwd=directory, capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout == result.stderr == ""
    for name, content in legacy.items():
        assert (original / name).read_bytes() == (restored / name).read_bytes() == content
