from shiftbot import Shiftbot


bot = Shiftbot(headless=True)
try:
    bot.run()
except KeyboardInterrupt:
    print("\n\nInterrupted...")
finally:
    bot.shutdown()
