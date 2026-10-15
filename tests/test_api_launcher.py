"""Offline local launcher configuration and real shared-service composition."""

import asyncio
from datetime import date, datetime, timezone
import os
from pathlib import Path
import subprocess
import sys

import pytest

from stock_tracker.api.configuration import ApiConfiguration, ApiConfigurationError, load_api_configuration
from stock_tracker.api.composition import create_local_app
from stock_tracker.api import launcher
from stock_tracker.persistence.models import WatchlistRecord
from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
from stock_tracker.providers.models import PriceBar
from test_api_foundation import authorized_headers, credential, invoke, scope
from test_api_watchlists import row


ROOT = Path(__file__).resolve().parents[1]
_loop = None


@pytest.fixture(scope="module", autouse=True)
def native_loop():
    global _loop
    _loop = asyncio.new_event_loop()
    try:
        yield
    finally:
        _loop.run_until_complete(_loop.shutdown_asyncgens())
        _loop.run_until_complete(_loop.shutdown_default_executor())
        _loop.close()


def options(tmp_path):
    return {"database": str(tmp_path / "state.sqlite3"), "history_cache": str(tmp_path / "cache.json"),
            "menu_legacy": str(tmp_path / "menu.pkl"), "evaluation_legacy": str(tmp_path / "evaluation.pkl")}


def configured(tmp_path, monkeypatch, **kwargs):
    monkeypatch.setenv("STOCK_TRACKER_API_TOKEN", credential())
    return load_api_configuration(**options(tmp_path), **kwargs)


def request(app, path="/health", *, headers=None, query=b"", no_receive=False):
    return _loop.run_until_complete(invoke(app, scope(path, headers=headers if headers is not None else authorized_headers(), query=query), no_receive=no_receive))


@pytest.mark.parametrize("token", [None, "", "short", "x" * 257, "x" * 31, "x" * 31 + " ", "x" * 31 + "é", "x" * 31 + "\n", "x" * 31 + ":"])
def test_token_required_valid_and_safe(tmp_path, monkeypatch, token):
    if token is None:
        monkeypatch.delenv("STOCK_TRACKER_API_TOKEN", raising=False)
    else:
        monkeypatch.setenv("STOCK_TRACKER_API_TOKEN", token)
    monkeypatch.setattr("dotenv.load_dotenv", lambda: pytest.fail("API token read dotenv"))
    with pytest.raises(ApiConfigurationError) as caught:
        load_api_configuration(**options(tmp_path))
    assert str(caught.value) == "Local API configuration is invalid. Check the required token and four distinct file paths."
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("token", ["x" * 32, "A_9-" * 64])
def test_token_bounds_and_repr_and_resolved_paths(tmp_path, monkeypatch, token):
    monkeypatch.setenv("STOCK_TRACKER_API_TOKEN", token)
    opts = options(tmp_path)
    opts["database"] = "nested/../state.sqlite3"
    configuration = load_api_configuration(**opts)
    assert configuration.database == tmp_path / "state.sqlite3"
    assert configuration.token == token and token not in repr(configuration)
    assert configuration.enable_history is False and not list(tmp_path.iterdir())


def test_configuration_cannot_bypass_loader_and_composition_guard_is_pure(tmp_path, monkeypatch):
    with pytest.raises(ApiConfigurationError):
        ApiConfiguration(*(tmp_path / "same" for _ in range(4)), token=None)
    forged = object.__new__(ApiConfiguration)
    with pytest.raises(ApiConfigurationError):
        create_local_app(forged)
    configuration = configured(tmp_path, monkeypatch)
    monkeypatch.setattr(Path, "stat", lambda *a, **k: pytest.fail("Composition repeated metadata checks"))
    monkeypatch.setattr(Path, "resolve", lambda *a, **k: pytest.fail("Composition repeated resolution"))
    create_local_app(configuration)
    for name, bad in (("token", None), ("enable_history", "true"), ("database", configuration.history_cache)):
        previous = getattr(configuration, name)
        object.__setattr__(configuration, name, bad)
        with pytest.raises(ApiConfigurationError):
            create_local_app(configuration)
        object.__setattr__(configuration, name, previous)


