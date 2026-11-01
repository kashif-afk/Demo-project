"""TC1-TC12. Every test runs against both versions: [faulty] and [fixed].

Tests marked `regression` must FAIL on faulty and PASS on fixed. All others must pass on both.
"""

import importlib

import pytest

from fixtures import RUN_AT, assert_paid_once, task, tasks
from ledger import Ledger, SimulatedCrash
from notifier import MockNotifier


@pytest.fixture(params=["faulty", "fixed"])
def settle(request):
    return importlib.import_module(f"settle_{request.param}").settle


@pytest.fixture
def ledger():
    return Ledger()


@pytest.fixture
def notifier():
    return MockNotifier()


def test_tc1_happy_path_pays_and_notifies_each_task(settle, ledger, notifier):
    result = settle(tasks("T-1", "T-2", "T-3"), RUN_AT, ledger, notifier)

    assert result["paid"] == ["T-1", "T-2", "T-3"]
    assert notifier.sent == ["T-1", "T-2", "T-3"]
    assert_paid_once(ledger, ["T-1", "T-2", "T-3"])


@pytest.mark.parametrize("completed_at, included", [
    pytest.param("2026-10-19T00:00:00Z", True, id="tc2-lower-bound-included"),
    pytest.param("2026-10-26T00:00:00Z", False, id="tc3-upper-bound-excluded"),
    pytest.param("2026-10-25T23:59:59Z", True, id="tc4-just-inside"),
    pytest.param("2026-10-26T04:59:00+05:00", True, id="tc5-plus5-is-sunday-2359Z"),
    pytest.param("2026-10-26T05:00:00+05:00", False, id="tc6-plus5-is-monday-0000Z"),
])
def test_tc2_to_tc6_window_boundaries_and_timezones(settle, ledger, notifier, completed_at, included):
    result = settle([task("T-1", completed_at)], RUN_AT, ledger, notifier)

    assert result["paid"] == (["T-1"] if included else [])
    assert ledger.total() == (10 if included else 0)


@pytest.mark.regression
def test_tc7_duplicate_task_id_in_input_is_paid_once(settle, ledger, notifier):
    result = settle([task("T-1"), task("T-1")], RUN_AT, ledger, notifier)

    assert result["duplicate_input"] == ["T-1"]
    assert_paid_once(ledger, ["T-1"])


@pytest.mark.regression
def test_tc8_retry_after_crash_pays_each_task_once(settle, ledger, notifier):
    batch = tasks("T-1", "T-2", "T-3", "T-4")
    with pytest.raises(SimulatedCrash):
        settle(batch, RUN_AT, ledger, notifier, crash_after=2)
    assert ledger.total() == 20  # T-1 and T-2 paid before the crash

    settle(batch, RUN_AT, ledger, notifier)  # the scheduler retries the run

    assert_paid_once(ledger, ["T-1", "T-2", "T-3", "T-4"])  # total 40


@pytest.mark.regression
def test_tc9_rerun_of_finished_run_pays_nothing(settle, ledger, notifier):
    batch = tasks("T-1", "T-2", "T-3", "T-4")
    settle(batch, RUN_AT, ledger, notifier)

    second = settle(batch, RUN_AT, ledger, notifier)

    assert second["paid"] == []
    assert second["already_paid"] == ["T-1", "T-2", "T-3", "T-4"]
    assert_paid_once(ledger, ["T-1", "T-2", "T-3", "T-4"])


@pytest.mark.regression
def test_tc10_notification_failure_keeps_payouts(settle, ledger):
    notifier = MockNotifier(fail=True)

    result = settle(tasks("T-1", "T-2", "T-3"), RUN_AT, ledger, notifier)

    assert result["notify_failed"] == ["T-1", "T-2", "T-3"]
    assert notifier.sent == []
    assert_paid_once(ledger, ["T-1", "T-2", "T-3"])  # no rollback


def test_tc11_failed_payout_sends_no_notification(settle, notifier):
    ledger = Ledger(fail_for={"T-2"})

    result = settle(tasks("T-1", "T-2"), RUN_AT, ledger, notifier)

    assert result["payout_failed"] == ["T-2"]
    assert notifier.sent == ["T-1"]
    assert_paid_once(ledger, ["T-1"])


def test_tc12_timestamp_without_offset_is_rejected(settle, ledger, notifier):
    result = settle([task("T-1", "2026-10-21T12:00:00")], RUN_AT, ledger, notifier)

    assert result["rejected"] == {"T-1": "timestamp has no UTC offset: '2026-10-21T12:00:00'"}
    assert ledger.total() == 0
    assert notifier.sent == []
