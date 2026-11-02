# AI usage log

Tool: Claude Code (Claude Opus 5.5) in VS Code. Format: what I asked, what it produced, what I checked, what was corrected.

## 2026-10-30 to 2026-10-31: first version (discarded)

- **Asked:** build the rewards settlement fixture, tests, CI and docs from my first plan.
- **Produced:** a larger project (package layout, 35 tests, mutation testing, a FastAPI "payout console").
- **Kept as a lesson:** a review found that the first "fixed" version paid the user *before* writing the ledger record. A crash between those two steps left money paid but unrecorded, so a retry paid again, and the original crash test could not see it. That is why the new fix makes the payout and the ledger record a single write.
- **Why discarded (my decision):** it did not follow my plan's structure and was harder to explain than the task needed.

## 2026-11-01: rebuild from scratch (this version)

- **Asked:** rebuild everything from my Quest Plan and directive, plain and simple, with Playwright tests.
- **Order followed (plan step 4):** the agent wrote `window.py`, `ledger.py`, `notifier.py`, `settle_faulty.py` and the tests first, and ran them **before** `settle_fixed.py` existed. Faulty side: TC7, TC8, TC9, TC10 failed, 8 passed. Then it wrote the fix: all 12 engine checks passed on fixed.
- **Produced:** the code in `src/`, `tests/`, the demo page, CI, and drafts of every document.
- **Corrections during the build:**
  - **Contradiction in my directive:** "faulty notifies before commit" would also send a notification for a failed payout, making TC11 fail on faulty, but the directive said only TC7–TC10 fail. Resolved by modelling the faulty version as "notify inside the payout transaction": a payout failure happens before the notification (TC11 passes), and a notification failure rolls back the payout (TC10 fails). The two documents now agree with the code.
  - The Playwright fixture was named `base_url`, which clashes with pytest-playwright's own fixture. All UI tests errored. Renamed to `demo_url`.
  - Possible race in the UI tests: the page's first load and the version reset could finish in either order. The tests now wait for the page to load before switching version, and check the total is 0.
  - The CI gate first matched `^N failed in`, which missed pytest's "27 deselected" in the summary line. Changed to "failed and no passed". Verified: OK on faulty, "GATE BROKEN" when pointed at fixed.
  - The invariant helper's assert printed a bare `AssertionError` (helper modules are not assert-rewritten). Added `pytest.register_assert_rewrite("fixtures")`.
- **Checked by running:** full suite 3 times (7 failed, 27 passed each time, ~12 s); evidence files captured from real runs; demo numbers (60 vs 40) read from the running code.
- **Found while checking:** on the fixed version, a crash between payout and notify means that task is never notified (T-2 in UI4). Recorded as a gap, not hidden.

## 2026-11-02: browser coverage for timezone and duplicates

- **Asked:** make the Playwright tests cover all six categories, not only the engine tests.
- **Produced:** sample task T-6 (`+05:00`, lands on Mon 00:00Z), a "T-2 sent twice in the input" checkbox on the demo page, and tests UI6 (timezone) and UI7 (duplicate input, `regression`).
- **Corrected:** UI7 first checked the run log text, so on faulty it failed on a missing message rather than the defect. Reordered so it fails on "T-2 payout rows: expected 1, actual 2".
- **Checked by running:** full suite 8 failed (all faulty), 30 passed; CI gate steps run locally (faulty non-regression 11 passed, faulty regression 8 failed); evidence files re-captured.

## My decisions

`<Fill in: which problem you picked and why, what you accepted or rejected from the agent, what you checked yourself.>`
