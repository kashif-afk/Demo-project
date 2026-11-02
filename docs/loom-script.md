# Loom script (under 5 minutes)

Say it in your own words; lines in `<angle brackets>` are yours to fill. Only say what is true.

**Before recording:** run `python src/app.py`, open http://127.0.0.1:8000, choose **faulty**. Have a terminal open in the project folder.

## 0:00–0:45: the flow and why this problem

Screen: [intent.md](../intent.md), the table.

> "Every Tuesday a job pays 10 credits for each task finished last week. Each task must be paid once. I listed six things that can go wrong and scored them. The top one: if the job crashes and is run again, it pays the same tasks twice. It's real money, nobody complains about being paid twice so it stays hidden, and it comes back every time the job is retried. These scores are my estimates, not incident data."

## 0:45–1:30: test case map

Screen: [docs/test-cases.md](test-cases.md), flow map and the coverage table.

> "Here is the flow: check the time, check the window, skip duplicates, skip already paid, pay, then notify. I wrote 12 engine tests and 5 browser tests covering the six required types: happy path, cut-off, timezone, duplicate, retry and partial failure. Every test runs against both versions."

## 1:30–3:00: demo

Browser, version **faulty**:
1. Tick **Crash after 2 payouts**, click **Run settlement**. → "The job crashed after paying 2 tasks: 20 paid."
2. Untick, click **Run settlement**. → "That's the retry. Red: paid 60, should be 40. T-1 and T-2 were paid twice."
3. Choose **fixed**, repeat both steps. → "Green: 40. The retry skipped the two already-paid tasks."

Terminal:
```
python -m pytest -v -k tc8
```
> "Same thing as a test: TC8 fails on faulty, passes on fixed."
```
python -m pytest -q
```
> "The full run: 7 failures, all on the faulty version, exactly the regression tests. Everything on fixed passes. CI runs this and blocks the release if a regression test stops catching the bug."

## 3:00–3:45: most important verification or revision

> `<Pick a real one. Options from docs/ai-log.md: the faulty version was built and TC8 confirmed failing before the fix existed; my directive contradicted itself about TC11 and the agent's model was adjusted; the CI gate check was wrong at first and I verified it reports "GATE BROKEN" on the fixed code; the earlier version paid before writing the ledger, which is why the fix is one write.>`

## 3:45–4:30: AI use and my decisions

Screen: [docs/ai-log.md](ai-log.md).

> "I used Claude Code. It wrote the code and drafts; every step and correction is in this log. My decisions: `<which problem, the rules interpretation, scrapping the first version, what you checked yourself>`."

## 4:30–5:00: limitations and release call

Screen: [docs/release-checklist.md](release-checklist.md).

> "Not covered: two runs at the same time; a notification is lost if the job crashes between paying and notifying; 'paid once' is per week. Decision: the current release is no-go. The fix is go once CI is green."
