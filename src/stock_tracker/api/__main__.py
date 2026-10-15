"""Supported ``python -m stock_tracker.api`` entry point."""

from .launcher import main


if __name__ == "__main__":
    raise SystemExit(main())
