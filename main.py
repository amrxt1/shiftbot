from shiftbot import Shiftbot
import time

bot = Shiftbot(headless=False)
try:
    bot.run()
except KeyboardInterrupt:
    print("\n\nInterrupted...")
finally:
    print("Waiting for 15 seconds for a stable state.")
    time.sleep(15)
    bot.shutdown()
