"""Legacy display and synthetic charts; real market history remains M4 work."""

from datetime import datetime, timedelta
from decimal import Decimal

import matplotlib.pyplot as plt


def format_return(ratio: Decimal | None) -> str:
    """Convert a numeric ratio to legacy percentage-point text at display only."""
    if ratio is None:
        return "-"
    displayed = format(ratio * 100, ".2f").rstrip("0").rstrip(".")
    return displayed if "." in displayed else displayed + ".0"


def graph_performance(self):
    """
        Plots an approximate graph of the stock's price performance over the past 5 years.

        The method calculates historical price points based on the stock's percentage change
        over various time intervals (e.g., 1 day, 5 days, 1 month, etc.). It then creates a line
        plot with dates on the x-axis and stock prices on the y-axis.

        Calculation details:
        - Historical prices are estimated using the formula: historical_price = current_price / (1 + percent_change / 100).
        - Time intervals considered: 1 day, 5 days, 1 month, 3 months, 6 months, 1 year, 3 years, 5 years.

        Graph details:
        - X-axis: Dates (from today to 5 years ago, spaced according to the time intervals).
        - Y-axis: Stock prices (in the same currency as `current_price`).
        """
    percent_changes = {'1D': float(self.price_1d), '5D': float(self.price_5d), '1M': float(self.price_30d), '3M': float(self.price_3m), '6M': float(self.price_6m), '1Y': float(self.price_1y), '3Y': float(self.price_3y), '5Y': float(self.price_5y)}
    time_intervals = {'1D': 1, '5D': 5, '1M': 30, '3M': 90, '6M': 180, '1Y': 365, '3Y': 1095, '5Y': 1825}
    historical_values = {0: float(self.current_price)}
    for period, days_num in time_intervals.items():
        historical_value = round(float(self.current_price) / (1 + percent_changes[period] / 100), 2)
        historical_values[days_num] = historical_value
    days_ago, prices = zip(*sorted(historical_values.items()))
    today = datetime.today()
    dates = [today - timedelta(days=days) for days in days_ago]
    plt.figure(figsize=(10, 6))
    plt.plot(dates, prices, marker='o', label='Stock Price')
    plt.title('Approximate 5-Year Performance')
    plt.xlabel('Date')
    plt.ylabel('Price (USD)')
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
