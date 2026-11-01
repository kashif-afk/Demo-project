# DEF-001 — Re-running the weekly settlement pays the same task again

| Field | Value |
|---|---|
| Component | Weekly settlement job, `src/settle_faulty.py` (current release) |
| Found by | Regression tests TC7, TC8, TC9 and Playwright UI3, UI4 |
| Severity | **Critical** |
| Priority | **P1: blocks release** |
| Environment | Local fixture, Python 3.14.3, synthetic data, run time Tue 2026-10-27 09:00 UTC |
| Status | Fixed in `src/settle_fixed.py`, verified |

## Summary

When the settlement job crashes part-way and the scheduler runs it again, every task paid before the crash is paid a second time. The same happens when a finished run is repeated, or when a task ID appears twice in the input.

## Steps to reproduce

**In the browser**
1. `python src/app.py`, then open http://127.0.0.1:8000
2. Version: **faulty (current release)**
3. Tick **Crash after 2 payouts**, click **Run settlement**. The run list shows "Crashed: job crashed after 2 payouts", and 20 are paid (T-1, T-2).
4. Untick the crash box and click **Run settlement** again (the scheduler's retry).

**With pytest**
```
python -m pytest -v -k "tc8 and faulty"
```

## Expected vs actual

| | Expected | Actual (faulty) |
|---|---|---|
| Total paid after crash + retry | 40 (4 tasks × 10) | **60** |
| Times T-1 and T-2 paid | 1 each | **2 each** |
| Page status | "OK: every task paid once, total 40." | "PROBLEM: paid 60, should be 40. Paid more than once: T-1, T-2." |
| Notifications | 1 per task | T-1 and T-2 notified twice |

## Severity rationale

- **Direct money loss**, proportional to how far the run got before crashing. A full re-run doubles the whole week.
- **Silent:** no error is raised, and the people overpaid have no reason to report it.
- **Recurring:** every crash, timeout or manual re-run triggers it again.

## Root cause

`settle_faulty.py` calls `ledger.pay()` for every qualifying task without checking whether that task ID was already paid for this window. It also does not de-duplicate task IDs in the input. Nothing in the run remembers what an earlier attempt already paid.

**Related defect found by the same suite (TC10, UI5):** the faulty version sends the notification inside the payout transaction, before it commits. When the notification service is down, the payout is rolled back. Fixed in the same change.

## Evidence

- [docs/evidence-faulty.txt](evidence-faulty.txt): 7 failed, 10 passed (exit 1)
- [docs/evidence-fixed.txt](evidence-fixed.txt): 17 passed (exit 0)

## Fix

In `settle_fixed.py`:
1. De-duplicate task IDs in the input.
2. Pay with `ledger.pay_once()`: unique key `(task_id, window_start)`. Check and write happen in one step, and the payout is a single ledger write, so a crash cannot leave a task paid but unrecorded.
3. Notify only after the payout is committed. A notification error is recorded as `notify_failed`, and the payout stays.

## Release checks that would have blocked this

1. **CI regression gate** (`.github/workflows/ci.yml`): every test marked `regression` must pass on the fixed version and fail on the faulty one. TC8 failing blocks the merge.
2. **Idempotency test:** a second run pays 0 (TC9, UI3).
3. **Invariant check** in every payout test: each task paid once, total = 10 × unique qualifying tasks.
4. **Browser check:** Playwright UI4 replays the crash and retry through the page.
5. **Code review rule:** any payout path must check "already paid" and write the payout in one step.