@pytest.mark.parametrize("first,second", [(a, b) for a in range(4) for b in range(a + 1, 4)])
def test_all_missing_path_alias_pairs_rejected(tmp_path, monkeypatch, first, second):
    monkeypatch.setenv("STOCK_TRACKER_API_TOKEN", credential())
    opts = options(tmp_path)
    keys = list(opts)
    opts[keys[second]] = str(tmp_path / "absent" / ".." / Path(opts[keys[first]]).name)
    with pytest.raises(ApiConfigurationError):
        load_api_configuration(**opts)
    assert not list(tmp_path.iterdir())


def test_existing_hardlink_alias_rejected_without_contents(tmp_path, monkeypatch):
    monkeypatch.setenv("STOCK_TRACKER_API_TOKEN", credential())
    opts = options(tmp_path)
    Path(opts["database"]).write_bytes(b"opaque")
    os.link(opts["database"], opts["history_cache"])
    monkeypatch.setattr(Path, "open", lambda *a, **k: pytest.fail("Launch opened state contents"))
    with pytest.raises(ApiConfigurationError):
        load_api_configuration(**opts)


def test_symlink_alias_and_dangling_symlink_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("STOCK_TRACKER_API_TOKEN", credential())
    opts = options(tmp_path)
    original = Path(opts["database"])
    alias = Path(opts["history_cache"])
    original.write_bytes(b"opaque")
    try:
        alias.symlink_to(original)
    except OSError as error:
        if os.name != "nt" or getattr(error, "winerror", None) != 1314:
            raise
        # Actual Win32 symlink privilege is unavailable; the exact metadata
        # refusal branch is still tested below without changing system policy.
        from stat import S_IFLNK
        real_lstat = Path.lstat
        monkeypatch.setattr(Path, "lstat", lambda path: type("Stat", (), {"st_mode": S_IFLNK})()
                            if path == alias else real_lstat(path))
        with pytest.raises(ApiConfigurationError):
            load_api_configuration(**opts)
        return
    with pytest.raises(ApiConfigurationError):
        load_api_configuration(**opts)
    alias.unlink()
    alias.symlink_to(tmp_path / "missing")
    with pytest.raises(ApiConfigurationError):
        load_api_configuration(**opts)


def test_symlink_parent_missing_targets_alias(tmp_path, monkeypatch):
    monkeypatch.setenv("STOCK_TRACKER_API_TOKEN", credential())
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError as error:
        if os.name == "nt" and getattr(error, "winerror", None) == 1314:
            from stat import S_IFLNK
            real_lstat, real_resolve = Path.lstat, Path.resolve
            monkeypatch.setattr(Path, "lstat", lambda path: type("Stat", (), {"st_mode": S_IFLNK})()
                                if path == link else real_lstat(path))
            def resolve(path, *args, **kwargs):
                if path == link or link in path.parents:
                    return real_resolve(target / path.relative_to(link), *args, **kwargs)
                return real_resolve(path, *args, **kwargs)
            monkeypatch.setattr(Path, "resolve", resolve)
        else:
            raise
    opts = options(tmp_path)
    opts["database"], opts["history_cache"] = str(target / "missing"), str(link / "missing")
    with pytest.raises(ApiConfigurationError):
        load_api_configuration(**opts)


@pytest.mark.skipif(os.name != "nt", reason="Native Windows junction metadata")
def test_native_junction_resolves_alias_and_refuses_dangling_parent(tmp_path, monkeypatch):
    import _winapi
    monkeypatch.setenv("STOCK_TRACKER_API_TOKEN", credential())
    target, junction = tmp_path / "target", tmp_path / "junction"
    target.mkdir()
    _winapi.CreateJunction(str(target), str(junction))
    opts = options(tmp_path)
    opts["history_cache"] = str(junction / "cache.json")
    assert load_api_configuration(**opts).history_cache == target / "cache.json"
    opts["database"] = str(target / "cache.json")
    with pytest.raises(ApiConfigurationError):
        load_api_configuration(**opts)
    opts["database"] = str(tmp_path / "state.sqlite3")
    target.rmdir()
    with pytest.raises(ApiConfigurationError):
        load_api_configuration(**opts)


