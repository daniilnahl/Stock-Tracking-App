"""Real isolated SQLite aggregates, adversarial records and atomic failures."""

from decimal import Decimal
import sqlite3
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.fixture
def repository(tmp_path):
    from stock_tracker.persistence.sqlite_portfolios import SQLitePortfolioRepository
    return SQLitePortfolioRepository(tmp_path / "portfolio # %.sqlite3")


def portfolio(portfolio_id=None, name="Example", positions=None):
    from stock_tracker.domain import Portfolio
    return Portfolio(portfolio_id, name, positions)


def position(symbol="AAPL", exchange="NASDAQ", quantity="0.2500", cost="100.123456"):
    from stock_tracker.domain import Position, Stock
    return Position(Stock(symbol, "Example stock", exchange), Decimal(quantity), Decimal(cost))


def test_constructor_and_missing_reads_do_not_touch_storage(tmp_path, monkeypatch):
    from stock_tracker.persistence.sqlite_portfolios import SQLitePortfolioRepository
    from pathlib import Path
    with monkeypatch.context() as guarded:
        guarded.setattr(Path, "stat", lambda *args, **kwargs: pytest.fail("constructor IO"))
        repository = SQLitePortfolioRepository(tmp_path / "new.sqlite3")
    assert repository.get(1) is None
    assert repository.list() == []
    assert repository.delete(1) is False
    assert not repository._path.exists()


def test_roundtrip_precision_order_duplicates_and_fresh_records(repository):
    from stock_tracker.persistence.sqlite_portfolios import SQLitePortfolioRepository
    from stock_tracker.domain import position_snapshot
    supplied = portfolio(positions=[
        position(), position(), position(exchange="NYSE"), position(exchange=None),
        position(exchange=None), position(quantity="0E-30", cost="-0.000"),
        position(quantity="1.123456789012345678901234567890123456789", cost="1E+40"),
    ])
    created = repository.create(supplied)
    assert supplied.id is None and created.id == 1
    assert created.positions is not supplied.positions
    supplied.positions.clear()
    reopened = SQLitePortfolioRepository(repository._path).get(1)
    assert reopened.name == "Example" and len(reopened.positions) == 7
    assert [p.stock.exchange for p in reopened.positions] == ["NASDAQ", "NASDAQ", "NYSE", None, None, "NASDAQ", "NASDAQ"]
    assert reopened.positions[0].stock == reopened.positions[1].stock
    assert reopened.positions[3].stock != reopened.positions[4].stock
    assert str(reopened.positions[5].quantity) == "0E-30"
    assert str(reopened.positions[5].average_cost) == "-0.000"
    assert str(reopened.positions[6].quantity) == "1.123456789012345678901234567890123456789"
    assert str(reopened.positions[6].average_cost) == "1E+40"
    known = repository.create(portfolio(positions=[position(quantity="10", cost="100")]))
    snapshot = position_snapshot(repository.get(known.id).positions[0], Decimal("120"))
    assert (snapshot.cost_basis, snapshot.market_value, snapshot.unrealized_pnl,
            snapshot.unrealized_return) == (Decimal("1000"), Decimal("1200"), Decimal("200"), Decimal("0.20"))
    reopened.positions.clear()
    assert len(repository.get(1).positions) == 7


def test_arbitrary_ids_numeric_order_allocation_collision_and_reuse(repository):
    from stock_tracker.exceptions import PersistenceConflictError
    huge = 10 ** 4500
    for portfolio_id in (10, -7, 0, 2, huge):
        assert repository.create(portfolio(portfolio_id)).id == portfolio_id
    assert [p.id for p in repository.list()] == [-7, 0, 2, 10, huge]
    assert repository.create(portfolio()).id == huge + 1
    assert repository.get(huge).id == huge
    before = repository._path.read_bytes()
    with pytest.raises(PersistenceConflictError):
        repository.create(portfolio(huge, "Collision"))
    assert repository._path.read_bytes() == before
    assert repository.delete(huge + 1)
    assert repository.create(portfolio()).id == huge + 1


