"""

The Notifying Telegram obj

"""

import requests


class Notifier:
    def __init__(self, url, chat_id):
        self.url = url
        self.chat_id = chat_id

    def notify(self, message):
        requests.get(
            self.url + "/sendMessage",
            params={"chat_id": self.chat_id, "text": message},
        )
