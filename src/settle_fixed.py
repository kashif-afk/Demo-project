"""Weekly settlement, FIXED version.

- De-duplicates task IDs in the input.
- Skips any task already paid for this window (ledger unique key: task_id + window).
- The payout is one ledger write, so a crash cannot leave a task paid but unrecorded.
- Notifies only after the payout is committed; a notification failure is recorded, never rolled back.
"""

from datetime import datetime

from ledger import CREDITS_PER_TASK, Ledger, Payout, PayoutError, SimulatedCrash
from notifier import MockNotifier, NotificationError
from window import in_window, parse_utc, settlement_window


def settle(tasks: list[dict], run_at: datetime, ledger: Ledger, notifier: MockNotifier,
           crash_after: int | None = None) -> dict:
    """Settle one run. crash_after=N makes the job die after its Nth payout."""
    start, end = settlement_window(run_at)
    result = {"paid": [], "duplicate_input": [], "already_paid": [], "not_qualifying": [],
              "rejected": {}, "payout_failed": [], "notified": [], "notify_failed": []}
    seen: set[str] = set()

    for task in tasks:
        task_id = task["task_id"]
        try:
            completed_at = parse_utc(task["completed_at"])
        except ValueError as error:
            result["rejected"][task_id] = str(error)
            continue
        if task["status"] != "completed" or not in_window(completed_at, start, end):
            result["not_qualifying"].append(task_id)
            continue
        if task_id in seen:
            result["duplicate_input"].append(task_id)
            continue
        seen.add(task_id)

        try:
            if not ledger.pay_once(Payout(task_id, task["user_id"], CREDITS_PER_TASK, start)):
                result["already_paid"].append(task_id)
                continue
        except PayoutError:
            result["payout_failed"].append(task_id)
            continue
        result["paid"].append(task_id)

        if crash_after == len(result["paid"]):
            raise SimulatedCrash(f"job crashed after {crash_after} payouts")

        try:
            notifier.send(task["user_id"], task_id, CREDITS_PER_TASK)
            result["notified"].append(task_id)
        except NotificationError:
            result["notify_failed"].append(task_id)

    return result
