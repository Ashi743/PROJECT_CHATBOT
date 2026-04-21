# Telegram Alert System Setup

## Overview
This guide helps you set up a Telegram-based alert system for your chatbot using BotFather.

---

## Quick Setup (5 Minutes)

### Step 1: Create a Bot with BotFather

1. **Open Telegram** and search for "@BotFather"
2. **Send**: `/newbot`
3. **Answer the prompts:**
   - "What should your bot be called?" → Enter bot name (e.g., "MyChatBot")
   - "Give your bot a username." → Enter username (e.g., "mychatbot_bot")
4. **Copy your bot token** (looks like: `123456789:ABCdefGHIjklmnopQRSTuvwxyzABC-1234`)

### Step 2: Add to .env File

Create/edit `.env` file in your project:

```env
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### Step 3: Get Your Chat ID

**Method 1: Simple Way**
1. Start a message with your bot (send `/start`)
2. Visit this URL: `https://api.telegram.org/botYOUR_TOKEN/getUpdates`
   - Replace `YOUR_TOKEN` with your bot token
3. Look for `"chat":{"id":123456789}` - that's your Chat ID

**Method 2: Using Update Handler**
```python
from alert import get_alert_system

# Bot will log the chat ID when it receives a message
# Check telegram_alerts.log for your chat ID
```

### Step 4: Install Dependencies

```bash
pip install python-telegram-bot
```

### Step 5: Test the System

```bash
python alert.py
```

You should receive test alerts in Telegram!

---

## File Structure

```
alert.py                    # Main alert system
telegram_alerts.log         # Log file for alerts
TELEGRAM_SETUP.md          # This file
.env                       # Configuration (add bot token & chat ID)
```

---

## Configuration Options

### Required
- **TELEGRAM_BOT_TOKEN** - Your bot token from BotFather
- **TELEGRAM_CHAT_ID** - Your personal Telegram chat ID (where to send alerts)

### Optional
- **TELEGRAM_ADMIN_ID** - Alternative admin chat ID (for critical alerts)

### Example .env
```env
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
CALENDARIFIC_API_KEY=cal-...

TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklmnopQRSTuvwxyzABC-1234
TELEGRAM_CHAT_ID=987654321
TELEGRAM_ADMIN_ID=112233445
```

---

## Alert Types

### Alert Levels
```python
AlertLevel.INFO      # ℹ️ Information
AlertLevel.SUCCESS   # ✅ Success
AlertLevel.WARNING   # ⚠️ Warning
AlertLevel.ERROR     # ❌ Error
AlertLevel.CRITICAL  # 🚨 Critical
```

### Usage Examples

```python
from alert import get_alert_system
import asyncio

alert_system = get_alert_system()

# Send different alert types
asyncio.run(alert_system.send_info_alert("System started"))
asyncio.run(alert_system.send_success_alert("Operation completed"))
asyncio.run(alert_system.send_warning_alert("Temperature high"))
asyncio.run(alert_system.send_error_alert("Connection failed"))
asyncio.run(alert_system.send_critical_alert("System down!"))
```

---

## Advanced Features

### Stock Price Change Notifications

```python
asyncio.run(alert_system.notify_stock_price_change(
    symbol="AAPL",
    current_price=268.50,
    previous_price=273.00,
    threshold_percent=5.0  # Alert if change > 5%
))
```

### Web Search Notifications

```python
asyncio.run(alert_system.notify_search_results(
    query="AI news",
    result_count=5
))
```

### Calculator Result Notifications

```python
asyncio.run(alert_system.notify_calculator_result(
    expression="sqrt(16) + 5",
    result="9"
))
```

### Scheduled Alerts

```python
# Send alert after 30 seconds
asyncio.run(alert_system.send_scheduled_alert(
    message="Scheduled reminder",
    delay_seconds=30
))
```

---

## Integration with Chatbot

### In backend.py

```python
from alert import get_alert_system
import asyncio

alert_system = get_alert_system()

# Send alert when user runs search
asyncio.run(alert_system.send_info_alert(
    f"User searched for: latest AI news"
))

# Send alert for stock price queries
asyncio.run(alert_system.send_success_alert(
    f"AAPL Stock: $268.50 (-2.43%)"
))
```

### In frontend.py (Streamlit)

