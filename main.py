from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os

load_dotenv()

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir="./profiles",
        headless=False,
        locale="en-US",
        viewport={"width": 1280, "height": 720},
    )
    page = browser.new_page()
    page.goto("https://google.com/")
    page = browser.new_page()
    page.goto("https://shiftboard.com/guardteck")
    page.evaluate("""
    () => {
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
    }""")

    input("Page ready")

    page.fill(".email_input", os.getenv("SHIFTBOT_EMAIL"))
    input("Page ready")

    page.fill(".password_input", os.getenv("SHIFTBOT_LOGIN_PASS"))
    input("Page ready")

    page.press(".password_input", "Enter")
    input()

    browser.close()
