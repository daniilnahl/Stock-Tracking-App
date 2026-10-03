"""Developer scratch script, not an automated test.

Run explicitly with ``python test.py`` after configuring FMP_API_KEY locally.
This makes live market-data requests; automated tests must not run main().
"""


def main():
    from config import ConfigurationError, load_configuration, require_api_key

    try:
        api_key = require_api_key(load_configuration().api_key)
    except ConfigurationError as error:
        raise SystemExit(str(error)) from None

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
