# Quest Plan — What To Do and What Should Be Done

Quest: **Prevent a Recurring Business-Flow Failure** (rewards settlement)
Chosen problem: **A settlement re-run after a partial failure pays the same task twice** (task ID duplicates folded in).

Everything here is fictional and synthetic. No live financial system.

---

## 1. The four required submission items

| # | Item | What it must show | Status |
|---|------|-------------------|--------|
| 1 | **Loom video** (max 5 min) | Chosen problem and why it ranked first; demo of the result; the most important verification or revision; AI use, personal decisions, limitations | [ ] |
| 2 | **intent.md** | "Why this problem?": other problems considered, prioritization criteria (and scores if used), why this ranked first, affected users, evidence, intended value, non-goals | [ ] |
| 3 | **directive.md** (final) | Objective, scope, requirements, completion criteria + results/handoff appendix (artifact links, how to reproduce, checks and actual results, AI contribution and corrections, limitations) | [ ] draft done |
| 4 | **Career Path & Career Leverage Video** | Separate video, see the brief's career section | [ ] |

Optional (no bonus, no penalty): problem.md, agents.md, claude.md, earlier directive versions.

## 2. The five tasks and what "done" means

### Task 1: Rank the failure problems
**Do:** List at least 3 failures, rank by user impact, likelihood, effort. Pick one. State uncertainty.
**Done when:** `intent.md` has 6+ problems, a ranking table, a clear reason P1 won, and a plain statement that likelihood is an estimate (no invented incident history).

### Task 2: Map the flow and write 8+ test cases
**Do:** Draw the flow (input, window filter, dedupe, payout, ledger, notify). Write test cases with inputs and expected outcomes.
**Done when:** `docs/test-cases.md` has 8+ cases covering all six required types: happy path, cut-off boundary, timezone conversion, duplicate input, retry, partial failure. Assumptions about account changes and admin settings are written down.

### Task 3: Build the fixture and automated checks
**Do:** Build the faulty version, a fixed version, a mock ledger and a mock notifier. Write pytest tests.
**Done when:** the retry test (TC8) **fails** on the faulty version and **passes** on the fixed one. Both outputs are saved as evidence files.

### Task 4: Defect report
**Do:** Write one actionable report.
**Done when:** `docs/defect-report.md` has reproduction steps, expected vs actual, severity with rationale, root cause, evidence links, proposed fix, and the release checks that would block this failure.

### Task 5: Final run, gaps, release decision
**Do:** Run the full suite on camera. Record what is not covered. Make a go / no-go call.
**Done when:** `docs/release-checklist.md` is filled with real results, remaining gaps are listed, and the directive appendix has handoff instructions.

## 3. Order of work (with time budget)

Suggested total effort is 6–8 hours. Planning window is 5 days after accepting. **Confirm the exact deadline and timezone with recruiter John before starting.**

| Step | What | Time |
|------|------|------|
| 1 | Confirm deadline, timezone, effort and any compensation terms with John | 10 min |
| 2 | Write `intent.md` (problem list, ranking, why P1) | 45 min |
| 3 | Finalize test cases in `docs/test-cases.md` | 45 min |
| 4 | In Claude Code: build faulty version, **confirm TC8 fails first** | 60 min |
| 5 | Build the fixed version, get all tests green | 60 min |
| 6 | Capture evidence output for faulty and fixed runs | 15 min |
| 7 | Write `docs/defect-report.md` | 45 min |
| 8 | Write `docs/release-checklist.md` and the README | 30 min |
| 9 | Update `directive.md` appendix with real results and AI log | 30 min |
| 10 | Record the Quest Loom (max 5 min, rehearse once) | 45 min |
| 11 | Record the Career Path & Career Leverage video | 30 min |
| 12 | Verify every link and reviewer access, then submit | 20 min |

Record your **actual** effort. The brief asks you to report it.

## 4. AI usage log (keep this as you go)

Judges score how you worked with AI. For each AI step, note:
- what you asked the agent to do
- what it produced
- what you checked or ran yourself
- what you corrected, and why

Examples worth capturing: a wrong boundary operator (`<=` vs `<`), tests that pass without really simulating a crash, over-mocking, missing timezone handling.

## 5. Loom script outline (5 minutes)

| Time | Content |
|------|---------|
| 0:00–0:45 | The flow, the other problems considered, why the retry double payout ranked first |
| 0:45–1:30 | Test case map: the six required categories |
| 1:30–3:00 | Demo: TC8 failing on the faulty version, then passing on the fixed version |
| 3:00–3:45 | Most important verification or revision: a place where the AI was wrong and you caught it |
| 3:45–4:30 | AI use and your own decisions |
| 4:30–5:00 | Remaining limitations and release-readiness call |

## 6. Rules to stay inside (from the brief)

- Do **not** fabricate interviews, users, revenue, approvals, tests, sources or incident history.
- Label synthetic data, mockups, untested assumptions and estimates.
- Distinguish your work from AI output.
- If you reuse existing work, say what pre-existed and what you changed.
- No credentials, API keys, employer-confidential material or personal data in the submission.
- No real-money transactions, live deployment or public publishing.
- Open every link before submitting and confirm the reviewer can access it. A private shared folder or repository is fine.

## 7. Final pre-submit checklist

- [ ] Deadline and timezone confirmed with John
- [ ] intent.md complete
- [ ] directive.md final, with results/handoff appendix filled in
- [ ] Tests: faulty fails, fixed passes, evidence files saved
- [ ] Defect report and release checklist written
- [ ] Quest Loom under 5 minutes
- [ ] Career Path & Career Leverage video recorded
- [ ] Every link opened and access verified
- [ ] No secrets or confidential data in any file
- [ ] Actual effort recorded
