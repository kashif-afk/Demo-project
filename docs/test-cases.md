# Test cases — flow map, assumptions, results

All data is **synthetic**. Run time: Tue 2026-10-27 09:00 UTC. Window: Mon 2026-10-19 00:00Z (inclusive) to Mon 2026-10-26 00:00Z (exclusive).
Results below are copied from the captured runs, not predicted: [evidence-faulty.txt](evidence-faulty.txt) and [evidence-fixed.txt](evidence-fixed.txt).

## Flow map

```
Tasks in ──► parse completed_at to UTC ──(no offset)──► REJECTED with a clear error
                     │
                     ▼
           status completed AND start <= at < end ? ──(no)──► not qualifying
                     │ yes
                     ▼
           task ID already seen in this input ? ──(yes)──► skipped: duplicate input
                     │ no
                     ▼
           already paid for this window (ledger) ? ──(yes)──► skipped: already paid
                     │ no
                     ▼
           PAY = one ledger write ──(rejected)──► payout_failed, no notification
                     │ committed
                     ▼
           NOTIFY ──(service down)──► notify_failed, payout stays
                     │
                     ▼
                  notified
```

Where it breaks on the faulty version: it has no "already seen" and no "already paid" step, and it notifies *before* the payout commits, inside one transaction, so a notification failure undoes the payout.

## Assumptions

| ID | Assumption |
|---|---|
| A1 | A task qualifies if status is `completed` and `completed_at` is inside the window. |
| A2 | `completed_at` may have any UTC offset and is converted to UTC. A timestamp with no offset is rejected, never guessed. |
| A3 | **Account changes:** closed or suspended accounts are out of scope; every account in the fixture is active. |
| A4 | **Admin settings:** no admin setting changes the window or the 10-credit amount; both are constants. |
| A5 | A retry means the same run executed again after a crash or timeout, with the same input. |
| A6 | The ledger is an in-memory list. "Already paid" means the same task ID was paid for the same window. |

## Engine tests (pytest, every case runs on both versions)

| ID | Category | Input | Expected | Faulty | Fixed |
|---|---|---|---|---|---|
| TC1 | Happy path | 3 completed tasks inside the window | 30 credits, 3 payouts, 3 notifications | PASS | PASS |
| TC2 | Cut-off (lower) | `2026-10-19T00:00:00Z` | included, 10 credits | PASS | PASS |
| TC3 | Cut-off (upper) | `2026-10-26T00:00:00Z` | excluded, 0 credits (next window) | PASS | PASS |
| TC4 | Cut-off (just inside) | `2026-10-25T23:59:59Z` | included | PASS | PASS |
| TC5 | Timezone | `2026-10-26T04:59:00+05:00` (= Sun 23:59Z) | included | PASS | PASS |
| TC6 | Timezone | `2026-10-26T05:00:00+05:00` (= Mon 00:00Z) | excluded | PASS | PASS |
| TC7 | Duplicate input | same task ID twice in the input | paid once, 10 credits | **FAIL** (paid twice) | PASS |
| TC8 | **Retry after crash (selected failure)** | 4 tasks, crash after 2 payouts, run again | each task paid once, total 40 | **FAIL** (60) | PASS |
| TC9 | Re-run of a finished run | run twice, no crash | second run pays 0 | **FAIL** | PASS |
| TC10 | Partial failure (notification) | notification service down for every call | 3 payouts stay, 3 failures recorded, no rollback | **FAIL** (payouts rolled back) | PASS |
| TC11 | Partial failure (payout) | payout rejected for T-2 | no notification for T-2, T-1 paid and notified | PASS | PASS |
| TC12 | Invalid input | `2026-10-21T12:00:00` (no offset) | rejected: "timestamp has no UTC offset", nothing paid | PASS | PASS |

Every payout test also checks the invariant: **each task paid exactly once, total = 10 × unique qualifying tasks** (`assert_paid_once` in [tests/fixtures.py](../tests/fixtures.py)).

## Browser tests (Playwright, every case runs on both versions)

The demo page ([src/app.py](../src/app.py)) runs the same settlement code on 6 sample tasks. T-1 to T-4 qualify (expected total 40); T-3 is logged at +05:00 (= Sun 23:59Z). T-5 (`Z`) and T-6 (`+05:00`) both land exactly on Mon 00:00Z and do not.

| ID | Category | Steps | Expected | Faulty | Fixed |
|---|---|---|---|---|---|
| UI1 | Happy path | Run settlement | "OK: every task paid once, total 40.", 4 payout rows, T-1..T-4 notified | PASS | PASS |
| UI2 | Cut-off | Run settlement | T-5 shown "In window? no", never in payouts | PASS | PASS |
| UI3 | Retry | Run, then Run again | second run "Paid nothing · skipped already paid T-1, T-2, T-3, T-4" | **FAIL** | PASS |
| UI4 | Retry after crash | Tick "Crash after 2 payouts", Run (20 paid), untick, Run | "OK: every task paid once, total 40." | **FAIL** (60, T-1 and T-2 twice) | PASS |
| UI5 | Partial failure (notification) | Tick "Notification service down", Run | total 40, notifications "none", run shows the 4 failures | **FAIL** (total 0) | PASS |
| UI6 | Timezone | Run settlement | T-3 (`+05:00`, Sun 23:59Z) "yes" and paid; T-6 (`+05:00`, Mon 00:00Z) "no" and not paid | PASS | PASS |
| UI7 | Duplicate input | Tick "T-2 sent twice in the input", Run | one T-2 payout row, run shows "skipped duplicate input T-2", total 40 | **FAIL** (T-2 paid twice) | PASS |

## Coverage of the six required categories

| Category | Cases |
|---|---|
| Happy path | TC1, UI1 |
| Cut-off boundary | TC2, TC3, TC4, UI2 |
| Timezone conversion | TC5, TC6, TC12, UI6 |
| Duplicate input | TC7, UI7 |
| Retry | TC8, TC9, UI3, UI4 |
| Partial failure | TC10, TC11, UI5 |

## Totals

12 engine cases + 7 browser cases = 19 checks per version, 38 in one run.
- **Faulty:** 8 failed (TC7, TC8, TC9, TC10, UI3, UI4, UI5, UI7 — exactly the tests marked `regression`), 11 passed. Exit 1.
- **Fixed:** 19 passed. Exit 0.
