"""Offline security regression checks; never print credential values."""

import ast
import importlib.util
import io
from pathlib import Path
import re
import subprocess
import tempfile
import tokenize
import unittest


ROOT = Path(__file__).resolve().parents[1]
KEY_NAMES = {"api_key", "apikey", "my_api_key", "token", "password", "secret"}


def credential_lines(text, python_source=False):
    """Return line numbers only for literal keys and credential-bearing URLs.

    This deliberately bounded check covers the exposed patterns in issue #4,
    not all possible secret formats. Empty values and dynamic API URLs are safe.
    """
    findings = set()
    for number, line in enumerate(text.splitlines(), 1):
        for match in re.finditer(r"(?i)[?&](?:api_?key|token|password)=([^\s\"'&#]+)", line):
            if not match.group(1).startswith("{"):
                findings.add(number)
        assignment = re.match(r"\s*(\w+)\s*=\s*(.*?)\s*$", line)
        if assignment and assignment.group(1).lower() in KEY_NAMES:
            value = assignment.group(2).strip("\"'")
            if value and not python_source:
                findings.add(number)

    if python_source:
        # Tokenize rather than parse: legacy modules have syntax errors, and
        # string fixtures describing Python code must not count as assignments.
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
        for index, token in enumerate(tokens):
            following = tokens[index + 1:index + 5]
            value = None
            if token.type == tokenize.NAME and token.string.lower() in KEY_NAMES:
                if len(following) >= 2 and following[0].string == "=" and following[1].type == tokenize.STRING:
                    value = following[1]
            if token.type == tokenize.NAME and token.string == "Stock" and len(following) == 4:
                if (following[0].string == "(" and following[1].type == tokenize.STRING
                        and following[2].string == "," and following[3].type == tokenize.STRING):
                    value = following[3]
            if value is not None and ast.literal_eval(value.string):
                findings.add(token.start[0])
    return sorted(findings)


def git(*args, cwd=ROOT, input=None):
    # Binary stdin prevents Windows from adding CR characters to Git path lists.
    result = subprocess.run(
        ["git", *args], cwd=cwd, input=input.encode("utf-8") if input is not None else None,
        capture_output=True, check=True,
    )
    return result.stdout.decode("utf-8")


class CredentialScannerTests(unittest.TestCase):
    def test_detects_synthetic_literal_patterns(self):
        dummy = "synthetic-dummy-not-a-real-key"
        cases = [
            ("Stock('AMD', " + repr(dummy) + ")", True),
            ("API_KEY = " + repr(dummy), True),
            ("Stock('AMD', API_KEY=" + repr(dummy) + ")", True),
            ("https://example.invalid/quote?" + "apikey=" + dummy, False),
            ("MY_API_KEY=" + dummy, False),
        ]
        for text, python_source in cases:
            # No assertion includes the source or dummy value in diagnostics.
            self.assertEqual(credential_lines(text, python_source), [1])

    def test_accepts_empty_template_and_dynamic_credentials(self):
        self.assertEqual(credential_lines("MY_API_KEY="), [])
        source = '\n'.join([
            'api_key = os.getenv("MY_API_KEY")',
            'Stock("AMD", api_key)',
            'url = f"https://example.invalid/quote?apikey={API_KEY}"',
        ])
        self.assertEqual(credential_lines(source, True), [])


class RepositoryHygieneTests(unittest.TestCase):
    def test_tracked_files_have_no_issue_4_credential_patterns(self):
        findings = []
        for name in git("ls-files", "-z").split("\0"):
            if not name:
                continue
            path = ROOT / name
            # Scan the index so an unstaged cleanup cannot hide a staged secret.
            content = git("show", f":{name}")
            for line in credential_lines(content, path.suffix == ".py"):
                findings.append(f"{name}:{line}: [REDACTED credential pattern]")
        self.assertEqual(findings, [], "\n".join(findings))

    def test_local_environment_is_untracked(self):
        self.assertEqual(git("ls-files", "--", ".env").strip(), "")

    def test_untracking_preserves_environment_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            git("init", "--quiet", cwd=directory)
            env = Path(directory) / ".env"
            original = b"MY_API_KEY=synthetic-dummy-not-a-real-key\r\n"
            env.write_bytes(original)
            git("add", "--", ".env", cwd=directory)
            git("rm", "--cached", "--", ".env", cwd=directory)
            self.assertTrue(env.read_bytes() == original, "Environment bytes changed")
            self.assertEqual(git("ls-files", "--", ".env", cwd=directory).strip(), "")

    def test_template_documents_existing_variable_without_a_key(self):
        lines = (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
        assignments = [line for line in lines if line and not line.startswith("#")]
        self.assertTrue(assignments == ["MY_API_KEY="], "Template must contain only an empty MY_API_KEY")

    def test_ignore_rules_in_isolated_git_repository(self):
        ignored = [
            ".env", ".env.local", ".env.production", "nested/.env",
            "watchlist.pkl", "daniils_stock_methodd.pkl",
            "__pycache__/stock.cpython-311.pyc", "stock.pyc", "stock.pyo",
            ".pytest_cache/state", ".ruff_cache/state", ".mypy_cache/state",
            ".coverage", ".coverage.local", "coverage.xml", "htmlcov/index.html",
            ".tox/state", ".nox/state", "build/state", "dist/package.whl",
            "app.egg-info/PKG-INFO", ".eggs/state", ".venv/state",
            "venv/state", "env/state",
        ]
        trackable = [".env.example", "tests/test_repository_hygiene.py", "test.py"]
        with tempfile.TemporaryDirectory() as directory:
            git("init", "--quiet", cwd=directory)
            (Path(directory) / ".gitignore").write_bytes((ROOT / ".gitignore").read_bytes())
            result = git("check-ignore", "--no-index", "--stdin", cwd=directory,
                         input="\n".join(ignored + trackable) + "\n")
            self.assertEqual(set(result.splitlines()), set(ignored))

    def test_scratch_import_does_not_load_credentials_or_call_provider(self):
        # These dependencies are deliberately unavailable during this import.
        from unittest.mock import patch

        spec = importlib.util.spec_from_file_location("developer_scratch", ROOT / "test.py")
        module = importlib.util.module_from_spec(spec)
        with patch.dict("sys.modules", {"stock": None, "dotenv": None}):
            spec.loader.exec_module(module)
        self.assertTrue(callable(module.main))


if __name__ == "__main__":
    unittest.main()
