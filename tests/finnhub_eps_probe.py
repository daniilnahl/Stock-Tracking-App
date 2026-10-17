"""Cold source/wheel EPS adapter smoke under proven IO denial guards."""

import builtins
from contextlib import ExitStack
from datetime import date, datetime, timezone
from decimal import Decimal
import importlib
import io
import os
from pathlib import Path
import socket
import sys
from types import SimpleNamespace
import urllib.request
from unittest.mock import patch


SYNTHETIC_CREDENTIAL = "synthetic-probe-credential"


def denied(*args, **kwargs):
    raise AssertionError("EPS probe denied external work")


class DeniedEnvironment:
    __getitem__ = get = __iter__ = __contains__ = keys = items = values = denied


def main(root):
    with ExitStack() as guards:
        for target, attribute in (
            (builtins, "open"), (io, "open"), (io, "FileIO"), (os, "open"), (os, "getenv"),
            (socket, "getaddrinfo"), (socket, "create_connection"),
            (socket.socket, "connect"), (socket.socket, "connect_ex"), (socket.socket, "sendto"),
            (urllib.request, "urlopen"), (urllib.request.OpenerDirector, "open"),
        ):
            guards.enter_context(patch.object(target, attribute, denied))
        guards.enter_context(patch.object(os, "environ", DeniedEnvironment()))
        for control in (
            lambda: open("eps-probe", "w"), lambda: os.getenv("EPS_PROBE"),
            lambda: os.environ["EPS_PROBE"], lambda: socket.getaddrinfo("example.invalid", 443),
            lambda: urllib.request.urlopen("https://example.invalid"),
        ):
            try:
                control()
            except AssertionError:
                pass
            else:
                raise AssertionError("EPS guard negative control failed")
        modules = [importlib.import_module("stock_tracker.providers." + name)
                   for name in ("eps", "finnhub", "finnhub_transport")]
        for module in modules:
            assert Path(module.__file__).resolve().is_relative_to(root)
        for name in ("config", "stock", "stock_tracker.providers.fmp", "stock_tracker.providers.factory"):
            assert name not in sys.modules
        eps, finnhub, transport = modules
        native = transport.FinnhubHttpTransport(max_response_bytes=2000)
        finnhub.FinnhubUpcomingEpsProvider(api_key=SYNTHETIC_CREDENTIAL, transport=native,
            clock=denied, timeout_seconds=1.0, max_response_bytes=2000, max_rows=3)
        calls = []
        from stock_tracker.providers.transport import HttpResponse
        stamp = datetime(2026, 10, 16, tzinfo=timezone.utc)
        def get(url, **kwargs):
            calls.append((url, kwargs))
            return HttpResponse(200, {}, b'''{"earningsCalendar":[{"symbol":"TEST","date":"2026-10-20", "year":2026,"quarter":3,"epsActual":null,"epsEstimate":1.250000000000000001}]}''')
        provider = finnhub.FinnhubUpcomingEpsProvider(api_key=SYNTHETIC_CREDENTIAL,
            transport=SimpleNamespace(get=get), clock=lambda: stamp,
            timeout_seconds=1.0, max_response_bytes=2000, max_rows=3)
        result, = provider.get_upcoming_eps("TEST", start=date(2026, 10, 17),
                                           end=date(2026, 10, 31), analysis_date=date(2026, 10, 16))
        assert isinstance(result, eps.UpcomingEpsEstimate)
        assert result.estimate == Decimal("1.250000000000000001")
        assert result.currency is result.share_basis is result.published_at is result.fiscal_period_end is None
        assert result.source_field == "epsEstimate" and result.accounting_basis == "non-GAAP"
        assert len(calls) == 1 and "synthetic-probe-credential" not in calls[0][0]


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(root))
    main(root)
