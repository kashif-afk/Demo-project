"""UI1-UI5: Playwright drives the demo page (src/app.py) in a real browser, against both versions.

Sample data: T-1..T-4 qualify (expected total 40); T-5 completed exactly Mon 00:00 UTC and does not.
"""

import threading

import pytest
from playwright.sync_api import Page, expect

from app import make_server

expect.set_options(timeout=3000)


@pytest.fixture(scope="module")
def demo_url():
    server = make_server(port=0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture(params=["faulty", "fixed"])
def ui(request, page: Page, demo_url) -> Page:
    page.goto(demo_url)
    expect(page.get_by_test_id("tasks").locator("tbody tr")).to_have_count(5)  # initial state loaded
    page.get_by_test_id("version").select_option(request.param)  # switching version resets the demo
    expect(page.get_by_test_id("status")).to_have_text("Not run yet.")
    expect(page.get_by_test_id("total-paid")).to_have_text("0")
    return page


def test_ui1_single_run_pays_each_qualifying_task_once(ui: Page):
    ui.get_by_test_id("run").click()

    expect(ui.get_by_test_id("status")).to_have_text("OK: every task paid once, total 40.")
    expect(ui.get_by_test_id("payouts").locator("tbody tr")).to_have_count(4)
    expect(ui.get_by_test_id("notified")).to_have_text("T-1, T-2, T-3, T-4")


def test_ui2_cut_off_task_is_shown_out_of_window_and_never_paid(ui: Page):
    ui.get_by_test_id("run").click()

    t5 = ui.get_by_test_id("tasks").locator("tr", has_text="T-5")
    expect(t5).to_contain_text("no")
    expect(ui.get_by_test_id("payouts")).not_to_contain_text("T-5")


@pytest.mark.regression
def test_ui3_running_again_pays_nothing(ui: Page):
    ui.get_by_test_id("run").click()
    ui.get_by_test_id("run").click()

    expect(ui.get_by_test_id("runs").locator("li").nth(1)).to_have_text(
        "Paid nothing · skipped already paid T-1, T-2, T-3, T-4")
    expect(ui.get_by_test_id("status")).to_have_text("OK: every task paid once, total 40.")


@pytest.mark.regression
def test_ui4_retry_after_crash_pays_each_task_once(ui: Page):
    ui.get_by_test_id("crash").check()
    ui.get_by_test_id("run").click()
    expect(ui.get_by_test_id("runs")).to_contain_text("Crashed: job crashed after 2 payouts")
    expect(ui.get_by_test_id("total-paid")).to_have_text("20")

    ui.get_by_test_id("crash").uncheck()
    ui.get_by_test_id("run").click()

    expect(ui.get_by_test_id("status")).to_have_text("OK: every task paid once, total 40.")


@pytest.mark.regression
def test_ui5_notification_outage_keeps_payouts(ui: Page):
    ui.get_by_test_id("notify-down").check()
    ui.get_by_test_id("run").click()

    expect(ui.get_by_test_id("runs").locator("li").first).to_contain_text("notification failed T-1, T-2, T-3, T-4")
    expect(ui.get_by_test_id("total-paid")).to_have_text("40")
    expect(ui.get_by_test_id("notified")).to_have_text("none")
