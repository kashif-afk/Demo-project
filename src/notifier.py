"""Mock notifier: records "you were paid" messages, or fails every call when told to."""


class NotificationError(Exception):
    """The notification service is down (simulated)."""


class MockNotifier:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.sent: list[str] = []  # task IDs notified

    def send(self, user_id: str, task_id: str, amount: int) -> None:
        if self.fail:
            raise NotificationError(f"notification service down, {task_id} for {user_id} not sent")
        self.sent.append(task_id)