def test_save_delete_cascade_and_missing_targets(repository):
    from stock_tracker.exceptions import PersistenceNotFoundError
    original = repository.create(portfolio(0, positions=[position(), position()]))
    untouched = repository.create(portfolio(-1, "Other", [position()]))
    original.name = "Changed"
    original.positions = [position(quantity="0", cost="0")]
    repository.save(original)
    assert repository.get(0).name == "Changed"
    assert len(repository.get(0).positions) == 1
    repository.save(portfolio(0, "Empty"))
    assert repository.get(0).positions == []
    assert repository.delete(0) is True
    assert repository.delete(0) is False
    assert repository.get(0) is None
    assert repository.get(-1).name == untouched.name
    with sqlite3.connect(repository._path) as connection:
        assert connection.execute("SELECT count(*) FROM positions WHERE portfolio_id='0'").fetchone() == (0,)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    before = repository._path.read_bytes()
    for supplied in (portfolio(), portfolio(999)):
        with pytest.raises(PersistenceNotFoundError):
            repository.save(supplied)
    assert repository._path.read_bytes() == before


@pytest.mark.parametrize("bad", [True, False, None, "1", 1.0, Decimal("1"), [], object()])
def test_invalid_ids_fail_before_io(repository, bad, monkeypatch):
    from stock_tracker.exceptions import PersistenceValidationError
    import stock_tracker.persistence.sqlite_portfolios as module
    monkeypatch.setattr(module, "database_connection", lambda *a, **k: pytest.fail("invalid ID IO"))
    for operation in (repository.get, repository.delete):
        with pytest.raises(PersistenceValidationError):
            operation(bad)


@pytest.mark.parametrize("field,bad", [
    ("id", True), ("id", "1"), ("name", " "), ("name", " trailing "),
    ("positions", ()), ("positions", [object()]),
])
def test_mutated_portfolio_candidate_fails_before_io(repository, field, bad, monkeypatch):
    from stock_tracker.exceptions import PersistenceValidationError
    import stock_tracker.persistence.sqlite_portfolios as module
    candidate = portfolio(1)
    setattr(candidate, field, bad)
    monkeypatch.setattr(module, "database_connection", lambda *a, **k: pytest.fail("invalid aggregate IO"))
    for operation in (repository.create, repository.save):
        with pytest.raises(PersistenceValidationError):
            operation(candidate)


@pytest.mark.parametrize("field,bad", [
    ("quantity", "1"), ("quantity", Decimal("NaN")), ("quantity", Decimal("-1")),
    ("average_cost", Decimal("Infinity")), ("stock", object()),
])
def test_bypassed_position_mutations_revalidate_before_io(repository, field, bad, monkeypatch):
    from stock_tracker.exceptions import PersistenceValidationError
    import stock_tracker.persistence.sqlite_portfolios as module
    mutated = position()
    object.__setattr__(mutated, field, bad)
    monkeypatch.setattr(module, "database_connection", lambda *a, **k: pytest.fail("invalid position IO"))
    with pytest.raises(PersistenceValidationError):
        repository.create(portfolio(positions=[mutated]))


def test_sql_input_is_bound_and_literal(repository):
    malicious = "'); DROP TABLE positions; --"
    created = repository.create(portfolio(name=malicious, positions=[position(malicious, malicious)]))
    assert repository.get(created.id).name == malicious
    assert repository.get(created.id).positions[0].stock.symbol == malicious
    assert repository.get(created.id).positions[0].stock.exchange == malicious
    assert repository.create(portfolio()).id == 2


@pytest.mark.parametrize("field", ["portfolio_name", "symbol", "stock_name", "exchange"])
def test_unencodable_text_is_safe_validation_before_io(repository, field):
    from stock_tracker.domain import Position, Stock
    from stock_tracker.exceptions import PersistenceValidationError
    values = {"symbol": "AAPL", "stock_name": "Apple", "exchange": "NASDAQ"}
    if field != "portfolio_name":
        values[field] = chr(0xd800)
    candidate = portfolio(1, chr(0xd800) if field == "portfolio_name" else "Example", [
        Position(Stock(values["symbol"], values["stock_name"], values["exchange"]),
                 Decimal("1"), Decimal("100")),
    ])
    with pytest.raises(PersistenceValidationError) as failure:
        repository.create(candidate)
    assert failure.value.__suppress_context__
    assert not repository._path.exists()
    repository.create(portfolio(1))
    before = repository._path.read_bytes()
    with pytest.raises(PersistenceValidationError):
        repository.save(candidate)
    assert repository._path.read_bytes() == before


