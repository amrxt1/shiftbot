# dotenv stuff
from dotenv import load_dotenv
import os

# playwright
from playwright.sync_api import sync_playwright

# imap
from imapclient import IMAPClient

# logging
import logging
from datetime import datetime

# notifier
from notifier import Notifier

# misc
import time
import email
import re
from html import unescape

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(
            f"./logs/shiftbot{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
        logging.StreamHandler(),
    ],
)


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
        self.portal_url = os.getenv("SHIFTBOT_PORTAL_URL")
        self.portal_password = os.getenv("SHIFTBOT_LOGIN_PASS")

        # notifier
        self.n = Notifier(os.getenv("NOTIFIER_URL"), os.getenv("NOTIFIER_CHAT_ID"))

    def stealthify(self, page):
        page.evaluate("""
        () => {
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
        }""")
        return 0

    def handle_shift_link(self, urls: list[str]):
        page = self.page

        page.goto(self.portal_url)
        logging.info(f"Arrived at portal login. Working with: {len(urls)} URLs")

        # enter portal email
        page.fill(".email_input", os.getenv("SHIFTBOT_EMAIL"))
        logging.info("Dumped Email")

        # enter portal pass
        page.fill(".password_input", os.getenv("SHIFTBOT_LOGIN_PASS"))
        logging.info("Dumped Password")

        # login
        page.press(".password_input", "Enter")
        logging.info("Pressed Login")

        for url in urls:
            if isinstance(url, str):
                try:
                    logging.info(f"Try for {url}")

                    # on shift page
                    page.goto(url)

                    # press first button
                    page.click("button[name='cover']")

                    # press second button
                    page.click("button[name='confirm_coverage']")
                    logging.info("Shift acquired!")

                    # notify
                    logging.info("Sending notification.")
                    self.n.notify(f"Shift acquired!\nCheck details: {url}")

                except Exception as e:
                    logging.exception(f"Exception occured while handling {url}\n{e}")

        # logout
        page.goto("https://app.shiftboard.com/servola/logout.cgi?logout=1")

    @staticmethod
    def unique(seq):
        seen = set()
        return [x for x in seq if not (x in seen or seen.add(x))]

    def extract_shift_links_from_msg(self, msg):
        links = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type in ("text/plain", "text/html"):
                    payload = part.get_payload(decode=True)
                    if payload:
                        decoded = payload.decode(
                            part.get_content_charset() or "utf-8", errors="replace"
                        )
                        links.extend(
                            re.findall(
                                r"https://shiftboard\.com/go/guardteck/shifts/\d+",
                                unescape(decoded),
                            )
                        )
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                decoded = payload.decode(
                    msg.get_content_charset() or "utf-8", errors="replace"
                )
                links.extend(
                    re.findall(
                        r"https://shiftboard\.com/go/guardteck/shifts/\d+",
                        unescape(decoded),
                    )
                )

        return self.unique(links)

    def run(self):
        logging.info(self)
        self.client.idle()
        logging.info("IMAPClient logged in and in IDLE mode.")
        self.n.notify("We are Live!")
        while True:
            try:
                responses = self.client.idle_check(timeout=5)
                logging.info(f"Server sent: {responses if responses else 'nothing'}")
                time.sleep(0.1)

                if responses:
                    self.client.idle_done()
                    for response in responses:
                        if isinstance(response, tuple) and len(response) == 2:
                            seq, flag = response
                            if flag == b"EXISTS":
                                logging.info(f"Processing SEQ: {seq}")
                                for uid, message_data in self.client.fetch(
                                    seq, "RFC822"
                                ).items():
                                    msg = email.message_from_bytes(
                                        message_data[b"RFC822"]
                                    )
                                    logging.info(f"Message Data Recieved for SEQ-{seq}")
                                    links = self.extract_shift_links_from_msg(msg)
                                    logging.info(f"Links harvested:  {links}")
                                    self.handle_shift_link(links)
                                    return 0
                    self.client.idle()
                    time.sleep(0.25)

            except KeyboardInterrupt:
                break
            except Exception as e:
                logging.exception("An exception occured. Retrying...\n", e)
                self.client.idle()

    def shutdown(self):
        logging.info("Exiting...")

        try:
            self.pw.stop()
        except Exception as e:
            logging.exception(f"Could not stop Playwright: {e}")

        try:
            self.client.idle_done()
            self.client.logout()
        except Exception as e:
            logging.exception(f"Could not logout from IMAP: {e}")
