"""Fixed ADR-0016 native Finnhub bounds, without environment or network IO."""

from collections.abc import Callable
from datetime import datetime

from config import require_finnhub_api_key
from .eps import UpcomingEpsProvider
from .finnhub import FinnhubUpcomingEpsProvider
from .finnhub_transport import FinnhubHttpTransport


def create_upcoming_eps_provider(api_key: str | None, *, clock: Callable[[], datetime]) -> UpcomingEpsProvider:
    return FinnhubUpcomingEpsProvider(
        api_key=require_finnhub_api_key(api_key), clock=clock,
        transport=FinnhubHttpTransport(max_response_bytes=262144),
        timeout_seconds=5.0, max_response_bytes=262144, max_rows=128,
    )
