"""Deterministic app-local attempts, expiry, cooldown and lease ownership."""

from concurrent.futures import ThreadPoolExecutor
import threading

import pytest

from stock_tracker.api.eps_budget import EpsBudget
from stock_tracker.api.errors import ApiFailure


@pytest.fixture
def rig():
    now = [0.0]
    return now, EpsBudget(lambda: now[0])


def refused(budget, code="eps_rate_limited"):
    with pytest.raises(ApiFailure) as caught:
        budget.reserve()
    assert caught.value.code == code


def test_startup_exact_boundary_and_restart_quiet_time(rig):
    now, budget = rig
    refused(budget)
    now[0] = 59.999999
    refused(budget)
    now[0] = 60.0
    lease = budget.reserve()
    refused(budget)
    lease.complete()
    lease.complete()  # Completion is idempotent, never releases another lease.
    replacement = budget.reserve()
    lease.complete()
    refused(budget)
    replacement.complete()
    restarted = EpsBudget(lambda: now[0])
    refused(restarted)
    now[0] = 120.0
    restarted.reserve().complete()


def test_rolling_thirty_attempts_no_refund_and_age_sixty_expires(rig):
    now, budget = rig
    now[0] = 60.0
    for _ in range(30):
        budget.reserve().complete()
    refused(budget)
    now[0] = 119.999999
    refused(budget)
    assert len(budget._attempts) == 30
    now[0] = 120.0
    budget.reserve().complete()
    assert list(budget._attempts) == [120.0]


def test_trailing_window_does_not_reset_as_a_fixed_minute(rig):
    now, budget = rig
    now[0] = 60.0
    budget.reserve().complete()
    now[0] = 90.0
    for _ in range(29):
        budget.reserve().complete()
    now[0] = 120.0
    budget.reserve().complete()
    refused(budget)
    assert len(budget._attempts) == 30


def test_upstream_cooldown_begins_at_receipt_not_reservation(rig):
    now, budget = rig
    now[0] = 60.0
    lease = budget.reserve()
    now[0] = 65.0
    lease.complete(rate_limited=True)
    now[0] = 124.999999
    refused(budget)
    now[0] = 125.0
    budget.reserve().complete()


def test_clock_is_sampled_under_lock_and_concurrent_leases_are_exclusive():
    now, entered, release = [0.0], threading.Event(), threading.Event()
    calls = []
    def clock():
        calls.append(threading.get_ident())
        if len(calls) == 2:
            entered.set()
            assert release.wait(5)
        return now[0]
    budget = EpsBudget(clock)
    now[0] = 60.0
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(budget.reserve)
        assert entered.wait(5)
        second = executor.submit(budget.reserve)
        assert len(calls) == 2
        release.set()
        lease = first.result(5)
        with pytest.raises(ApiFailure) as caught:
            second.result(5)
        assert caught.value.code == "eps_rate_limited"
        lease.complete()
    assert len(budget._attempts) == 1


@pytest.mark.parametrize("bad", [None, True, 1, float("nan"), float("inf"), -1.0])
def test_bad_or_backward_clock_fails_closed_even_after_recovery(rig, bad):
    now, budget = rig
    now[0] = bad
    refused(budget, "provider_unavailable")
    now[0] = 120.0
    refused(budget, "provider_unavailable")


def test_broken_cooldown_clock_still_releases_active_lease_and_stays_closed(rig):
    now, budget = rig
    now[0] = 60.0
    lease = budget.reserve()
    now[0] = 59.0
    with pytest.raises(ApiFailure) as caught:
        lease.complete(rate_limited=True)
    assert caught.value.code == "provider_unavailable" and budget._active is None
    now[0] = 120.0
    refused(budget, "provider_unavailable")


def test_clock_exception_is_sanitized():
    def broken():
        raise RuntimeError("synthetic-private-clock-diagnostic")
    with pytest.raises(ApiFailure) as caught:
        EpsBudget(broken)
    assert caught.value.code == "provider_unavailable"
    assert "synthetic-private" not in str(caught.value) and caught.value.__suppress_context__