def test_non_symlink_reparse_point_requires_strict_resolution(tmp_path, monkeypatch):
    import stat
    monkeypatch.setenv("STOCK_TRACKER_API_TOKEN", credential())
    candidate = tmp_path / "junction"
    opts = options(tmp_path)
    opts["history_cache"] = str(candidate / "cache.json")
    original_lstat, original_resolve = Path.lstat, Path.resolve
    monkeypatch.setattr(Path, "lstat", lambda path: type("Stat", (), {
        "st_mode": stat.S_IFDIR, "st_file_attributes": stat.FILE_ATTRIBUTE_REPARSE_POINT})()
        if path == candidate else original_lstat(path))
    strict_checks = []
    def resolve(path, *, strict=False):
        if path == candidate and strict:
            strict_checks.append(path)
            raise FileNotFoundError("synthetic dangling junction")
        return original_resolve(path, strict=strict)
    monkeypatch.setattr(Path, "resolve", resolve)
    with pytest.raises(ApiConfigurationError):
        load_api_configuration(**opts)
    assert strict_checks == [candidate]


@pytest.mark.parametrize("value", ["", "bad\x00name"])
def test_invalid_paths_safe(tmp_path, monkeypatch, value):
    monkeypatch.setenv("STOCK_TRACKER_API_TOKEN", credential())
    opts = options(tmp_path)
    opts["history_cache"] = value
    with pytest.raises(ApiConfigurationError):
        load_api_configuration(**opts)


def test_directory_and_file_parent_refused(tmp_path, monkeypatch):
    monkeypatch.setenv("STOCK_TRACKER_API_TOKEN", credential())
    opts = options(tmp_path)
    opts["database"] = str(tmp_path)
    with pytest.raises(ApiConfigurationError):
        load_api_configuration(**opts)
    parent = tmp_path / "parent"
    parent.write_bytes(b"opaque")
    opts["database"] = str(parent / "child")
    with pytest.raises(ApiConfigurationError):
        load_api_configuration(**opts)


def test_inaccessible_metadata_and_resolution_fail_safely(tmp_path, monkeypatch):
    monkeypatch.setenv("STOCK_TRACKER_API_TOKEN", credential())
    monkeypatch.setattr(Path, "lstat", lambda *a, **k: (_ for _ in ()).throw(PermissionError("private path")))
    with pytest.raises(ApiConfigurationError) as caught:
        load_api_configuration(**options(tmp_path))
    assert "private path" not in str(caught.value)


def test_native_case_behavior(tmp_path, monkeypatch):
    monkeypatch.setenv("STOCK_TRACKER_API_TOKEN", credential())
    opts = options(tmp_path)
    opts["database"], opts["history_cache"] = str(tmp_path / "CASE"), str(tmp_path / "case")
    if os.name == "nt":
        with pytest.raises(ApiConfigurationError):
            load_api_configuration(**opts)
    else:
        assert load_api_configuration(**opts).database != load_api_configuration(**opts).history_cache


@pytest.mark.skipif(os.name != "nt", reason="Native Windows ambiguous path semantics")
@pytest.mark.parametrize("value", ["target.", "target ", "NUL", "CON.txt", "file:stream", "C:relative", "\\\\?\\C:\\missing", "\\\\.\\C:\\missing", "//?/C:/missing", "\\\\?/C:/missing"])
def test_windows_ambiguous_paths_refused(tmp_path, monkeypatch, value):
    monkeypatch.setenv("STOCK_TRACKER_API_TOKEN", credential())
    opts = options(tmp_path)
    opts["database"] = value
    with pytest.raises(ApiConfigurationError):
        load_api_configuration(**opts)


@pytest.mark.skipif(os.name != "nt", reason="Native Windows namespace aliases")
@pytest.mark.parametrize("first,second", [(a, b) for a in range(4) for b in range(a + 1, 4)])
@pytest.mark.parametrize("prefix", ["\\\\?\\", "//?/", "\\\\?/", "\\\\.\\"])
def test_windows_namespace_aliases_all_roles(tmp_path, monkeypatch, first, second, prefix):
    monkeypatch.setenv("STOCK_TRACKER_API_TOKEN", credential())
    opts = options(tmp_path)
    keys = list(opts)
    opts[keys[second]] = prefix + opts[keys[first]]
    with pytest.raises(ApiConfigurationError):
        load_api_configuration(**opts)
    assert not list(tmp_path.iterdir())


