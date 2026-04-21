from langchain_core.tools import tool
from datetime import datetime
from zoneinfo import ZoneInfo

@tool
def get_india_time() -> str:
    """
    Get current date and time in India (IST - Indian Standard Time).
    Use when user asks about current time, date, or what time it is in India.
    """
    try:
        ist = ZoneInfo("Asia/Kolkata")
        india_now = datetime.now(ist)

        current_date = india_now.strftime("%d %B %Y")
        current_time = india_now.strftime("%H:%M:%S")
        day_name = india_now.strftime("%A")

        return f"""
Current Date & Time in India (IST):
📅 Date: {day_name}, {current_date}
🕐 Time: {current_time}
⏰ Timezone: IST (UTC+5:30)
""".strip()

    except Exception as e:
        return f"Error getting India time: {str(e)}"
