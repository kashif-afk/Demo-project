# Release checklist — weekly settlement

Results from the captured runs on 2026-11-01 ([evidence-faulty.txt](evidence-faulty.txt), [evidence-fixed.txt](evidence-fixed.txt)). CI passed on GitHub: [run 41310774366](https://github.com/kashif-afk/Demo-project/actions/runs/41310774366).

## Gates

| # | Gate | Check | Faulty (current release) | Fixed |
|---|---|---|---|---|
| G1 | Retry after crash pays each task once | TC8, UI4 | FAIL | PASS |
| G2 | Re-run pays 0 | TC9, UI3 | FAIL | PASS |
| G3 | Duplicate task ID paid once | TC7 | FAIL | PASS |
| G4 | Invariant: total = 10 × unique qualifying tasks | in every payout test | FAIL | PASS |
| G5 | Cut-off and timezone | TC2–TC6, UI2 | PASS | PASS |
| G6 | Notification failure keeps the payout | TC10, UI5 | FAIL | PASS |
| G7 | No notification for a failed payout | TC11 | PASS | PASS |
| G8 | Timestamp without offset rejected | TC12 | PASS | PASS |
| G9 | CI: regression tests fail on faulty, pass on fixed | `.github/workflows/ci.yml` | gate verified locally | PASS ([CI run](https://github.com/kashif-afk/Demo-project/actions/runs/41310774366)) |

## Remaining gaps (not covered)

- **Lost notification after a crash:** if the job dies after paying a task but before notifying, the retry skips that task as already paid, so that person is never notified (T-2 in UI4 on the fixed version). Needs an outbox or a "notified" flag.
- **"Paid once" is per window:** the same task ID resubmitted in a later week with a new `completed_at` would be paid again.
- **No concurrency test:** two runs at the same time are not tested; the in-memory ledger has no locking.
- **No schedule check:** nothing checks that the job really runs on Tuesday 09:00 UTC (no real scheduler).
- Closed or suspended accounts, admin changes to amount or window, daylight saving beyond one offset test: out of scope.

## Decision

- **Faulty (current release): NO-GO.** G1, G2, G3, G4 and G6 fail: retries overpay, and a notification outage reverses payouts.
- **Fixed: GO.** CI is green on main ([run](https://github.com/kashif-afk/Demo-project/actions/runs/41310774366)). The gaps above are known risks for the next iteration, not blockers for this fix.