def test_composition_health_rejections_and_disabled_history_acquire_no_io(tmp_path, monkeypatch):
    configuration = configured(tmp_path, monkeypatch)
    def denied(*a, **k):
        pytest.fail("Application IO acquired")
    import config
    import stock_tracker.providers.factory as factory
    monkeypatch.setattr(config, "load_configuration", denied)
    monkeypatch.setattr(factory, "create_historical_market_data_provider", denied)
    monkeypatch.setattr(Path, "stat", denied)
    monkeypatch.setattr(Path, "lstat", denied)
    app = create_local_app(configuration)
    assert request(app)[0:2] == (200, {"status": "ok"})
    assert request(app, "/api/v1/openapi.json")[0] == 200
    history = "/api/v1/watchlists/menu_watchlist/entries/0/history"
    assert request(app, history)[1]["error"]["code"] == "history_disabled"
    for headers, expected in [([(b"host", b"127.0.0.1:8000")], 401),
                              ([(b"host", b"outside.invalid")], 400),
                              ([*authorized_headers(), (b"origin", b"null")], 403)]:
        assert request(app, "/api/v1/watchlists/menu_watchlist", headers=headers, no_receive=True)[0] == expected


@pytest.mark.parametrize("enabled", [False, True])
def test_real_local_view_no_provider_key_cache_or_writes(tmp_path, monkeypatch, enabled):
    configuration = configured(tmp_path, monkeypatch, enable_history=enabled)
    repository = SQLiteWatchlistRepository(configuration.database)
    for namespace in ("menu_watchlist", "daniils_stock_method"):
        repository.save(WatchlistRecord(namespace, "Saved", (row(), row())))
    before = configuration.database.read_bytes()
    import config
    monkeypatch.setattr(config, "load_configuration", lambda: pytest.fail("View read provider credentials"))
    app = create_local_app(configuration)
    for namespace in ("menu_watchlist", "daniils_stock_method"):
        status, payload, _, _ = request(app, "/api/v1/watchlists/" + namespace)
        assert status == 200 and [entry["ordinal"] for entry in payload["entries"]] == [0, 1]
        assert payload["entries"][0]["snapshot"]["market_value"] == "1200"
    assert configuration.database.read_bytes() == before
    assert set(tmp_path.iterdir()) == {configuration.database}


def test_real_empty_and_legacy_namespaces_preserve_files(tmp_path, monkeypatch):
    configuration = configured(tmp_path, monkeypatch)
    app = create_local_app(configuration)
    assert request(app, "/api/v1/watchlists/menu_watchlist")[1]["entries"] == []
    configuration.menu_legacy.write_bytes(b"opaque legacy")
    assert request(app, "/api/v1/watchlists/menu_watchlist")[1]["error"]["code"] == "legacy_state_present"
    assert request(app, "/api/v1/watchlists/daniils_stock_method")[1]["entries"] == []
    assert not configuration.database.exists() and not configuration.history_cache.exists()
    assert configuration.menu_legacy.read_bytes() == b"opaque legacy"


def test_supported_history_lazily_uses_existing_configuration_factory_and_explicit_cache(tmp_path, monkeypatch):
    configuration = configured(tmp_path, monkeypatch, enable_history=True)
    repository = SQLiteWatchlistRepository(configuration.database)
    repository.save(WatchlistRecord("menu_watchlist", "Saved", (row(), row())))
    before = configuration.database.read_bytes()
    import config
    import stock_tracker.providers.factory as factory
    calls = []
    class Provider:
        def get_price_history(self, symbol, start, end):
            calls.append((symbol, start, end))
            return [PriceBar(symbol, date(2020, 1, 2), row().current_price, row().current_price,
                             row().current_price, row().current_price, None, 0)]
    def create(key, *, cache_path):
        assert key == "synthetic provider header" and cache_path == configuration.history_cache
        calls.append("factory")
        return Provider()
    monkeypatch.setattr(config, "load_configuration", lambda: config.Configuration("synthetic provider header"))
    monkeypatch.setattr(factory, "create_historical_market_data_provider", create)
    app = create_local_app(configuration)
    monkeypatch.setattr("stock_tracker.api.composition.datetime", type("Clock", (), {"now": staticmethod(lambda zone: datetime(2020, 1, 4, tzinfo=timezone.utc))}))
    status, payload, _, _ = request(app, "/api/v1/watchlists/menu_watchlist/entries/1/history", query=b"start=2020-01-02&end=2020-01-03")
    assert status == 200 and payload["ordinal"] == 1
    assert payload["provenance"]["source"] == "fmp" and payload["provenance"]["freshness"] == "accepted_cache_policy"
    assert calls == ["factory", ("AAPL", date(2020, 1, 2), date(2020, 1, 3))]
    assert configuration.database.read_bytes() == before and not configuration.history_cache.exists()


