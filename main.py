from shiftbot import Shiftbot


bot = Shiftbot()
try:
    bot.run()
except KeyboardInterrupt:
    print("\n\nInterrupted...")
finally:
    bot.shutdown()
