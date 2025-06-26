# ShiftBOT

## ⚠️ DISCLAIMER:

This project is **meant purely for study and experimental purposes**. Do not use this to violate site terms or contractual obligations. Use responsibly. If you end up explaining this to HR, that’s on you.

---

**Shiftbot** is a precision-crafted, email-triggered automation agent that scans your inbox for short-notice shifts and grabs them before your coworkers even finish yawning. Designed for students, part-timers, and schedule-hunters. Perfect if your employer sends out shifts via email and you’re tired of playing refresh roulette.

---

## 🎯 Features

- **Real-time email monitoring** via IMAP IDLE
- **Keyword-based filtering** (e.g., `"$50/hr"`, `"0700:1900"`)
- **Link parsing for eligible shifts**
- **Automated login and shift pickup** using Playwright
- **Telegram notifications** with DEFCON-1 urgency
- **Stealth browser automation** to avoid detection
- **Auto logout before and after**
- **Detailed logs** with timestamps, sender, and subject

---

## 🧪 Setup Instructions

### 1. Clone this repository

```bash
git clone https://github.com/amrxt1/shiftbot.git
cd shiftbot
```

### 3. Set up virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
playwright install
```

### 4. Create .env file

Make a .env file in the root of the project with the following:

```py
# Email login
SHIFTBOT_HOST=imap.example.com
SHIFTBOT_EMAIL=your@email.com
SHIFTBOT_PASS=yourpassword

# Portal login
SHIFTBOT_PORTAL_URL=https://app.shiftboard.com/servola
SHIFTBOT_LOGIN_PASS=your_shiftboard_password

# Telegram bot
NOTIFIER_URL=https://api.telegram.org/bot<your-bot-token>
NOTIFIER_CHAT_ID=<your-chat-id>

# Keywords to match in emails
SHIFTBOT_KEYWORD=keyword1,keyword2
```

### 🚀 Running the Bot

```bash
python main.py
```

**The bot will:**

- Monitor your inbox for new messages
- Filter emails by keywords
- Parse shiftboard links
- Attempt to claim shifts
- Notify you via Telegram
- Exit after successful acquisition
- If no match or no shift is claimed, it keeps looping silently

### 📁 Logs

Logs are saved in `./logs/shiftbot<timestamp>.log` and include:

- Message sender & subject
- Matching keywords
- Parsed shift links
- Playwright actions
- Errors and retries

### 🧠 Tips

- Use precise keywords for your shifts (site names, times, etc.)
- Best used during expected shift-drop windows
- Add page.wait_for_selector() if buttons take long to load
- Make your Telegram bot’s profile a B-2 bomber. It’s tradition.

### 🧱 Future Plans

- Add time-based hunting windows
- Web dashboard for history/stats
- Voice alert fallback
- Telegram control commands (start/stop/status)

### 🏁 Final Words

> Let Shiftbot handle you shcedule for ya.

Made with caffeine, frustration, and Python. Deploy responsibly.

_Copy. Paste. Commit. You’re no longer just a shift worker. You’re running ops._
