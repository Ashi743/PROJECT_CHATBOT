# Telegram Alert Tool Setup Guide

## Overview
The chatbot now has a **Telegram Alert Tool** that allows it to send messages directly to Telegram when requested by the user.

---

## Quick Setup (10 Minutes)

### Step 1: Create a Bot with BotFather

1. **Open Telegram** (mobile app or web)
2. **Search for**: `@BotFather`
3. **Start conversation** and send: `/newbot`
4. **Answer the questions:**
   - "What should your bot be called?" → `MyChatBot` (display name)
   - "Give your bot a username." → `mychatbot_bot` (must end with _bot)
5. **Copy your bot token** - Save it safely!
   - Example: `123456789:ABCdefGHIjklmnopQRSTuvwxyzABC-1234`

### Step 2: Start Your Bot

1. **Search for your bot** (e.g., `@mychatbot_bot`)
2. **Click START** or send `/start`
3. **Note:** Keep this chat open (you'll need the chat ID)

### Step 3: Get Your Chat ID

**Easy Method:**
1. Open your bot chat
2. Send any message to the bot
3. Visit this URL in your browser:
   ```
   https://api.telegram.org/bot123456789:ABCdefGHIjklmnopQRSTuvwxyzABC-1234/getUpdates
   ```
   (Replace with your actual bot token)
4. Look for `"chat":{"id":987654321}`
5. Your chat ID is `987654321`

### Step 4: Update .env File

Add these lines to your `.env` file:

```env
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklmnopQRSTuvwxyzABC-1234
TELEGRAM_CHAT_ID=987654321
```

**Important Notes:**
- `TELEGRAM_CHAT_ID` must be your **personal user ID**, NOT a bot ID
- If you get "bots can't send messages to bots", you have the wrong chat ID

### Step 5: Test the Tool

```bash
cd tool_testing
python test_telegram_alert.py
```

You should see success messages and receive alerts in Telegram!

---

## How It Works

### Architecture
```
Chatbot (backend.py)
    |
    v
Telegram Alert Tool (send_telegram_alert)
    |
    v
Telegram Bot API
    |
    v
Your Telegram Chat
```

### Example Conversation

```
User: "Send a message to Telegram: Task completed successfully"
Bot: [Uses send_telegram_alert tool]
     "Message sent to Telegram: Task completed successfully"
Telegram: Receives "✅ [SUCCESS] Task completed successfully"
```

---

## Usage Examples

### In the Chatbot

```
User: "Alert on Telegram: System started"
Bot: Message sent to Telegram: System started
Telegram: ℹ️ [INFO] System started

User: "Send warning to Telegram: High CPU usage"
Bot: Message sent to Telegram: High CPU usage
Telegram: ⚠️ [WARNING] High CPU usage

User: "Critical alert: Database connection failed"
Bot: Message sent to Telegram: Database connection failed
Telegram: 🚨 [CRITICAL] Database connection failed
```

---

## Alert Types

### Available Alert Types

```python
"info"      # ℹ️ Information/status update
"success"   # ✅ Operation succeeded
"warning"   # ⚠️ Warning/caution needed
"error"     # ❌ Error occurred
"critical"  # 🚨 Critical issue
```

### Default Behavior
- Default alert type is **"info"**
- The tool automatically adds emoji and timestamp
- All messages go to your Telegram chat

---

## File Structure

```
tools/
└── telegram_alert_tool.py         # Main telegram tool

tool_testing/
└── test_telegram_alert.py         # Test suite

TELEGRAM_ALERT_SETUP.md            # This file
backend.py                         # Integrated with chatbot
.env                              # Configuration (bot token & chat ID)
```

---

## Troubleshooting

### "TELEGRAM_BOT_TOKEN not set in .env"
**Solution:**
1. Make sure you copied the token from BotFather
2. Add it to .env file
3. Restart the chatbot

### "TELEGRAM_CHAT_ID not set in .env"
**Solution:**
1. Start a chat with your bot
2. Visit: https://api.telegram.org/botYOUR_TOKEN/getUpdates
3. Find your chat ID and add to .env

### "bots can't send messages to bots"
**Solution:**
- You've set TELEGRAM_CHAT_ID to another bot's ID
- Get your **personal user chat ID** instead
- Visit the getUpdates URL and find your correct ID

### Messages not appearing in Telegram
**Solutions:**
1. Check bot is not muted (swipe left on chat)
2. Verify bot token is correct
3. Verify chat ID is correct (not a bot ID)
4. Restart the chatbot after updating .env
5. Check telegram_alerts.log for errors

### "Unauthorized" or "404" errors
**Solutions:**
- Bot token is invalid or expired
- Get a new token from BotFather: `/token`
- Delete old bot with `/revoke` if needed
- Create new bot with `/newbot`

---

## Advanced Features

### Integration with Other Tools

```
User: "Search for AI news and alert me on Telegram"
Bot: [Uses web_search] Found 5 articles
     [Uses send_telegram_alert] Sent notification to Telegram
```

### Conditional Alerts

```
User: "Alert on Telegram if AAPL stock drops below $260"
Bot: [Monitors stock price]
     [When price < $260, sends alert]
Telegram: ⚠️ [WARNING] AAPL dropped to $258
```

### Batch Notifications

```
User: "Send all calculation results to Telegram"
Bot: [Calculates complex expressions]
     [Sends each result to Telegram]
Telegram: [Receives multiple alerts]
```

---

## Security Best Practices

1. **Keep bot token private**
   - Never share in code or public forums
   - Don't commit to GitHub

2. **Use .env file**
   - Store sensitive data in .env
   - Add .env to .gitignore

3. **Limit bot permissions**
   - Use BotFather to set allowed commands
   - Only grant necessary permissions

4. **Monitor alerts**
   - Check telegram_alerts.log regularly
   - Review who has access to your bot

5. **Rotate credentials if compromised**
   - Delete bot: `/revoke` in BotFather
   - Create new bot: `/newbot`

---

## Useful BotFather Commands

```
/start          - Start BotFather
/newbot         - Create new bot
/token          - Get token for bot
/revoke         - Delete/revoke a bot
/setname        - Set bot display name
/setdescription - Set bot description
/setcommands    - Set bot commands
```

---

## Common Use Cases

### 1. Task Completion Alerts
```
User: "Run the analysis and alert when done"
Bot: [Runs analysis]
     [Sends alert: Task completed]
Telegram: ✅ [SUCCESS] Analysis completed
```

### 2. Error Notifications
```
User: "Search for missing data and alert if errors occur"
Bot: [Encounters error]
     [Sends alert immediately]
Telegram: ❌ [ERROR] Connection timeout
```

### 3. Status Updates
```
User: "Send hourly status to Telegram"
Bot: [Sends updates every hour]
Telegram: ℹ️ [INFO] System running normally
```

### 4. Warning Thresholds
```
User: "Alert when CPU exceeds 80%"
Bot: [Monitors CPU]
     [Triggers when threshold exceeded]
Telegram: ⚠️ [WARNING] CPU at 85%
```

---

## Configuration Examples

### Minimal Setup
```env
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Full Setup (with all tools)
```env
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
TAVILY_API_KEY=tvly-...
CALENDARIFIC_API_KEY=cal-...
HOLIDAY_COUNTRY=IN
```

---

## Testing

### Manual Test
```bash
cd tool_testing
python test_telegram_alert.py
```

### Backend Integration Test
```bash
python test_all_tools.py
```

### Live Test with Chatbot
```bash
streamlit run frontend.py
# Then say: "Send a test message to Telegram"
```

---

## Performance & Limits

- **Rate limit**: ~30 messages per second
- **Message size**: Max 4096 characters
- **Response time**: 1-3 seconds typically
- **Reliability**: 99.99% delivery rate

---

## Getting Help

### Resources
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **BotFather**: Search `@BotFather` on Telegram
- **Telegram Docs**: https://core.telegram.org/bots

### Check Logs
```bash
# View alert logs
tail -f telegram_alerts.log

# Search for errors
grep ERROR telegram_alerts.log
```

---

## Next Steps

1. ✅ Create bot with BotFather
2. ✅ Get bot token and chat ID
3. ✅ Add to .env file
4. ✅ Test with: `python test_telegram_alert.py`
5. ✅ Use in chatbot: "Send message to Telegram: ..."
6. ✅ Set up other optional tools if needed

---

## Quick Command Reference

```bash
# Get your chat ID (replace TOKEN)
https://api.telegram.org/botTOKEN/getUpdates

# Add to .env
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Test setup
python tool_testing/test_telegram_alert.py

# Run chatbot
streamlit run frontend.py

# View logs
tail -f telegram_alerts.log
```

**Start sending Telegram alerts from your chatbot! 🚀**
