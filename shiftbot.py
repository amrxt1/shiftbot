# dotenv stuff
from dotenv import load_dotenv
import os

# playwright
from playwright.sync_api import sync_playwright

load_dotenv()


class Shiftbot:
    def __init__(self):
        self.keyword = os.getenv("SHIFTBOT_KEYWORD")
        # imap creds
        self.host = os.getenv("SHIFTBOT_HOST")
        self.email = os.getenv("SHIFTBOT_EMAIL")
        self.password = os.getenv("SHIFTBOT_PASS")
        # playwright
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch_persistent_context(
            user_data_dir="./profile",
            headless=False,
            locale="en-CA",
            args=["--start-maximized"],
        )
        self.page = self.browser.new_page()
        # portal creds
        self.portal_password = os.getenv("SHIFTBOT_LOGIN_PASS")

    def stealthify(self, page):
        page.evaluate("""
        () => {
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
        }""")
        return 0

    def handle_shift_link(self, url: str):
        page = self.page

        page.goto(url)
        self.stealthify(page=page)
        input("Page ready")

        # enter portal email
        page.fill(".email_input", os.getenv("SHIFTBOT_EMAIL"))
        input("Email Entered")

        # enter portal pass
        page.fill(".password_input", os.getenv("SHIFTBOT_LOGIN_PASS"))
        input("Password entered")

        # login
        page.press(".password_input", "Enter")
        input("Logged in")
        self.stealthify(page=page)

        # press first button
        page.click("button[name='cover']")
        input("Past stage 1")
        self.stealthify(page=page)

        # press second button
        page.click("button[name='confirm_coverage']")
        input("We're done here...Sending notification")
        # notify

    def run(self):
        input("Bot Ready")
