"""Accepted local Stock identity and infrastructure isolation contracts."""

from dataclasses import FrozenInstanceError, fields
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_stock_required_optional_fields_and_exact_spelling():
    from stock_tracker.domain import Stock

    stock = Stock("brk.b", name="Berkshire Hathaway", exchange="NYSE")
    assert (stock.symbol, stock.name, stock.exchange) == (
        "brk.b", "Berkshire Hathaway", "NYSE",
    )
    assert [field.name for field in fields(stock)] == ["symbol", "name", "exchange"]
    assert Stock("AAPL").name is None
    assert Stock("AAPL").exchange is None


@pytest.mark.parametrize("field", ["symbol", "name", "exchange"])
@pytest.mark.parametrize("invalid", ["", " \t", " AAPL", "AAPL\n", 1, False, []])
def test_invalid_fields_raise_safe_local_errors(field, invalid):
    from stock_tracker.domain import DomainValidationError, Stock

    values = {"symbol": "AAPL", field: invalid}
    with pytest.raises(DomainValidationError) as caught:
        Stock(**values)
    assert str(caught.value) == (
        f"{field} must be a nonblank string without surrounding whitespace."
    )


def test_required_symbol_and_safe_error_do_not_echo_input():
    from stock_tracker.domain import DomainValidationError, Stock

    for value in (None, " private-input "):
        with pytest.raises(DomainValidationError) as caught:
            Stock(value)
        assert "private-input" not in str(caught.value)
        assert str(caught.value).startswith("symbol must")


@pytest.mark.parametrize("field", ["symbol", "name", "exchange"])
def test_stock_fields_cannot_change_or_be_deleted(field):
    from stock_tracker.domain import Stock

    stock = Stock("AAPL", name="Apple", exchange="NASDAQ")
    with pytest.raises(FrozenInstanceError):
        setattr(stock, field, "changed")
    with pytest.raises(FrozenInstanceError):
        delattr(stock, field)
    assert (stock.symbol, stock.name, stock.exchange) == ("AAPL", "Apple", "NASDAQ")


def test_known_identity_ignores_name_but_preserves_symbol_and_exchange():
    from stock_tracker.domain import Stock

    first = Stock("AAPL", name="Apple", exchange="NASDAQ")
    renamed = Stock("AAPL", None, "NASDAQ")
    assert first == renamed
    assert renamed == first
    assert hash(first) == hash(renamed) == hash(("AAPL", "NASDAQ"))
    assert len({first, renamed}) == 1
    assert first != Stock("AAPL", exchange="NYSE")
    assert first != Stock("aapl", exchange="NASDAQ")
    assert first != Stock("AAPL", exchange="nasdaq")
    assert first != "AAPL"


def test_unknown_identity_is_reflexive_and_distinct_from_other_instances():
    from stock_tracker.domain import Stock

    first = Stock("AAPL")
    second = Stock("AAPL")
    known = Stock("AAPL", exchange="NASDAQ")
    assert first == first
    assert first != second
    assert second != first
    assert first != known
    assert known != first
    assert hash(first) == object.__hash__(first)
    assert hash(second) == object.__hash__(second)
    assert len({first, second, known}) == 3
    assert {first: "unresolved"}[first] == "unresolved"


def test_domain_import_and_construction_without_infrastructure(tmp_path):
    # An independent process guards imports and operations before importing domain.
    # Preloading stdlib dataclasses avoids denying its own lazy stdlib setup.
    code = """
import builtins
import dataclasses
import os
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, sys.argv[1])
original_import = builtins.__import__
forbidden = {'config', 'stock', 'watch_list', 'menu_watchlist', 'daniils_stock_method',
             'dotenv', 'rich', 'typer', 'matplotlib', 'utils', 'urllib', 'socket',
             'sqlite3', 'stock_tracker.compatibility'}

def guarded_import(name, *args, **kwargs):
    # Relative domain imports use names such as 'stock'; reject absolute imports only.
    level = kwargs.get('level', args[3] if len(args) > 3 else 0)
    if level == 0 and any(name == item or name.startswith(item + '.') for item in forbidden):
        raise AssertionError('Infrastructure import denied')
    return original_import(name, *args, **kwargs)

def denied(*args, **kwargs):
    raise AssertionError('Infrastructure operation denied')

with patch.object(builtins, '__import__', guarded_import), \
     patch.object(builtins, 'open', denied), \
     patch.object(builtins, 'print', denied), \
     patch.object(os, 'getenv', denied), \
     patch.object(type(os.environ), '__getitem__', denied):
    from stock_tracker.domain import Stock, DomainValidationError
    stock = Stock('AAPL', exchange='NASDAQ')
    assert stock == Stock('AAPL', 'Apple', 'NASDAQ')
    assert Stock('AAPL') != Stock('AAPL')
    assert issubclass(DomainValidationError, ValueError)
    assert Path(sys.modules[Stock.__module__].__file__).resolve().is_relative_to(
        Path(sys.argv[1]).resolve())
    # Demonstrate that the same guards reject safe prohibited probes.
    for probe in (lambda: __import__('config'), lambda: os.getenv('DOMAIN_PROBE'),
                  lambda: open('domain-probe', 'w'), lambda: print('domain-probe')):
        try:
            probe()
        except AssertionError:
            pass
        else:
            raise AssertionError('Guard did not enforce isolation')
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code, str(ROOT / "src")],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == ""
    assert not (tmp_path / "domain-probe").exists()
