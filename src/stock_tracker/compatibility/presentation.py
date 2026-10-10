"""Legacy display and genuine historical observation charts."""

from datetime import date
from decimal import Decimal
from math import isfinite

from stock_tracker.compatibility import history_operations
from stock_tracker.exceptions import MarketDataUnavailableError

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, DayLocator


def format_return(ratio: Decimal | None) -> str:
    """Convert a numeric ratio to legacy percentage-point text at display only."""
    if ratio is None:
        return "-"
    displayed = format(ratio * 100, ".2f").rstrip("0").rstrip(".")
    return displayed if "." in displayed else displayed + ".0"


def graph_performance(self, *, start: date | None = None, end: date | None = None):
    """Plot only validated raw closes on their observed exchange-session dates."""
    start, end, bars = history_operations.get_price_history_with_range(self, start=start, end=end)
    prices = []
    for bar in bars:
        try:
            price = float(bar.close)
        except OverflowError:
            raise MarketDataUnavailableError() from None
        if not isfinite(price) or bar.close > 0 and price == 0:
            raise MarketDataUnavailableError()
        prices.append(price)
    dates = [bar.date for bar in bars]
    plt.figure(figsize=(10, 6))
    plt.plot(dates, prices, marker='o', linestyle='None', label='Raw historical close')
    axes = plt.gca()
    axes.xaxis.set_major_locator(DayLocator(interval=max(1, (dates[-1] - dates[0]).days // 6 + 1)))
    axes.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    plt.title(f'{bars[0].symbol} — Raw historical close\nRequested: {start.isoformat()} to {end.isoformat()}')
    plt.xlabel('Exchange session date')
    plt.ylabel('Price (currency unavailable)')
    plt.figtext(0.5, 0.02,
                f'Observed: {dates[0].isoformat()} to {dates[-1].isoformat()}; {len(bars)} observations\n'
                'Unadjusted prices; splits may appear as discontinuities.', ha='center')
    plt.subplots_adjust(bottom=0.20)
    plt.grid(True)
    plt.legend()
    plt.show()

def format_mcap(mcap: float):
    """
        Formats a market cap value into a readable string with appropriate units.
        Market caps in trillions are formatted with a "T" suffix, while those in billions are formatted with a "B" suffix.

        Args:
            mcap (float): unformatted market cap.

        Returns:
            str: The formatted market cap as a string (e.g., "1.23T" for trillions or "456.789B" for billions).
        """
    if abs(mcap) >= 1000000000000:
        return f'{mcap / 1000000000000:.2f}T'
    else:
        return f'{mcap / 1000000000:.3f}B'
