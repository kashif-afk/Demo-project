> Draft prepared with Claude Code from the owner's directive (2026-11-01). Fill in the links, review, and rewrite in your own words before submitting, then delete this line.

# directive.md — Rewards Settlement: Prevent Double Payout on Retry

> Fictional assessment case. All data is synthetic. No live financial system, real money or real customer data is involved.

| Link | |
|---|---|
| Repository | https://github.com/kashif-afk/Demo-project |
| Quest Loom video | `<LOOM_URL>` |
| Career Path & Career Leverage video | `<CAREER_VIDEO_URL>` |

## 1. Objective

Find, reproduce, fix and guard against this failure:

**A settlement re-run after a partial failure (crash or retry) pays the same task twice.**

Deliver a runnable test project that shows the regression **failing** on the faulty implementation and **passing** on the fixed one.

## 2. Business rules (source of truth)

1. Settlement runs every Tuesday 09:00 UTC.
2. Window = previous Monday 00:00:00 UTC (inclusive) to the following Monday 00:00:00 UTC (exclusive).
3. Each qualifying completed task earns 10 test credits.
4. Each task ID is counted once, even if it appears twice in the input.
5. A retry or re-run must never create a second payout for a task.
6. A notification is sent only after a successful payout.
7. A notification failure must never reverse the payout.

## 3. Assumptions (label these in the final report)

- A task is "qualifying" if its status is `completed` and its `completed_at` falls inside the window.
- `completed_at` may arrive with any UTC offset; it is converted to UTC before comparison. Naive (no-offset) timestamps are rejected.
- Account changes (closed or suspended accounts) are out of scope; every account in the fixture is active.
- No admin setting changes the window or the 10-credit amount. These are constants.
- The ledger is an in-memory list, not a real database or gateway. "Already paid" = same task ID paid for the same window.

## 4. Scope

**In scope:** a settlement function, a payout ledger, a mock notifier, a faulty and a fixed implementation, automated engine tests, Playwright browser tests on a small local demo page, a defect report, a release checklist.

**Non-goals:** a real scheduler, a real payment gateway, a real notification provider, daylight saving edge cases beyond one timezone test, a production UI. (The demo page exists only so the flow can be tested and shown in a browser.)

## 5. Project structure

```
rewards-qa/
  directive.md
  intent.md
  README.md                # how to run
  requirements.txt         # pytest, pytest-playwright
  pytest.ini
  .github/workflows/ci.yml # release gate
  src/
    window.py          # computes window from run time, UTC-safe
    ledger.py          # payout ledger (pay_once: unique key on task_id + window)
    notifier.py        # mock notifier that can be told to fail
    settle_faulty.py   # naive version: no idempotency, notifies before commit
    settle_fixed.py    # fixed version
    app.py, index.html # local demo page (standard library only) for Playwright and the Loom
  tests/
    fixtures.py        # synthetic tasks + the paid-once invariant
    test_settlement.py # TC1-TC12, parametrised over faulty and fixed
    test_ui.py         # UI1-UI7, Playwright, parametrised over faulty and fixed
  docs/
    test-cases.md, defect-report.md, release-checklist.md
    effort-log.md
    evidence-faulty.txt, evidence-fixed.txt
```

Python 3.11+, pytest and pytest-playwright (Chromium). Nothing else.

## 6. Implementation requirements

**Faulty version (`settle_faulty.py`) must:**
- pay every qualifying task it sees, with no check of prior payouts
- not deduplicate task IDs
- be able to crash midway (injectable failure after N payouts)

**Fixed version (`settle_fixed.py`) must:**
- skip any `task_id` already in the ledger for that window
- deduplicate input task IDs before paying
- write the credit and the ledger entry together, so a crash cannot leave a task paid but unrecorded
- send the notification only after the payout commits
- catch notifier errors, record them as `notify_failed`, and never roll back the payout
- use `<` for the upper bound and `>=` for the lower bound

## 7. Test cases

Window used in all cases: Mon 2026-10-19 00:00Z to Mon 2026-10-26 00:00Z. Expected credits = 10 per unique qualifying task. Full table with results: [docs/test-cases.md](docs/test-cases.md).

| ID | Category | Input | Expected |
|----|----------|-------|----------|
| TC1 | Happy path | 3 completed tasks inside the window | 30 credits, 3 payouts, 3 notifications |
| TC2 | Boundary (lower) | task at 2026-10-19T00:00:00Z | included, 10 credits |
| TC3 | Boundary (upper) | task at 2026-10-26T00:00:00Z | excluded, 0 credits (belongs to next window) |
| TC4 | Boundary (just inside) | task at 2026-10-25T23:59:59Z | included |
| TC5 | Timezone | task at 2026-10-26T04:59:00+05:00 (= 23:59Z Sunday) | included |
| TC6 | Timezone | task at 2026-10-26T05:00:00+05:00 (= 00:00Z Monday) | excluded |
| TC7 | Duplicate input | same task_id twice in input | paid once, 10 credits |
| TC8 | Retry after crash (**selected failure**) | 4 tasks; crash after 2 payouts; run again | each task paid exactly once, total 40 |
| TC9 | Re-run of a finished run | run settlement twice, no crash | second run pays 0 |
| TC10 | Partial failure (notification) | notifier raises on every call | payouts stay committed, failures recorded, no rollback |
| TC11 | Order of operations | payout fails for a task | no notification sent for it |
| TC12 | Invalid input | naive timestamp (no offset) | rejected with a clear error |
| UI1–UI7 | Browser (Playwright) | happy path, cut-off, re-run, crash + retry, notification outage, timezone, duplicate input through the demo page | same expectations, checked on screen |

