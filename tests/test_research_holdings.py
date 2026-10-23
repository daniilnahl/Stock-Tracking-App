"""Fictional local-only FC-051 projection fixtures; no deployment cap defaults."""

from decimal import Decimal, Inexact, InvalidOperation, Overflow, ROUND_DOWN, localcontext
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from stock_tracker.domain import (
    DomainValidationError, Position, PositionValuationInput,
    SnapshotCurrencyMismatchError, SnapshotCurrencyUnavailableError, Stock,
    portfolio_snapshot,
)
from stock_tracker.services.research_holdings import (
    ResearchHoldingsValidationError, project_holdings,
)


ROOT = Path(__file__).resolve().parents[1]


def row(quantity="10", cost="100", price="120", *, symbol="A", exchange="NASDAQ",
        cost_currency="USD", quote_currency="USD", name=None):
    return PositionValuationInput(
        Position(Stock(symbol, name=name, exchange=exchange), Decimal(quantity), Decimal(cost)),
        None if price is None else Decimal(price), cost_currency, quote_currency,
    )


def project(rows, **changes):
    # These explicit fictional caller bounds are test data, never product defaults.
    return project_holdings(rows, **{**dict(currency="USD", max_rows=100, max_output_bytes=65536),
                                    **changes})


def test_known_values_exact_ascii_bytes_and_private_field_allowlist():
    inputs = (row(name="PRIVATE-NAME"), row("5", "40", "60", symbol="B", exchange="PRIVATE-EXCHANGE"))
    expected = b'[{"portfolio_weight":"0.8","ticker":"A"},{"portfolio_weight":"0.2","ticker":"B"}]'
    result = project(inputs)
    assert type(result) is bytes and result == expected
    assert not result.endswith(b"\n")
    decoded = json.loads(result)
    assert all(set(item) == {"ticker", "portfolio_weight"} for item in decoded)
    for forbidden in (b"PRIVATE", b"quantity", b"average_cost", b"cost_basis", b"price",
                      b"exchange", b"namespace", b"ordinal", b"account", b"name"):
        assert forbidden not in result


def test_fractional_known_values():
    result = project((row("0.25"), row("0.5", "200", "240", symbol="B")))
    assert result == b'[{"portfolio_weight":"0.2","ticker":"A"},{"portfolio_weight":"0.8","ticker":"B"}]'


@pytest.mark.parametrize("rows,weights", [
    ((), []),
    ((row(price="0"),), [None]),
    ((row(quantity="0"),), [None]),
    ((row(quantity="0", price=None),), [None]),
    ((row(), row("0", price=None, symbol="B")), [None, None]),
    ((row(), row(price=None, symbol="B")), [None, None]),
    ((row(price="0"), row("5", "40", "60", symbol="B")), ["0", "1"]),
    ((row("0", "0", "120"), row("5", "0", "60", symbol="B")), ["0", "1"]),
    ((row("10", "0", "120"),), ["1"]),
])
def test_empty_missing_zero_and_nonpositive_total(rows, weights):
    assert [item["portfolio_weight"] for item in json.loads(project(rows))] == weights


def test_order_duplicate_identity_and_unresolved_exchange_not_merged():
    nyse, nasdaq, unknown = row(exchange="NYSE"), row(exchange="NASDAQ"), row(exchange=None)
    inputs = (nyse, nasdaq, unknown, nyse)
    result = json.loads(project(inputs))
    assert result == [{"ticker": "A", "portfolio_weight": "0.25"}] * 4
    assert len(inputs) == len(result)
    assert [item.position.stock.exchange for item in inputs] == ["NYSE", "NASDAQ", None, "NYSE"]


def test_caller_context_precision_rounding_flags_and_representation_preserved():
    inputs = (row("1", "1", "1"), row("1", "1", "2", symbol="B"))
    with localcontext() as context:
        context.prec = 7
        context.rounding = ROUND_DOWN
        context.traps[Inexact] = False
        context.clear_flags()
        before = (context.prec, context.rounding, context.Emin, context.Emax, dict(context.traps))
        result = json.loads(project(inputs))
        projected_flags = dict(context.flags)
        assert [item["portfolio_weight"] for item in result] == ["0.3333333", "0.6666666"]
        assert before == (context.prec, context.rounding, context.Emin, context.Emax, dict(context.traps))
        context.clear_flags()
        accepted = portfolio_snapshot(inputs, currency="USD")
        assert projected_flags == dict(context.flags)
        assert [item["portfolio_weight"] for item in result] == [str(item.weight) for item in accepted.positions]


