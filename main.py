from shiftbot import Shiftbot


bot = Shiftbot(headless=False)
try:
    bot.run()
except KeyboardInterrupt:
    print("\n\nInterrupted...")
finally:
    bot.shutdown()
