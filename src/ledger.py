"""In-memory payout ledger. Writing a payout row IS the payment: there is no separate credit step."""

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime

CREDITS_PER_TASK = 10


class PayoutError(Exception):
    """The payment was rejected (simulated)."""


class SimulatedCrash(Exception):
    """The settlement job died part-way through a run (simulated)."""


@dataclass(frozen=True)
class Payout:
    task_id: str
    user_id: str
    amount: int
    window_start: datetime


class Ledger:
    def __init__(self, fail_for: set[str] | None = None):
        self.payouts: list[Payout] = []
        self.fail_for = fail_for or set()  # task IDs whose payment is rejected

    def pay(self, payout: Payout) -> None:
        """Write a payout with no uniqueness check."""
        if payout.task_id in self.fail_for:
            raise PayoutError(f"payment rejected for {payout.task_id}")
        self.payouts.append(payout)

    def pay_once(self, payout: Payout) -> bool:
        """Write a payout unless (task_id, window_start) is already paid. Returns False if it was."""
        if self.has_paid(payout.task_id, payout.window_start):
            return False
        self.pay(payout)
        return True

    def has_paid(self, task_id: str, window_start: datetime) -> bool:
        return any(p.task_id == task_id and p.window_start == window_start for p in self.payouts)

    @contextmanager
    def transaction(self):
        """Payouts written inside the block are undone if the block raises."""
        saved = len(self.payouts)
        try:
            yield
        except BaseException:
            del self.payouts[saved:]
            raise

    def total(self) -> int:
        return sum(p.amount for p in self.payouts)

    def times_paid(self, task_id: str) -> int:
        return sum(p.task_id == task_id for p in self.payouts)