**Results on the faulty version:** TC7, TC8, TC9, TC10 and UI3, UI4, UI5, UI7 fail. TC8 is the headline regression. The remaining cases pass on both, which shows the tests are not simply failing everywhere.

## 8. Deliverables and completion criteria

1. `pytest` runs from the repo root with one command. ✅
2. TC8 **fails** against `settle_faulty` and **passes** against `settle_fixed`; output saved to [docs/evidence-faulty.txt](docs/evidence-faulty.txt) and [docs/evidence-fixed.txt](docs/evidence-fixed.txt). ✅
3. Invariant check: total credits paid = 10 × unique qualifying tasks (`assert_paid_once`). ✅
4. [docs/defect-report.md](docs/defect-report.md) with title, reproduction steps, expected vs actual, severity, root cause, evidence, fix and blocking checks. ✅
5. [docs/release-checklist.md](docs/release-checklist.md) with gates and pass/fail. ✅
6. [README.md](README.md) explains setup and how to run the comparison. ✅
7. Remaining gaps and limitations written down (below and in the checklist). ✅

## 9. Release checks that would block this failure

- CI regression test: crash mid-settlement, re-run, assert exactly-once payout (TC8, UI4). Failure blocks merge.
- Idempotency test: run twice, second run pays 0 (TC9, UI3).
- Invariant check: credits paid = 10 × unique qualifying tasks.
- Boundary and timezone tests (TC2–TC6, UI2, UI6) green.
- Notification isolation test (TC10, UI5) green.
- CI also proves the tests still catch the bug: every `regression` test must fail on the faulty version, or the gate reports "GATE BROKEN".
- Code review gate: any payout path must check "already paid" and write the payout in one step.

## 10. How to work with the AI agent (record this for the Loom)

- Ask the agent to build the faulty version first and confirm TC8 fails **before** writing the fix.
- Read and run every test yourself; do not accept "tests pass" without seeing the output.
- Note each place you corrected the agent. These go in the appendix.
- Keep a short record: what the AI wrote, what you changed, and why (summarised in the appendix).

## 11. Results and handoff appendix

**Artifact links:** repository https://github.com/kashif-afk/Demo-project · [intent.md](intent.md) · [docs/test-cases.md](docs/test-cases.md) · [docs/defect-report.md](docs/defect-report.md) · [docs/release-checklist.md](docs/release-checklist.md) · [docs/evidence-faulty.txt](docs/evidence-faulty.txt) · [docs/evidence-fixed.txt](docs/evidence-fixed.txt) · [.github/workflows/ci.yml](.github/workflows/ci.yml)

**How to reproduce:**
```
pip install -r requirements.txt
python -m playwright install chromium
python -m pytest -v              # both versions: 8 failed (all faulty), 30 passed
python -m pytest -v -k fixed     # 19 passed
python -m pytest -v -k faulty    # 8 failed, 11 passed
python src/app.py                # demo page: http://127.0.0.1:8000
```

**Checks and actual results** (2026-11-02, Python 3.14.3, from the evidence files):

| Run | Result | Exit |
|---|---|---|
| Faulty | 8 failed (TC7, TC8, TC9, TC10, UI3, UI4, UI5, UI7), 11 passed | 1 |
| Fixed | 19 passed | 0 |
| CI gate | verified locally: OK on faulty, "GATE BROKEN" when pointed at fixed | — |
| CI on GitHub | passed: [run 41310774366](https://github.com/kashif-afk/Demo-project/actions/runs/41310774366) | 0 |

Demo numbers: crash after 2 payouts, then retry → faulty pays **60** (T-1 and T-2 twice), fixed pays **40**.

**AI contribution and corrections:** Claude Code (Claude Opus 5.5) wrote the code in `src/`, the tests, the demo page, CI and drafts of every document. The faulty version and its tests were written and run before `settle_fixed.py` existed (TC7–TC10 failed first). Corrections made along the way:
- The directive contradicted itself on TC11; resolved by modelling the faulty version as "notify inside the payout transaction".
- The Playwright fixture `base_url` clashed with pytest-playwright's own fixture; renamed to `demo_url`.
- A load/reset race in the UI tests; tests now wait for the page before switching version.
- The CI gate first missed pytest's "deselected" summary; fixed and verified ("GATE BROKEN" when pointed at fixed).
- UI7 first failed on a missing log message instead of the double payout; reordered so it fails on "T-2 paid twice".

`<Add your own corrections and decisions here.>`

**Limitations:** fictional flow; in-memory ledger and mock notifier; no concurrency testing; no real scheduler; a notification is lost if the job crashes between payout and notify; "paid once" is per window, so the same task ID in a later week would be paid again.

**Release-readiness decision:** faulty **NO-GO** (retries overpay, notification outage reverses payouts). Fixed **GO**: CI is green on main.

**Pre-existing work:** an earlier version of this project (same case, different structure and a larger demo console) was built with Claude Code on 2026-10-30/31 and discarded on 2026-11-01. This version was rebuilt from scratch. The idea of making the payout and the ledger record a single write came from a gap found in that earlier version.
