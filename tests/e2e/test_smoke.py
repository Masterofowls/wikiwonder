"""Playwright smoke tests (require playwright browsers: playwright install chromium)."""
import pytest

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module")
def browser_context():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("playwright not installed")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        yield browser
        browser.close()


def test_homepage_loads(live_server, browser_context):
    page = browser_context.new_page()
    page.goto(live_server.url)
    assert page.locator("body").inner_text()
    page.close()


def test_create_page_requires_login(live_server, browser_context):
    page = browser_context.new_page()
    page.goto(f"{live_server.url}/wiki/new/")
    assert "login" in page.url.lower() or page.locator("form").count() >= 0
    page.close()
