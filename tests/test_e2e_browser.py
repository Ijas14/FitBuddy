"""
End-to-end browser verification for FitBuddy (Playwright).

This test drives a live Uvicorn server through the complete user journey:
home form -> plan generation -> feedback refinement -> admin dashboard.

Run with the server already listening:

    python -m uvicorn app.main:app --port 8010 &
    PYTHONPATH=. python -m pytest tests/test_e2e_browser.py -v

Tests are skipped automatically when the server is not reachable, so the
regular unit/integration suite never fails because of a missing server.
"""

import os
import re
import socket

import pytest

playwright = pytest.importorskip("playwright.sync_api")

from playwright.sync_api import sync_playwright, expect  # noqa: E402

BASE_URL = "http://127.0.0.1:8010"

# Prefer chromium; fall back to firefox when chromium binaries are unavailable
# (e.g. restricted CI environments where the chromium download is blocked).
BROWSER_PREFERENCE = [b for b in os.getenv("FITBUDDY_E2E_BROWSER", "").split(",") if b] or [
    "chromium",
    "firefox",
]


def _server_is_up() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.0)
        return sock.connect_ex(("127.0.0.1", 8010)) == 0


pytestmark = pytest.mark.skipif(
    not _server_is_up(),
    reason="Live FitBuddy server not running on 127.0.0.1:8010",
)


def _launch_browser(playwright_instance):
    """Try bundled browsers first, then the system Chrome installation."""
    last_error = None
    for name in BROWSER_PREFERENCE:
        browser_type = getattr(playwright_instance, name, None)
        if browser_type is None:
            continue
        attempts = [{}]
        if name == "chromium":
            # Fall back to a locally installed Google Chrome when the bundled
            # Playwright chromium binaries are unavailable.
            attempts.append({"channel": "chrome"})
        for kwargs in attempts:
            try:
                return browser_type.launch(**kwargs)
            except Exception as exc:  # pragma: no cover - depends on local binaries
                last_error = exc
    pytest.skip(f"No Playwright browser could be launched: {last_error}")


def test_full_user_journey():
    with sync_playwright() as p:
        browser = _launch_browser(p)
        page = browser.new_page()
        page.set_default_timeout(20000)

        # --- 1. Home page renders the input form -----------------------
        page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
        assert "FitBuddy" in page.title()
        assert page.get_by_label("Name:").is_visible()
        assert page.get_by_label("User ID:").is_visible()
        assert page.get_by_label("Age:").is_visible()
        assert page.get_by_label("Weight (kg):").is_visible()
        assert page.get_by_label("Fitness Goal:").is_visible()
        assert page.get_by_label("Workout Intensity:").is_visible()

        # --- 2. Submit the form and get a personalized plan ------------
        page.get_by_label("Name:").fill("Playwright Journey")
        page.get_by_label("User ID:").fill("7777")
        page.get_by_label("Age:").fill("31")
        page.get_by_label("Weight (kg):").fill("69.5")
        page.get_by_label("Fitness Goal:").fill("weight loss and endurance")
        page.get_by_label("Workout Intensity:").select_option("High")
        with page.expect_navigation(wait_until="domcontentloaded"):
            page.get_by_role("button", name="Generate Plan").click()

        expect(page).to_have_url(re.compile(r"/generate-workout$"))

        # Without a fallback, plan generation fails visibly when Gemini is
        # unavailable (quota, key, model name). The journey needs live AI, so
        # surface the exact reason and skip rather than fail.
        error_reason = page.locator(".error-reason")
        if error_reason.count() > 0:
            pytest.skip(f"AI unavailable: {error_reason.first.inner_text()[:150]}")

        expect(page.locator("body")).to_contain_text("Playwright Journey")
        expect(page.locator("body")).to_contain_text("7777")

        plan_text = page.locator("pre.formatted-plan").inner_text()
        assert "Day 1:" in plan_text
        assert "Day 7:" in plan_text
        assert "Warm-up" in plan_text
        assert "Main Workout" in plan_text
        assert "Cooldown" in plan_text

        # The tip card shows either the generated tip or, when Flash alone
        # failed, an inline error box with the reason.
        tip_box = page.locator(".nutrition-tip-box")
        tip_error = page.locator(".alert-error")
        if tip_box.count() > 0:
            assert len(tip_box.inner_text().strip()) > 20
        else:
            assert tip_error.count() > 0, "neither a nutrition tip nor an error reason is shown"

        # --- 3. Submit feedback and confirm the plan is updated --------
        # The spec shows the feedback form's User ID field starting empty with
        # its placeholder visible, so the journey types the ID in explicitly.
        page.get_by_label("Your Unique User ID:").fill("7777")
        page.get_by_label("Your Feedback:").fill("Add more cardio and yoga sessions.")
        with page.expect_navigation(wait_until="domcontentloaded"):
            page.get_by_role("button", name="Submit Feedback").click()

        expect(page).to_have_url(re.compile(r"/submit-feedback$"))
        confirmation = page.locator(".alert-success")
        expect(confirmation).to_contain_text(
            "Your plan has been updated based on your feedback!"
        )

        updated_plan = page.locator("pre.formatted-plan").inner_text()
        assert "Updated based on your feedback" in updated_plan

        # Auto-accept the JS confirm() used by the admin delete action.
        page.on("dialog", lambda dialog: dialog.accept())

        # --- 4. Admin dashboard lists the user with both plans ---------
        page.goto(f"{BASE_URL}/view-all-users", wait_until="domcontentloaded")
        assert page.title() == "FitBuddy - All Users & Workout Plans"

        headers = [h.inner_text().strip() for h in page.locator("table.data-table thead th").all()]
        assert headers[:8] == [
            "User ID",
            "Name",
            "Age",
            "Weight (kg)",
            "Goal",
            "Intensity",
            "Original Plan",
            "Updated Plan",
        ]

        row = page.locator("table.data-table tbody tr", has_text="Playwright Journey")
        expect(row).to_have_count(1)
        expect(row.first.locator("td").nth(7)).not_to_contain_text("Not updated")

        # --- 5. Admin delete removes the record ------------------------
        with page.expect_navigation(wait_until="domcontentloaded"):
            row.first.get_by_role("button", name="Delete").click()

        expect(
            page.locator("table.data-table tbody tr", has_text="Playwright Journey")
        ).to_have_count(0)

        browser.close()
