"""Weekly settlement, FAULTY version (deliberate defects for the QA demo).

Defects:
1. Pays every qualifying task it sees: no check of earlier payouts, no de-duplication of task IDs.
2. Sends the notification before the payout commits, inside one transaction,
   so a notification failure rolls the payout back.
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

        try:
            with ledger.transaction():
                ledger.pay(Payout(task_id, task["user_id"], CREDITS_PER_TASK, start))  # defect 1
                notifier.send(task["user_id"], task_id, CREDITS_PER_TASK)  # defect 2
        except PayoutError:
            result["payout_failed"].append(task_id)
            continue
        except NotificationError:
            result["notify_failed"].append(task_id)
            continue
        result["paid"].append(task_id)
        result["notified"].append(task_id)

        if crash_after == len(result["paid"]):
            raise SimulatedCrash(f"job crashed after {crash_after} payouts")

    return result
