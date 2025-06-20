# mail client
from imapclient import IMAPClient

# env var support
from dotenv import load_dotenv
import os

load_dotenv()

m_server = IMAPClient("imap.gmail.com", use_uid=True)
print(m_server.login(os.getenv("SHIFTBOT_EMAIL"), os.getenv("SHIFTBOT_PASS")))
print("we're good")
