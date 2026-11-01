> Draft prepared with Claude Code (2026-11-01). Review it and rewrite it in your own words before submitting, then delete this line.

# intent.md — Why this problem?

Fictional assessment case. All data is synthetic. No live financial system, real money or real customer data is involved.

## The flow

Every Tuesday 09:00 UTC a job pays **10 test credits** for each task completed in the previous week (Mon 00:00 UTC inclusive to Mon 00:00 UTC exclusive). Each task ID is paid once; a retry must not pay again. A notification goes out only after a successful payout, and a notification failure must not reverse the payout.

## Problems considered

Scores 1–5. Impact: 5 = worst for users or the business. Likelihood: 5 = most likely. Effort: 5 = cheapest to test and fix.

| # | Problem | Impact | Likelihood | Effort | Total |
|---|---|---|---|---|---|
| **P1** | **Re-run after a crash or retry pays the same task twice** (duplicate task IDs in the input folded in) | 5 | 4 | 4 | **13** |
| P2 | Notification failure rolls back a payout that already happened | 4 | 3 | 4 | 11 |
| P3 | Task completed exactly at Monday 00:00 UTC lands in the wrong week (`<=` instead of `<`) | 3 | 3 | 5 | 11 |
| P4 | Timestamp with a non-UTC offset is compared as if it were UTC, so the task moves weeks | 3 | 3 | 4 | 10 |
| P5 | Notification sent for a payout that failed ("you were paid" when you were not) | 3 | 2 | 4 | 9 |
| P6 | Timestamp without any offset is guessed as local time instead of rejected | 2 | 2 | 5 | 9 |

**Uncertainty:** these scores are my estimates from reasoning about the flow. There is no incident history behind them, and none is claimed.

## Why P1 ranked first

- **Direct money loss.** Every duplicate payout is money the business did not intend to pay.
- **Silent.** The person paid twice does not complain. It only shows up in reconciliation, if anyone reconciles.
- **Recurring by nature.** Batch jobs are retried after timeouts and crashes. Without a "paid once" check, every retry pays again, so the failure returns whenever the infrastructure is unhealthy.
- **Cheap to prevent.** A per-task check before paying plus a few regression tests stop it permanently.

P2–P6 are still covered by test cases (TC2–TC6, TC10–TC12), just not as the deep dive.

## Who is affected

- **Finance / operations:** they must find and claw back overpayments.
- **The business:** loses budget on every retry.
- **People being paid:** overpayments clawed back later, and duplicate "you were paid" messages, damage trust.

## Evidence

A reproduction on a local fixture, not production data. On the faulty version, a crash after 2 of 4 payouts followed by a retry pays **60** instead of **40** (T-1 and T-2 paid twice). See [docs/evidence-faulty.txt](docs/evidence-faulty.txt) and [docs/defect-report.md](docs/defect-report.md).

## Intended value

A regression check that **stops the failure from coming back**: tests that fail on the faulty version, pass on the fix, and run in CI so a regression blocks the release. Plus a defect report and a go / no-go decision someone else can act on.

## Non-goals

Real scheduler, real payment provider, real notification service, account lifecycle (closed or suspended accounts), admin changes to the window or amount, concurrency, performance.
