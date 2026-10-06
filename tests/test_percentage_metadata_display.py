"""Accepted percentage display metadata survives real offline CLI restoration."""

import json
from pathlib import Path
import runpy

import pytest
from typer.testing import CliRunner


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("value", [None, "", "-", "N/A"])
def test_missing_percentage_metadata_uses_existing_display(value):
    from watch_list import Watch_list
    assert Watch_list.wrap_percent(value) == "-"


@pytest.mark.parametrize("value,color", [("2.500", "green"), ("-2.500", "red"),
                                        ("0", "green"), ("-0.00", "green"),
                                        ("+3", "green"), ("1e2", "green"),
                                        (" 4.0 ", "green")])
def test_numeric_percentage_format_and_color_remain_exact(value, color):
    from watch_list import Watch_list
    assert Watch_list.wrap_percent(value) == f"[{color}]{value}%[/]"


@pytest.mark.parametrize("value", ["Unrated", "No estimate", "5%", " ",
                                  "[red]literal[/red]", "[/]", "[link=https://example.invalid]literal[/link]"])
def test_nonnumeric_display_is_literal_without_color_or_percent(value):
    from rich.markup import escape
    from rich.text import Text
    from watch_list import Watch_list
    rendered = Watch_list.wrap_percent(value)
    assert rendered == escape(value)
    displayed = Text.from_markup(rendered)
    assert displayed.plain == value and displayed.spans == []


@pytest.mark.parametrize("script,namespace", [("menu_watchlist.py", "menu_watchlist"),
                                            ("daniils_stock_method.py", "daniils_stock_method")])
def test_real_cli_restores_display_metadata_offline_without_changing_sqlite(tmp_path, monkeypatch, script, namespace):
    from stock_tracker.persistence.transfer import import_neutral_state
    from stock_tracker.persistence.sqlite_watchlists import SQLiteWatchlistRepository
    from stock_tracker.compatibility import stock_operations
    import config
    import stock
    metadata = dict(sector="Tech", country="US", currency="USD", market_cap="1.000B",
                    price_1d="", price_5d="Unrated", price_30d="[red]literal[/red]",
                    price_3m="-2.500", price_6m="0", price_1y="N/A", price_3y="-", price_5y=None)
    entry = dict(stock=dict(symbol="ABC", name="Example", exchange="NASDAQ"),
                 quantity="0.2500", average_cost="100.0000", current_price="120.0000", **metadata)
    payload = dict(format="stock-tracker-neutral", version=1, portfolios=[], watchlists=[
        dict(namespace=key, name="Metadata", entries=[entry])
        for key in ("menu_watchlist", "daniils_stock_method")
    ])
    source, database = tmp_path / "neutral.json", tmp_path / "stock_tracker.sqlite3"
    source.write_text(json.dumps(payload), encoding="utf-8")
    import_neutral_state(source, database)
    before, original_source = database.read_bytes(), source.read_bytes()
    original_record = SQLiteWatchlistRepository(database).get(namespace)
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    monkeypatch.delenv("MY_API_KEY", raising=False)
    monkeypatch.setenv("COLUMNS", "600")
    def denied(*args, **kwargs):
        pytest.fail("Offline display requested a credential or provider")
    monkeypatch.setattr(config, "require_api_key", denied)
    monkeypatch.setattr(stock, "load_configuration", denied)
    monkeypatch.setattr(stock_operations.provider_factory, "create_market_data_provider", denied)
    module = runpy.run_path(str(ROOT / script), run_name="percentage_display_restart")
    assert module["API_KEY"] is None
    assert module["current_watchlist"].stocks == []
    result = CliRunner().invoke(module["app"], ["show-stocks"], terminal_width=600)
    assert result.exit_code == 0, result.output
    assert "ABC" in result.output and "Unrated" in result.output
    assert "[red]literal[/red]" in result.output
    restored = module["current_watchlist"].stocks[0]
    assert restored.API_KEY is None
    assert restored.amount_owned == "0.2500" and restored.cost_basis == "100.0000"
    assert restored.current_price == "120.0000" and restored.total_return == "20.0"
    assert {field: getattr(restored, field) for field in metadata} == metadata
    current_record = SQLiteWatchlistRepository(database).get(namespace)
    assert current_record == original_record
    assert database.read_bytes() == before and source.read_bytes() == original_source
