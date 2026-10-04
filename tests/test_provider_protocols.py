"""Transport-free fake capabilities under the accepted M2/M4 contract."""

from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
import subprocess
import sys


def test_independent_fake_providers_supply_current_and_history_capabilities():
    from stock_tracker.providers import (
        CompanyProfile, HistoricalMarketDataProvider, InstrumentIdentity, MarketDataProvider,
        PeriodChanges, PriceBar, Quote,
    )

    received = datetime(2020, 1, 2, tzinfo=timezone.utc)

    class CurrentFake:
        def resolve_symbol(self, symbol: str) -> InstrumentIdentity:
            return InstrumentIdentity(symbol, "NASDAQ", "Fictional company", "USD")

        def get_quote(self, symbol: str) -> Quote:
            return Quote(symbol, Decimal("120.123456789"), "NASDAQ", None, None, received)

        def get_company_profile(self, symbol: str) -> CompanyProfile:
            return CompanyProfile(symbol, "Fictional company", "NASDAQ", "USD", None,
                                  None, None, None, None, received)

        def get_period_changes(self, symbol: str) -> PeriodChanges:
            return PeriodChanges(symbol, Decimal("12.5"), None, None, None,
                                 None, None, None, None, None, received)

    class HistoryFake:
        def get_price_history(self, symbol: str, start: date, end: date) -> list[PriceBar]:
            assert start == end == date(2020, 1, 2)
            return [PriceBar(symbol, start, Decimal("100"), Decimal("120"), Decimal("99"),
                             Decimal("110"), None, None)]

    provider: MarketDataProvider = CurrentFake()
    history: HistoricalMarketDataProvider = HistoryFake()
    assert provider.resolve_symbol("AAPL").currency == "USD"
    assert provider.get_quote("AAPL").price == Decimal("120.123456789")
    assert provider.get_company_profile("AAPL").price is None
    assert provider.get_period_changes("AAPL").day_1 == Decimal("12.5")
    assert not hasattr(provider, "get_price_history")
    bars = history.get_price_history("AAPL", date(2020, 1, 2), date(2020, 1, 2))
    assert bars[0].close == Decimal("110")
    assert not hasattr(history, "get_quote")


def test_source_contract_imports_and_constructors_need_no_infrastructure(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-I", str(root / "tests" / "provider_contract_probe.py"), str(root / "src")],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
    assert list(tmp_path.iterdir()) == []
