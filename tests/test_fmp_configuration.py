"""Exercise real environment/dotenv loading with isolated legacy dependencies."""

import os
import runpy
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ("menu_watchlist.py", "daniils_stock_method.py", "test.py")


class FMPConfigurationTests(unittest.TestCase):
    def load_key(self, script, environment, dotenv_text=""):
        """Run the actual script; replace only unrelated domain/persistence code.

        watch_list.py has a pre-existing syntax error (#6). These focused tests
        do not certify CLI importability or application behavior. dotenv still
        parses a real isolated file; no loader or environment lookup is mocked.
        """
        captured = []
        stock_module = ModuleType("stock")
        watch_module = ModuleType("watch_list")

        class FakeStock:
            def __init__(self, symbol, api_key):
                captured.append(api_key)

            def get_stock_info(self):
                pass

        stock_module.Stock = FakeStock
        watch_module.Watch_list = lambda name: object()
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            env_file = Path(directory) / ".env"
            env_file.write_text(dotenv_text, encoding="utf-8")
            stack.callback(os.chdir, os.getcwd())
            os.chdir(directory)
            stack.enter_context(patch.dict(os.environ, environment, clear=True))
            stack.enter_context(patch.dict("sys.modules", {
                "stock": stock_module, "watch_list": watch_module,
            }))
            stack.enter_context(patch(
                "dotenv.load_dotenv", side_effect=lambda: load_dotenv(env_file),
            ))
            stack.enter_context(patch("pickle.load", side_effect=AssertionError("User state accessed")))
            stack.enter_context(patch("urllib.request.urlopen", side_effect=AssertionError("Network accessed")))
            module = runpy.run_path(str(ROOT / script), run_name="configuration_test")
            if script == "test.py":
                module["main"]()
                return captured[0]
            return module["API_KEY"]

    def test_canonical_process_environment_is_loaded_by_every_script(self):
        for script in SCRIPTS:
            with self.subTest(script=script):
                self.assertEqual(self.load_key(script, {"FMP_API_KEY": "synthetic-canonical"}), "synthetic-canonical")

    def test_canonical_name_wins_over_legacy_name(self):
        for script in SCRIPTS:
            with self.subTest(script=script):
                self.assertEqual(self.load_key(script, {
                    "FMP_API_KEY": "synthetic-canonical", "MY_API_KEY": "synthetic-legacy",
                }), "synthetic-canonical")

    def test_canonical_dotenv_is_loaded_by_every_script(self):
        for script in SCRIPTS:
            with self.subTest(script=script):
                self.assertEqual(self.load_key(script, {}, "FMP_API_KEY=synthetic-file\n"), "synthetic-file")

    def test_process_environment_overrides_same_name_in_dotenv(self):
        for script in SCRIPTS:
            with self.subTest(script=script):
                self.assertEqual(self.load_key(script, {"FMP_API_KEY": "synthetic-process"},
                                              "FMP_API_KEY=synthetic-file\n"), "synthetic-process")

    def test_canonical_dotenv_wins_over_legacy_process_variable(self):
        for script in SCRIPTS:
            with self.subTest(script=script):
                self.assertEqual(self.load_key(script, {"MY_API_KEY": "synthetic-legacy"},
                                              "FMP_API_KEY=synthetic-file\n"), "synthetic-file")

    def test_legacy_fallback_is_preserved_when_canonical_name_is_absent(self):
        for script in SCRIPTS:
            with self.subTest(script=script):
                self.assertEqual(self.load_key(script, {"MY_API_KEY": "synthetic-legacy"}), "synthetic-legacy")
                self.assertEqual(self.load_key(script, {}, "MY_API_KEY=synthetic-file\n"), "synthetic-file")

    def test_missing_and_empty_canonical_keep_existing_failure_behavior(self):
        for environment in ({}, {"FMP_API_KEY": "", "MY_API_KEY": "synthetic-legacy"}):
            for script in SCRIPTS:
                with self.subTest(script=script, canonical_present="FMP_API_KEY" in environment):
                    if script == "test.py":
                        with self.assertRaisesRegex(SystemExit, "Set FMP_API_KEY"):
                            self.load_key(script, environment)
                    else:
                        self.assertEqual(self.load_key(script, environment), environment.get("FMP_API_KEY"))


if __name__ == "__main__":
    unittest.main()
