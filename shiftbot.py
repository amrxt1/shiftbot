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
        self.keywords = [
            k.strip().lower() for k in (os.getenv("SHIFTBOT_KEYWORD") or "").split(",")
        ]

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

    def handle_shift_links(self, urls: list[str]):
        page = self.page
        shift_acquired = False

        # make sure we start at logged out state
        page.goto("https://app.shiftboard.com/servola/logout.cgi?logout=1")

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

                    shift_acquired = True

                except Exception as e:
                    logging.exception(f"Exception occured while handling {url}\n{e}")

        # logout
        page.goto("https://app.shiftboard.com/servola/logout.cgi?logout=1")
        return shift_acquired

    @staticmethod
    def unique(seq):
        seen = set()
        return [x for x in seq if not (x in seen or seen.add(x))]

    def extract_shift_links_from_msg(self, msg):
        links = []
        body_text = ""

        # log sender and subject
        sender = msg.get("From", "Unknown Sender")
        subject = msg.get("Subject", "No Subject")
        logging.info(f"Email From: {sender}")
        logging.info(f"Subject: {subject}")

        # get keywords from .env
        keywords = self.keywords

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type in ("text/plain", "text/html"):
                    payload = part.get_payload(decode=True)
                    if payload:
                        decoded = payload.decode(
                            part.get_content_charset() or "utf-8", errors="replace"
                        )
                        body_text += unescape(decoded)
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                decoded = payload.decode(
                    msg.get_content_charset() or "utf-8", errors="replace"
                )
                body_text += unescape(decoded)

        # keyword filtering
        if any(keyword in body_text.lower() for keyword in keywords):
            links = re.findall(
                r"https://shiftboard\.com/go/guardteck/shifts/\d+",
                body_text,
            )
        else:
            logging.info("No keywords matched. Skipping email.")

        return self.unique(links)

    def run(self):
        logging.info(self)
        self.client.idle()
        logging.info("IMAPClient logged in and in IDLE mode.")
        logging.info(f"We are looking for: {self.keywords}")

        if not self.keywords or self.keywords == [""]:
            logging.warning("No keywords defined. Shiftbot will match everything.")

        # self.n.notify("We are Live!")

        # log out before checking incase there is a session from previous run
        self.page.goto("https://app.shiftboard.com/servola/logout.cgi?logout=1")

        # run the eternal loop
        while True:
            try:
                # watch out for new mail
                responses = self.client.idle_check(timeout=5)
                logging.info(f"Server sent: {responses if responses else 'nothing'}")
                time.sleep(0.1)

                # if anything in response
                if responses:
                    self.client.idle_done()
                    # iterate over the responses
                    for response in responses:
                        # make sure we only deal with b'EXISTS'
                        if isinstance(response, tuple) and len(response) == 2:
                            seq, flag = response
                            if flag == b"EXISTS":
                                # fetch the message data for SEQ: seq
                                logging.info(f"Processing SEQ: {seq}")
                                for uid, message_data in self.client.fetch(
                                    seq, "RFC822"
                                ).items():
                                    # convert bytes into a message using email
                                    msg = email.message_from_bytes(
                                        message_data[b"RFC822"]
                                    )
                                    # look for any useful links and make sure there's at least one keyword
                                    logging.info(f"Message Data Recieved for SEQ-{seq}")
                                    links = self.extract_shift_links_from_msg(msg)
                                    logging.info(f"Links harvested:  {links}")

                                    # if there are any links, handle them or keep looking
                                    if links:
                                        try:
                                            if self.handle_shift_links(urls=links):
                                                return 0
                                        except Exception as e:
                                            logging.exception(
                                                f"Exception occured while taking the shift {e}"
                                            )
                                            continue
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
            self.client.logout()
        except Exception as e:
            logging.exception(f"Could not logout from IMAP: {e}")