```python
import asyncio
from alert import get_alert_system

def on_search():
    query = st.text_input("Search query")
    if st.button("Search"):
        # Do search
        alert_system = get_alert_system()
        asyncio.run(alert_system.send_info_alert(
            f"Search completed for: {query}"
        ))
```

---

## Features

### Supported Actions
- ✓ Send text alerts
- ✓ Multiple alert levels
- ✓ Alert history tracking
- ✓ Scheduled alerts
- ✓ Stock price change notifications
- ✓ Search result notifications
- ✓ Calculator result notifications
- ✓ Logging to file

### Alert History

```python
alert_system = get_alert_system()

# Get last 10 alerts
history = alert_system.get_alert_history(limit=10)
for alert in history:
    print(f"{alert['timestamp']} | {alert['level']}: {alert['message']}")

# Clear history
alert_system.clear_alert_history()
```

### Configuration Status

```python
status = alert_system.get_config_status()
print(f"Bot initialized: {status['bot_initialized']}")
print(f"Chat ID set: {status['chat_id_set']}")
print(f"Alerts sent: {status['alert_history_count']}")
```

---

## Troubleshooting

### "TELEGRAM_BOT_TOKEN not found"
**Solution:** Add your bot token to `.env` file

### "No target chat ID specified"
**Solution:** Add either TELEGRAM_CHAT_ID or TELEGRAM_ADMIN_ID to `.env`

### "TelegramError: Unauthorized"
**Solution:** Your bot token is invalid. Get a new one from BotFather

### "TelegramError: Bad Request: chat_id is empty"
**Solution:** Your chat ID is invalid. Get the correct one using Method 1 above

### Alerts not appearing in Telegram
**Solutions:**
1. Check bot token is correct
2. Check chat ID is correct
3. Verify bot is not muted in Telegram
4. Check `telegram_alerts.log` for errors
5. Test with `python alert.py`

---

## BotFather Commands

Useful commands in BotFather:

```
/newbot          - Create a new bot
/mybot           - Check your existing bots
/token           - Get bot token
/revoke          - Delete a bot
/setname         - Set bot display name
/setdescription  - Set bot description
/setuserpic      - Set bot profile picture
/setcommands     - Set bot commands
```

---

## Security Best Practices

1. **Keep bot token private** - Don't share in code or GitHub
2. **Use .env file** - Don't hardcode credentials
3. **Limit chat IDs** - Only allow trusted users
4. **Monitor logs** - Check `telegram_alerts.log` regularly
5. **Rotate token if compromised** - Use `/revoke` in BotFather

---

## Example: Complete Integration

```python
# In your main application
import asyncio
from alert import get_alert_system

alert_system = get_alert_system()

# Monitor stock price
async def monitor_stock():
    while True:
        try:
            # Fetch stock price
            price = get_stock_price("AAPL")
            
            # Send alert if significant change
            await alert_system.notify_stock_price_change(
                symbol="AAPL",
                current_price=268.50,
                previous_price=273.00,
                threshold_percent=5.0
            )
            
            # Wait before next check
            await asyncio.sleep(3600)  # 1 hour
            
        except Exception as e:
            await alert_system.send_error_alert(f"Monitoring error: {e}")

# Run monitoring
asyncio.run(monitor_stock())
```

---

## Performance Tips

1. Use async/await for non-blocking alerts
2. Batch multiple alerts if possible
3. Set appropriate thresholds to avoid alert spam
4. Archive old logs periodically
5. Use different alert levels appropriately

---

## Limits & Quotas

- **Rate limit**: ~30 messages per second
- **Message size**: Max 4096 characters
- **File size**: Max 50 MB (for file uploads)
- **Update frequency**: ~20-30 updates per second

---

## Support & Resources

- **Telegram Bot API**: https://core.telegram.org/bots/api
- **python-telegram-bot**: https://github.com/python-telegram-bot/python-telegram-bot
- **BotFather**: @BotFather on Telegram

---

## Next Steps

1. ✓ Create bot with BotFather
2. ✓ Get bot token and chat ID
3. ✓ Add to .env file
4. ✓ Install dependencies: `pip install python-telegram-bot`
5. ✓ Test system: `python alert.py`
6. ✓ Integrate with your application

**Start receiving Telegram alerts today!** 🎉
