"""Synthetic test data and the payout invariant. Window for every case: Mon 2026-10-19 00:00Z to Mon 2026-10-26 00:00Z."""

from datetime import datetime, timezone

from ledger import CREDITS_PER_TASK, Ledger

RUN_AT = datetime(2026, 10, 27, 9, 0, tzinfo=timezone.utc)  # Tuesday 09:00 UTC
INSIDE = "2026-10-21T12:00:00Z"  # Wednesday, mid-window


def task(task_id: str, completed_at: str = INSIDE, user_id: str = "U-1", status: str = "completed") -> dict:
    return {"task_id": task_id, "user_id": user_id, "status": status, "completed_at": completed_at}


def tasks(*task_ids: str) -> list[dict]:
    return [task(task_id, user_id=f"U-{n}") for n, task_id in enumerate(task_ids, start=1)]


def assert_paid_once(ledger: Ledger, task_ids: list[str]) -> None:
    """Invariant: every task paid exactly once, total = 10 x unique qualifying tasks."""
    times_paid = {task_id: ledger.times_paid(task_id) for task_id in task_ids}
    assert times_paid == {task_id: 1 for task_id in task_ids}
    assert ledger.total() == CREDITS_PER_TASK * len(set(task_ids))