@pytest.mark.parametrize("target,field", [("portfolio", "name"), ("portfolio", "positions"),
                                         ("position", "quantity"), ("stock", "exchange")])
def test_missing_bypassed_attributes_are_invalid_input(repository, target, field):
    from stock_tracker.exceptions import PersistenceValidationError
    candidate = portfolio(1, positions=[position()])
    targets = {"portfolio": candidate, "position": candidate.positions[0],
               "stock": candidate.positions[0].stock}
    object.__delattr__(targets[target], field)
    with pytest.raises(PersistenceValidationError):
        repository.create(candidate)
    assert not repository._path.exists()


def test_read_transaction_pins_parent_and_children_snapshot(repository, monkeypatch):
    from stock_tracker.persistence import sqlite_portfolios as module
    repository.create(portfolio(1, "Before", [position(quantity="1")]))
    # WAL is only a test fixture allowing another writer during a reader snapshot;
    # production code deliberately retains SQLite's default journal policy.
    with sqlite3.connect(repository._path) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
    read_portfolio = module._read_portfolio
    def concurrent(connection, row):
        repository.save(portfolio(1, "After", [position(quantity="2")]))
        return read_portfolio(connection, row)
    monkeypatch.setattr(module, "_read_portfolio", concurrent)
    result = repository.get(1)
    assert result.name == "Before"
    assert result.positions[0].quantity == Decimal("1")
    monkeypatch.setattr(module, "_read_portfolio", read_portfolio)
    assert repository.get(1).name == "After"


def test_orphan_positions_refuse_affected_get_and_whole_list(repository):
    from stock_tracker.exceptions import PersistenceDataError
    repository.create(portfolio(1, positions=[position()]))
    with sqlite3.connect(repository._path) as connection:
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute("UPDATE positions SET portfolio_id='99'")
    before = repository._path.read_bytes()
    with pytest.raises(PersistenceDataError):
        repository.get(99)
    with pytest.raises(PersistenceDataError):
        repository.list()
    assert repository.get(1).positions == []
    assert repository._path.read_bytes() == before


def test_connections_close_after_every_public_operation(repository, monkeypatch):
    import stock_tracker.persistence.connection as boundary
    connections = []
    real_connect = boundary.sqlite3.connect
    def tracked(*args, **kwargs):
        connection = real_connect(*args, **kwargs)
        connections.append(connection)
        return connection
    monkeypatch.setattr(boundary.sqlite3, "connect", tracked)
    repository.create(portfolio(1))
    repository.get(1)
    repository.list()
    repository.save(portfolio(1, "Changed"))
    repository.delete(1)
    for connection in connections:
        with pytest.raises(sqlite3.ProgrammingError):
            connection.execute("SELECT 1")


@pytest.mark.parametrize("stored", ["01", "-0", "+1", "1.0", "1e0", " 1", "1_0", "", "bad"])
def test_bad_saved_id_refuses_whole_list_and_allocation(repository, stored):
    from stock_tracker.exceptions import PersistenceDataError
    repository.create(portfolio(1))
    with sqlite3.connect(repository._path) as connection:
        connection.execute("INSERT INTO portfolios VALUES (?, ?)", (stored, "Malformed"))
    before = repository._path.read_bytes()
    with pytest.raises(PersistenceDataError):
        repository.list()
    with pytest.raises(PersistenceDataError):
        repository.create(portfolio())
    assert repository._path.read_bytes() == before


@pytest.mark.parametrize("column,value", [
    ("quantity", "NaN"), ("quantity", "Infinity"), ("quantity", "-1"),
    ("quantity", " 1"), ("quantity", "1_0"), ("quantity", "$1"),
    ("average_cost", ""), ("average_cost", "-2"), ("symbol", " "),
    ("name", ""), ("exchange", " trailing "), ("ordinal", 2),
])
def test_malformed_child_rejects_get_and_entire_list(repository, column, value):
    from stock_tracker.exceptions import PersistenceDataError
    repository.create(portfolio(1))
    repository.create(portfolio(2, positions=[position()]))
    # Column names are fixed test parameters; values remain parameterized.
    with sqlite3.connect(repository._path) as connection:
        connection.execute(f"UPDATE positions SET {column}=? WHERE portfolio_id='2'", (value,))
    before = repository._path.read_bytes()
    with pytest.raises(PersistenceDataError):
        repository.get(2)
    with pytest.raises(PersistenceDataError):
        repository.list()
    assert repository.get(1).positions == []
    assert repository._path.read_bytes() == before