def test_existing_decimal_trap_propagates_without_modifying_context():
    inputs = (row("1", "1", "1"), row("1", "1", "2", symbol="B"))
    with localcontext() as context:
        context.prec = 7
        context.traps[Inexact] = True
        before = (context.prec, context.rounding, dict(context.traps))
        with pytest.raises(Inexact):
            project(inputs)
        assert before == (context.prec, context.rounding, dict(context.traps))
        assert context.flags[Inexact]


def test_nonfinite_analytics_from_disabled_overflow_traps_cannot_publish():
    inputs = (row(), row("5", "40", "60", symbol="B"))
    with localcontext() as context:
        context.prec = 6
        context.Emax = 2
        context.traps[Overflow] = False
        context.traps[InvalidOperation] = False
        context.clear_flags()
        before = (context.prec, context.Emax, context.Emin, context.rounding, dict(context.traps))
        with pytest.raises(ResearchHoldingsValidationError):
            project(inputs)
        assert context.flags[Overflow]
        assert before == (context.prec, context.Emax, context.Emin, context.rounding, dict(context.traps))


def test_signed_zero_exponent_and_significant_zero_weight_spelling():
    signed = project((row("-0.00", "0", "1"), row("1", "0", "1", symbol="B")))
    # Existing analytics divides -0.00 by the aggregate 1.00, yielding -0.
    assert json.loads(signed)[0]["portfolio_weight"] == "-0"
    significant = project((row("1.00", "0", "1"), row("3.00", "0", "1", symbol="B")))
    assert [item["portfolio_weight"] for item in json.loads(significant)] == ["0.25", "0.75"]
    tiny = project((row("1E-8", "0", "1"), row("0.99999999", "0", "1", symbol="B")))
    assert [item["portfolio_weight"] for item in json.loads(tiny)] == ["1E-8", "0.99999999"]


@pytest.mark.parametrize("field", ["cost_currency", "quote_currency"])
@pytest.mark.parametrize("value,error", [(None, SnapshotCurrencyUnavailableError),
                                        ("EUR", SnapshotCurrencyMismatchError),
                                        ("usd", SnapshotCurrencyMismatchError)])
@pytest.mark.parametrize("quantity,price", [("10", "120"), ("0", "120"), ("0", None)])
def test_currency_evidence_errors_survive_including_zero_quantity(field, value, error, quantity, price):
    inputs = (row(), row(quantity=quantity, price=price, **{field: value}))
    with pytest.raises(error):
        project(inputs)


@pytest.mark.parametrize("currency", [None, "", " ", " USD", "USD ", 1, True])
def test_aggregate_currency_is_not_inferred_even_when_empty(currency):
    with pytest.raises((ResearchHoldingsValidationError, DomainValidationError)):
        project((), currency=currency)


def test_inclusive_row_and_output_byte_caps_and_empty_array():
    inputs = (row(), row("5", "40", "60", symbol="B"))
    exact = project(inputs)
    assert project(inputs, max_rows=len(inputs), max_output_bytes=len(exact)) == exact
    with pytest.raises(ResearchHoldingsValidationError):
        project(inputs, max_rows=len(inputs) - 1)
    with pytest.raises(ResearchHoldingsValidationError):
        project(inputs, max_output_bytes=len(exact) - 1)
    assert project((), max_rows=1, max_output_bytes=2) == b"[]"
    with pytest.raises(ResearchHoldingsValidationError):
        project((), max_rows=1, max_output_bytes=1)


@pytest.mark.parametrize("field", ["max_rows", "max_output_bytes"])
@pytest.mark.parametrize("value", [None, False, True, 0, -1, 1.0, "100", Decimal(100)])
def test_bounds_are_explicit_positive_builtin_integers(field, value):
    with pytest.raises(ResearchHoldingsValidationError):
        project((row(),), **{field: value})


def test_both_caller_bounds_are_required_without_defaults():
    with pytest.raises(TypeError):
        project_holdings((row(),), currency="USD", max_rows=1)
    with pytest.raises(TypeError):
        project_holdings((row(),), currency="USD", max_output_bytes=1000)


