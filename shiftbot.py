from dotenv import load_dotenv
import os

load_dotenv()


class Shiftbot:
    def __init__(self):
        self.host = os.getenv("SHIFTBOT_HOST")
        self.email = os.getenv("SHIFTBOT_EMAIL")
        self.password = os.getenv("SHIFTBOT_PASS")
