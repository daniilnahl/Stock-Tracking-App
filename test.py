"""Developer scratch script, not an automated test.

Run explicitly with ``python test.py`` after configuring MY_API_KEY locally.
This makes live market-data requests; automated tests must not run main().
"""


def main():
    import os

    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("MY_API_KEY")
    if not api_key:
        raise SystemExit("Set MY_API_KEY in your environment or local .env first.")

    from stock import Stock

    stock = Stock("AMD", api_key)
    stock.get_stock_info()

    # Research notes (provider endpoint names, without credential-bearing URLs):
    # industry P/E: industry-pe-snapshot
    # ROIC and market cap: key-metrics
    # EPS estimates: analyst-estimates; current EPS: earnings-calendar
    # Five-year revenue growth: financial-growth
    # Historical free cash flow is unavailable from the researched endpoints.


if __name__ == "__main__":
    main()