def test_row_cap_precedes_any_financial_arithmetic():
    inputs = (row("1", "1", "1"), row("1", "1", "2", symbol="B"))
    with localcontext() as context:
        context.traps[Inexact] = True
        context.clear_flags()
        with pytest.raises(ResearchHoldingsValidationError):
            project(inputs, max_rows=1)
        assert not any(context.flags.values())


def test_name_is_not_read_or_validated_and_input_objects_remain_unchanged(monkeypatch):
    supplied = row(name="PRIVATE-NAME")
    original_stock = supplied.position.stock
    before = (supplied.position, supplied.current_price, supplied.cost_currency, supplied.quote_currency,
              original_stock.symbol, original_stock.exchange)
    original_getattribute = Stock.__getattribute__
    def guard(instance, name):
        if instance is original_stock and name == "name":
            pytest.fail("projector read original Stock.name")
        return original_getattribute(instance, name)
    monkeypatch.setattr(Stock, "__getattribute__", guard)
    assert project((supplied,)) == b'[{"portfolio_weight":"1","ticker":"A"}]'
    assert before == (supplied.position, supplied.current_price, supplied.cost_currency, supplied.quote_currency,
                      original_stock.symbol, original_stock.exchange)
    object.__setattr__(original_stock, "name", object())
    assert project((supplied,)) == b'[{"portfolio_weight":"1","ticker":"A"}]'


@pytest.mark.parametrize("symbol", ["☃😀", "SYN\ud83d\ude00", "A\u0301"])
def test_ticker_unicode_ascii_escaping_without_normalization(symbol):
    payload = project((row(symbol=symbol),))
    expected = ('[{"portfolio_weight":"1","ticker":' + json.dumps(symbol, ensure_ascii=True) + '}]').encode("ascii")
    assert payload == expected and all(byte < 128 for byte in payload)
    assert project((row(symbol=symbol),), max_output_bytes=len(expected)) == expected
    with pytest.raises(ResearchHoldingsValidationError):
        project((row(symbol=symbol),), max_output_bytes=len(expected) - 1)


@pytest.mark.parametrize("symbol", ["\ud800", "x\udfff", "\ud800\ud800", "\udc00\ud800"])
def test_unpaired_ticker_surrogates_fail_safely(symbol):
    supplied = row()
    object.__setattr__(supplied.position.stock, "symbol", symbol)
    with pytest.raises(ResearchHoldingsValidationError) as caught:
        project((supplied,))
    assert caught.value.__cause__ is caught.value.__context__ is None


@pytest.mark.parametrize("target,field", [("stock", "exchange"), ("row", "cost_currency"),
                                         ("row", "quote_currency"), ("aggregate", "currency")])
def test_unpaired_surrogates_in_trusted_association_fields_are_structural_errors(target, field):
    supplied = row()
    kwargs = {}
    if target == "aggregate":
        kwargs[field] = "private\ud800"
    else:
        item = supplied.position.stock if target == "stock" else supplied
        object.__setattr__(item, field, "private\ud800")
    with pytest.raises(ResearchHoldingsValidationError) as caught:
        project((supplied,), **kwargs)
    assert "private" not in str(caught.value)


@pytest.mark.parametrize("rows", [None, [], {}, "private-input", (None,), (object(),)])
def test_malformed_container_or_row_type(rows):
    with pytest.raises(ResearchHoldingsValidationError):
        project(rows)


@pytest.mark.parametrize("target,field,value", [
    ("row", "position", object()), ("row", "current_price", True),
    ("row", "current_price", 120.0), ("row", "cost_currency", True),
    ("row", "quote_currency", 1), ("position", "stock", object()),
    ("position", "quantity", "10"), ("position", "average_cost", None),
    ("position", "quantity", False), ("stock", "symbol", 1),
    ("stock", "exchange", object()),
])
def test_tampered_graph_structural_types_rejected_before_calculation(target, field, value):
    supplied = row()
    item = {"row": supplied, "position": supplied.position, "stock": supplied.position.stock}[target]
    object.__setattr__(item, field, value)
    with pytest.raises(ResearchHoldingsValidationError):
        project((supplied,))


@pytest.mark.parametrize("target,field", [("row", "current_price"), ("position", "quantity"),
                                         ("position", "average_cost")])