@pytest.mark.parametrize("failure", ["load", "factory"])
def test_missing_provider_configuration_safe_upstream_failure(tmp_path, monkeypatch, failure):
    configuration = configured(tmp_path, monkeypatch, enable_history=True)
    SQLiteWatchlistRepository(configuration.database).save(WatchlistRecord("menu_watchlist", "Saved", (row(),)))
    import config
    import stock_tracker.providers.factory as factory
    def broken(*a, **k):
        raise config.ConfigurationError("synthetic private diagnostic")
    monkeypatch.setattr(config, "load_configuration", broken if failure == "load" else lambda: config.Configuration())
    monkeypatch.setattr(factory, "create_historical_market_data_provider", broken)
    result = request(create_local_app(configuration), "/api/v1/watchlists/menu_watchlist/entries/0/history", query=b"start=2020-01-02&end=2020-01-03")
    assert result[0] == 503 and result[1]["error"]["code"] == "provider_unavailable"
    assert "private" not in str(result)


@pytest.mark.parametrize("case,expected", [("unsupported", 503), ("invalid_range", 422), ("absent", 404)])
def test_saved_identity_range_and_row_checks_precede_configuration(tmp_path, monkeypatch, case, expected):
    configuration = configured(tmp_path, monkeypatch, enable_history=True)
    entry = row(exchange="NYSE" if case == "unsupported" else "NASDAQ")
    SQLiteWatchlistRepository(configuration.database).save(WatchlistRecord("menu_watchlist", "Saved", (entry,)))
    import config
    monkeypatch.setattr(config, "load_configuration", lambda: pytest.fail("Rejected identity/range acquired credentials"))
    query = b"start=2020-01-03&end=2020-01-02" if case == "invalid_range" else b"start=2020-01-02&end=2020-01-03"
    ordinal = "1" if case == "absent" else "0"
    assert request(create_local_app(configuration), f"/api/v1/watchlists/menu_watchlist/entries/{ordinal}/history", query=query)[0] == expected


def arguments(tmp_path):
    return [item for key, value in options(tmp_path).items() for item in ("--" + key.replace("_", "-"), value)]


def test_launcher_fixed_server_options_no_real_listener(tmp_path, monkeypatch):
    configured(tmp_path, monkeypatch)
    import uvicorn
    calls = []
    monkeypatch.setattr(uvicorn, "run", lambda app, **kwargs: calls.append((app, kwargs)))
    assert launcher.main(arguments(tmp_path)) == 0
    assert len(calls) == 1 and calls[0][1] == {"host": "127.0.0.1", "port": 8000, "workers": 1, "reload": False,
        "proxy_headers": False, "forwarded_allow_ips": "", "access_log": False, "log_config": None, "log_level": "critical"}
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("error", [RuntimeError("synthetic private token/path"), SystemExit(1)])
def test_launcher_startup_failure_safe(tmp_path, monkeypatch, capsys, error):
    configured(tmp_path, monkeypatch)
    import uvicorn
    monkeypatch.setattr(uvicorn, "run", lambda *a, **k: (_ for _ in ()).throw(error))
    assert launcher.main(arguments(tmp_path)) == 1
    captured = capsys.readouterr()
    assert captured.out == "" and "private" not in captured.err and "port 8000" in captured.err


def test_launcher_missing_token_safe(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("STOCK_TRACKER_API_TOKEN", raising=False)
    assert launcher.main(arguments(tmp_path)) == 2
    assert "configuration is invalid" in capsys.readouterr().err


@pytest.mark.parametrize("argv", [[], ["--host", "synthetic sensitive argument"], ["--database", "private path"],
                                  ["--enable-history", "--enable-history"], ["--database", "one", "--database", "two"],
                                  ["--token", "synthetic sensitive argument"], ["--dat", "private path"], ["@private-file"]])
def test_argument_failures_do_not_echo_supplied_values(argv, capsys):
    with pytest.raises(SystemExit) as caught:
        launcher.main(argv)
    assert caught.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == "Local API arguments are invalid. Use --help for the four required file options.\n"


def test_source_launcher_probe(tmp_path):
    result = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "tests/api_launcher_probe.py"), str(ROOT / "src")],
                            cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == "" and not list(tmp_path.iterdir())