def test_bad_stored_parent_name_is_data_error(repository):
    from stock_tracker.exceptions import PersistenceDataError
    repository.create(portfolio(1))
    with sqlite3.connect(repository._path) as connection:
        connection.execute("UPDATE portfolios SET name=' '")
    with pytest.raises(PersistenceDataError):
        repository.get(1)


def test_mid_save_and_create_failure_rollback_every_row(repository, monkeypatch):
    from stock_tracker.exceptions import PersistenceError
    import stock_tracker.persistence.sqlite_portfolios as module
    original = repository.create(portfolio(1, "Original", [position()]))
    before = repository._path.read_bytes()
    real_insert = module._insert_positions
    def failing(connection, candidate):
        real_insert(connection, candidate)
        raise sqlite3.OperationalError("secret path and SQL")
    monkeypatch.setattr(module, "_insert_positions", failing)
    for operation, candidate in ((repository.save, portfolio(1, "Changed", [position(quantity="10")])),
                                 (repository.create, portfolio(2, "New", [position()]))):
        with pytest.raises(PersistenceError) as failure:
            operation(candidate)
        assert str(failure.value) == "Local storage operation failed."
        assert failure.value.__suppress_context__
        assert failure.value.__cause__ is None
        assert repository._path.read_bytes() == before
    assert repository.get(1).name == original.name
    assert repository.get(2) is None


def test_initial_creation_failure_rolls_back_schema_and_version(repository, monkeypatch):
    from stock_tracker.exceptions import PersistenceError
    import stock_tracker.persistence.sqlite_portfolios as module
    def failing(*args):
        raise sqlite3.OperationalError("injected")
    monkeypatch.setattr(module, "_insert_positions", failing)
    with pytest.raises(PersistenceError):
        repository.create(portfolio())
    with sqlite3.connect(repository._path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (0,)
        assert connection.execute("SELECT name FROM sqlite_schema").fetchall() == []


@pytest.mark.parametrize("kind", ["future", "unversioned", "corrupt"])
def test_unsupported_database_refused_without_changes(repository, kind):
    from stock_tracker.exceptions import PersistenceError
    if kind == "corrupt":
        repository._path.write_bytes(b"not a database")
    else:
        repository.create(portfolio())
        with sqlite3.connect(repository._path) as connection:
            connection.execute("PRAGMA user_version=" + ("99" if kind == "future" else "0"))
    before = repository._path.read_bytes()
    for operation in (lambda: repository.get(1), repository.list,
                      lambda: repository.create(portfolio()), lambda: repository.save(portfolio(1)),
                      lambda: repository.delete(1)):
        with pytest.raises(PersistenceError):
            operation()
        assert repository._path.read_bytes() == before


def test_missing_parent_and_invalid_path_fail_safely(tmp_path):
    from stock_tracker.exceptions import PersistenceError, PersistenceValidationError
    from stock_tracker.persistence.sqlite_portfolios import SQLitePortfolioRepository
    with pytest.raises(PersistenceValidationError):
        SQLitePortfolioRepository("file.sqlite3")
    repository = SQLitePortfolioRepository(tmp_path / "absent" / "state.sqlite3")
    for operation in (repository.list, lambda: repository.get(1),
                      lambda: repository.create(portfolio()), lambda: repository.delete(1)):
        with pytest.raises(PersistenceError):
            operation()
    assert not repository._path.parent.exists()


def test_source_repository_restart_is_local_without_pickle(tmp_path):
    root = Path(__file__).resolve().parents[1]
    for mode in ("write", "read"):
        probe = subprocess.run(
            [sys.executable, "-I", str(root / "tests" / "portfolio_repository_probe.py"),
             str(root / "src"), str(tmp_path / "source-restart.sqlite3"), mode],
            cwd=tmp_path, capture_output=True, text=True,
        )
        assert probe.returncode == 0, probe.stderr
        assert probe.stdout == probe.stderr == ""
