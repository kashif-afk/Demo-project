# Rewards Settlement QA: prevent double payout on retry

Fictional assessment case. All data is synthetic. No real money or live system.

A weekly job pays 10 test credits per completed task. The **faulty** version pays a task again when the job is retried after a crash. The **fixed** version pays each task once. Every test runs against both versions, so one run shows the bug and the fix side by side.

Start with [directive.md](directive.md) and [intent.md](intent.md).

## Setup

Python 3.11+.

```
pip install -r requirements.txt
python -m playwright install chromium
```

## Run

```
python -m pytest -v              # everything: 7 failed (all on faulty), 27 passed
python -m pytest -v -k fixed     # fixed only: 17 passed
python -m pytest -v -k faulty    # faulty only: 7 failed, 10 passed
python -m pytest -v -k "tc8"     # the headline test on both versions
```

Tests marked `regression` are the ones that must fail on faulty and pass on fixed.

## See it in the browser

```
python src/app.py
```

Open http://127.0.0.1:8000, choose **faulty**, tick **Crash after 2 payouts**, click **Run settlement**, untick, click **Run settlement** again. The status turns red: paid 60, should be 40. Choose **fixed** and repeat: paid 40.

## Layout

| Path | What |
|---|---|
| `src/settle_faulty.py`, `src/settle_fixed.py` | the two versions of the settlement job |
| `src/window.py`, `src/ledger.py`, `src/notifier.py` | window and UTC handling, payout ledger, mock notifier |
| `src/app.py`, `src/index.html` | small local demo page (standard library only) |
| `tests/test_settlement.py` | TC1–TC12 engine tests |
| `tests/test_ui.py` | UI1–UI5 Playwright browser tests |
| `docs/` | plan, test cases, defect report, release checklist, AI log, effort log, Loom script, evidence |
| `.github/workflows/ci.yml` | release gate |
