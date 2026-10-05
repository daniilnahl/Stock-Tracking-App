"""Repository contracts independent of database, filesystem and presentation."""

from typing import Protocol

from stock_tracker.domain import Portfolio

from .models import WatchlistRecord


class PortfolioRepository(Protocol):
    """Explicit aggregate CRUD; implementation owns ID allocation and transactions."""

    def create(self, portfolio: Portfolio) -> Portfolio: ...

    def get(self, portfolio_id: int) -> Portfolio | None: ...

    def list(self) -> list[Portfolio]: ...

    def save(self, portfolio: Portfolio) -> None: ...

    def delete(self, portfolio_id: int) -> bool: ...


class WatchlistRepository(Protocol):
    """Independent ordered watchlists, never implicitly converted into Portfolios."""

    def get(self, namespace: str) -> WatchlistRecord | None: ...

    def list(self) -> list[WatchlistRecord]: ...

    def save(self, record: WatchlistRecord) -> None: ...