@pytest.mark.parametrize("bad", [Decimal("-1"), Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity")])
def test_tampered_decimal_values_cannot_publish(target, field, bad):
    supplied = row()
    item = supplied if target == "row" else supplied.position
    object.__setattr__(item, field, bad)
    with pytest.raises(DomainValidationError):
        project((supplied,))


def test_arbitrary_subclass_hooks_never_run():
    def denied(*args, **kwargs):
        raise AssertionError("untrusted input hook called")
    class Rows(tuple):
        __iter__ = __len__ = __getitem__ = denied
    class Text(str):
        __str__ = __eq__ = __len__ = strip = encode = denied
    class Numeric(Decimal):
        is_finite = __lt__ = __mul__ = denied
    class Bound(int):
        __le__ = __lt__ = denied
    for inputs, changes in ((Rows((row(),)), {}), ((row(),), {"currency": Text("USD")})):
        with pytest.raises(ResearchHoldingsValidationError):
            project(inputs, **changes)
    for field in ("max_rows", "max_output_bytes"):
        with pytest.raises(ResearchHoldingsValidationError):
            project((row(),), **{field: Bound(1000)})
    for target, field, value in (("stock", "symbol", Text("A")),
                                  ("position", "quantity", Numeric("10"))):
        supplied = row()
        item = supplied.position.stock if target == "stock" else supplied.position
        object.__setattr__(item, field, value)
        with pytest.raises(ResearchHoldingsValidationError):
            project((supplied,))
    for base, target in ((PositionValuationInput, "row"), (Position, "position"), (Stock, "stock")):
        class Untrusted(base):
            __getattribute__ = denied
        forged = object.__new__(Untrusted)
        supplied = row()
        if target == "position":
            object.__setattr__(supplied, "position", forged)
        elif target == "stock":
            object.__setattr__(supplied.position, "stock", forged)
        with pytest.raises(ResearchHoldingsValidationError):
            project((forged if target == "row" else supplied,))


def test_structural_errors_are_fixed_safe_without_private_exception_context():
    class PrivateObject:
        def __str__(self):
            raise AssertionError("private-sentinel")
        __repr__ = __str__
    messages = []
    for inputs, kwargs in ((PrivateObject(), {}), ((PrivateObject(),), {}),
                            ((row(),), {"max_rows": "private-sentinel"}),
                            ((row(),), {"max_output_bytes": 1})):
        with pytest.raises(ResearchHoldingsValidationError) as caught:
            project(inputs, **kwargs)
        messages.append(str(caught.value))
        assert "private-sentinel" not in repr(caught.value)
        assert caught.value.__cause__ is caught.value.__context__ is None
    assert len(set(messages)) == 1 and messages[0]


@pytest.fixture(scope="module")
def installed_holdings_wheel(tmp_path_factory):
    directory = tmp_path_factory.mktemp("holdings-wheel")
    environment = dict(os.environ, PIP_NO_INDEX="1", PIP_DISABLE_PIP_VERSION_CHECK="1")
    subprocess.run([sys.executable, "-m", "pip", "wheel", str(ROOT), "--no-index", "--no-deps",
                    "--no-build-isolation", "--wheel-dir", str(directory)],
                   env=environment, check=True, capture_output=True, text=True, timeout=90)
    wheel, = directory.glob("*.whl")
    with zipfile.ZipFile(wheel) as archive:
        module = "stock_tracker/services/research_holdings.py"
        assert archive.read(module) == (ROOT / "src" / module).read_bytes()
    installed = directory / "installed"
    subprocess.run([sys.executable, "-m", "pip", "install", str(wheel), "--no-index", "--no-deps",
                    "--no-compile", "--target", str(installed)], env=environment,
                   check=True, capture_output=True, text=True, timeout=90)
    return installed


@pytest.mark.parametrize("distribution", ["source", "wheel"])
def test_cold_source_and_installed_wheel_are_side_effect_free(tmp_path, installed_holdings_wheel, distribution):
    import_root = ROOT / "src" if distribution == "source" else installed_holdings_wheel
    environment = {key: value for key, value in os.environ.items()
                   if key not in {"MY_API_KEY", "FMP_API_KEY", "FINNHUB_API_KEY", "PYTHONPATH"}}
    result = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "tests/research_holdings_probe.py"),
                             str(import_root)], cwd=tmp_path, env=environment,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
    assert list(tmp_path.iterdir()) == []
