"""Settlement window: previous Monday 00:00 UTC (inclusive) to the following Monday 00:00 UTC (exclusive)."""

from datetime import datetime, timedelta, timezone


def parse_utc(value: str) -> datetime:
    """Parse an ISO 8601 timestamp and convert it to UTC. Timestamps without an offset are rejected."""
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError(f"not a valid ISO 8601 timestamp: {value!r}") from None
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp has no UTC offset: {value!r}")
    return parsed.astimezone(timezone.utc)


def settlement_window(run_at: datetime) -> tuple[datetime, datetime]:
    """Return (start, end) for a run. A Tuesday 09:00 UTC run settles the 7 days before Monday 00:00 UTC."""
    if run_at.tzinfo is None:
        raise ValueError("run_at has no UTC offset")
    run_at = run_at.astimezone(timezone.utc)
    end = (run_at - timedelta(days=run_at.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return end - timedelta(days=7), end


def in_window(at: datetime, start: datetime, end: datetime) -> bool:
    return start <= at < end
