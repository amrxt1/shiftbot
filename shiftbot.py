# dotenv stuff
from dotenv import load_dotenv
import os

# playwright
from playwright.sync_api import sync_playwright

# imap
from imapclient import IMAPClient

# misc
import time
import email

load_dotenv()


class Shiftbot:
    def __init__(self, headless=False):
        # keyword to look for
        self.keyword = os.getenv("SHIFTBOT_KEYWORD")

        # imap creds
        self.host = os.getenv("SHIFTBOT_HOST")
        self.email = os.getenv("SHIFTBOT_EMAIL")
        self.password = os.getenv("SHIFTBOT_PASS")
        # imap
        self.client = IMAPClient(self.host, use_uid=False)
        self.client.login(self.email, self.password)
        self.client.select_folder("INBOX")

        # playwright
        self.pw = sync_playwright().start()
        self.browser = self.pw.chromium.launch_persistent_context(
            user_data_dir="./profile",
            headless=headless,
            locale="en-CA",
            args=["--start-maximized"],
            viewport=None,
            no_viewport=True,
        )
        self.page = self.browser.new_page()
        self.stealthify(page=self.page)
        self.page.goto("https://google.com")

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

        # press first button
        page.click("button[name='cover']")
        input("Past stage 1")

        # press second button
        page.click("button[name='confirm_coverage']")
        input("We're done here...Sending notification and logging out")

        page.goto("https://app.shiftboard.com/servola/logout.cgi?logout=1")
        # notify

    def run(self):
        input(self)
        self.client.idle()
        input("IMAPClient in IDLE mode")
        while True:
            try:
                responses = self.client.idle_check(timeout=5)
                print("Server sent:", responses if responses else "nothing")
                time.sleep(0.1)

                if responses:
                    self.client.idle_done()
                    for uid1, flag in responses:
                        if flag == b"EXISTS":
                            for uid2, message_data in self.client.fetch(
                                uid1, "RFC822"
                            ).items():
                                msg = email.message_from_bytes(message_data[b"RFC822"])
                                print(msg)
                    self.client.idle()

            except KeyboardInterrupt:
                break

    def shutdown(self):
        print("Exiting...")

        try:
            self.pw.stop()
        except Exception as e:
            print(f"Could not stop Playwright: {e}")

        try:
            self.client.idle_done()
            self.client.logout()
        except Exception as e:
            print(f"Could not logout from IMAP: {e}")
