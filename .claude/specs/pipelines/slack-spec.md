# Slack Alerting Specification

## Purpose
Send automated alerts to Slack channel for commodity monitoring and scheduled reports.
Background process, NO user approval required (fire-and-forget).

## Architecture

### Slack Webhook
Setup:
1. Create Slack workspace/channel (e.g., #commodity-alerts)
2. Create incoming webhook: https://api.slack.com/messaging/webhooks
3. Save URL to .env: `SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...`

### Tool: slack_notify
```python
@tool
def slack_notify(message: str, channel: str = "#commodity-alerts") -> str:
    """
    Send message to Slack webhook.
    No HITL - automatic background alerts.
    """
    # Send POST request to webhook
    # Return: {status: "ok"} or error
```

## Message Types

### 1. Monitor Alert (Commodity Price)
Triggered: NEGATIVE sentiment + price drop > 1.5%

```
:alert: COMMODITY ALERT
*Commodity:* WHEAT (ZW=F)
*Sentiment:* NEGATIVE
*Price Change:* -2.15%
*Time:* 2026-04-22 14:30 UTC
*Details:* Supply disruption reported in key growing regions
*Action:* Check market conditions and adjust hedge
```

Format in code:
```python
{
    "text": "[ALERT] COMMODITY ALERT",
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":alert: *COMMODITY ALERT*\n*Commodity:* WHEAT\n*Price Change:* -2.15%"
            }
        },
        {
            "type": "divider"
        }
    ]
}
```

### 2. Daily Consolidated Report
Triggered: Daily at 09:00 UTC (scheduler)

```
:chart_with_upwards_trend: DAILY COMMODITY REPORT
*Date:* 2026-04-22

*Monitored Commodities:*
:wheat: WHEAT: $7.25 [DOWN] -2.15%
  Sentiment: NEGATIVE | Alerts: 2

:corn: CORN: $6.50 [UP] +1.50%
  Sentiment: POSITIVE | Alerts: 0

:seedling: SOY: $13.75 [NEUTRAL] +0.25%
  Sentiment: NEUTRAL | Alerts: 0

*Summary:*
2 of 3 commodities down today. Wheat showing negative sentiment in news. Monitor closely.

*Recommended Actions:*
• Review wheat supply contracts
• Check currency hedges for soy
• No action on corn (stable)
```

### 3. System Health Alert
Triggered: Monitoring failures, API errors

```
:warning: SYSTEM ALERT
*Issue:* Monitor thread crashed for WHEAT
*Error:* yfinance API timeout
*Time:* 2026-04-22 14:30 UTC
*Status:* ATTEMPTING RESTART
*Logs:* [link to error logs]
```

## Internal Function: send_slack_alert()
```python
import requests
from os import getenv

def send_slack_alert(
    message: str,
    title: str = "",
    severity: str = "info",  # info, warning, alert, error
    blocks: list = None
) -> dict:
    """
    Send alert to Slack webhook.
    
    Args:
        message: Plain text message
        title: Optional title (becomes first block)
        severity: info, warning, alert, error (affects emoji/color)
        blocks: Custom Slack block kit (overrides message formatting)
    
    Returns:
        {status: "ok"} or {status: "error", message: "..."}
    """
    webhook_url = getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return {"status": "error", "message": "SLACK_WEBHOOK_URL not set"}
    
    # Default emoji + color by severity
    emoji_map = {
        "info": ":information_source:",
        "warning": ":warning:",
        "alert": ":alert:",
        "error": ":x:"
    }
    
    emoji = emoji_map.get(severity, ":information_source:")
    
    # Build payload
    payload = {
        "text": f"{emoji} {title or message}",
        "blocks": blocks or [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{emoji} *{title or 'Alert'}*\n{message}"
                }
            }
        ]
    }
    
    # Send
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            return {"status": "ok"}
        else:
            return {
                "status": "error",
                "message": f"Slack API returned {response.status_code}"
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

## slack_notify @tool
```python
@tool
def slack_notify(
    message: str,
    title: str = "Alert",
    severity: str = "info"
) -> str:
    """
    Send message to Slack.
    NO HITL - fires automatically.
    
    Args:
        message: Alert message text
        title: Optional title
        severity: info, warning, alert, error
    
    Returns: "[OK] Message sent to Slack" or error
    """
    result = send_slack_alert(message, title, severity)
    
    if result["status"] == "ok":
        return "[OK] Message sent to Slack"
    else:
        return f"[ERROR] {result['message']}"
```

## Integration with Monitor Tool
```python
# In monitor_tool.py
from tools.slack_alert_tool import send_slack_alert

def _send_alert(message: str, callback: Callable = None):
    """
    Default: Send to Slack
    Optional callback: Custom handler (email, sms, etc.)
    """
    if callback:
        callback(message)
    else:
        # Default: Slack
        send_slack_alert(message, severity="alert")

# In start_monitoring():
start_monitoring(
    commodity='wheat',
    alert_callback=lambda msg: send_slack_alert(
        msg,
        title=f"Commodity Alert",
        severity="alert"
    )
)
```

## Daily Report Scheduler (APScheduler)
```python
# In pipelines/daily_report.py
from apscheduler.schedulers.background import BackgroundScheduler
from tools.slack_alert_tool import send_slack_alert
from tools.monitor_tool import get_monitoring_results

def send_daily_report():
    """Generate and send daily commodity report at 09:00 UTC"""
    results = get_monitoring_results.invoke({})
    
    # Parse results → build summary
    message = f"""Daily Commodity Report - {datetime.now().strftime('%Y-%m-%d')}
    
{results}

Recommended Actions: ...
    """
    
    send_slack_alert(
        message,
        title="DAILY COMMODITY REPORT",
        severity="info"
    )

# Setup scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(
    send_daily_report,
    trigger="cron",
    hour=9,
    minute=0,
    timezone="UTC"
)
scheduler.start()
```

## Environment & Testing
```bash
# .env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Test
python -c "
from tools.slack_alert_tool import slack_notify
print(slack_notify.invoke({
    'message': 'Test alert',
    'title': 'Test',
    'severity': 'info'
}))
"
```

## No HITL Rationale
- Background alerts are time-sensitive
- Delays for user approval defeat automation value
- Monitoring is continuous, not event-driven
- Slack is audit log (not send-and-forget like email)
- Operator can disable monitoring in chat if not wanted

## Failure Modes
| Issue | Handling |
|-------|----------|
| Webhook URL invalid | Log error, retry next cycle |
| Network timeout | Retry 3x with exponential backoff |
| Slack API rate limit | Queue message, send when available |
| App restart | Lose pending alerts (trade-off for simplicity) |

## Bunge Relevance
Real-time notifications for commodities trading desk, supply chain events, and market alerts.
