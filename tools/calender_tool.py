from langchain_core.tools import tool
from datetime import datetime
import requests
import os

@tool
def get_holidays(query: str = "") -> str:
    """
    Get public holidays and special observances for today, a month, or full year.
    Use when user asks:
    - is today a holiday
    - what holidays are this month / year
    - list upcoming holidays
    - what is special about today
    Input can be empty (defaults to today), a month name, or a year.
    """
    try:
        api_key = os.getenv("CALENDARIFIC_API_KEY")
        country_code = os.getenv("HOLIDAY_COUNTRY", "IN")

        if not api_key:
            return "Error: CALENDARIFIC_API_KEY not set in .env file. Get a free API key at https://calendarific.com/"

        today = datetime.now()
        year  = today.year

        # parse year from query
        for word in query.split():
            if word.isdigit() and len(word) == 4:
                year = int(word)
                break

        # parse month from query
        month_map = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12
        }
        month_filter = None
        for name, num in month_map.items():
            if name in query.lower():
                month_filter = num
                break

        # --- Calendarific API ---
        url    = "https://calendarific.com/api/v2/holidays"
        params = {"api_key": api_key, "country": country_code, "year": year}
        if month_filter:
            params["month"] = month_filter

        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()

        if resp.status_code != 200 or "response" not in data:
            return f"API error: {data.get('meta', {}).get('error_detail', 'Unknown error')}"

        holidays  = data["response"]["holidays"]
        today_str = today.strftime("%Y-%m-%d")
        output    = []

        if not holidays:
            return f"No holidays found for {country_code} in {year}."

        # is today a holiday?
        today_holidays = [h for h in holidays if h["date"]["iso"][:10] == today_str]
        if today_holidays:
            output.append(f"🎉 TODAY ({today.strftime('%d %B %Y')}) IS A HOLIDAY:")
            for h in today_holidays:
                desc = h.get("description", "")[:80] if h.get("description") else ""
                output.append(f"  • {h['name']} — {desc}")
        else:
            output.append(f"📅 Today ({today.strftime('%d %B %Y')}) is not a public holiday in {country_code}.")

        # upcoming 5
        upcoming = [h for h in holidays if h["date"]["iso"][:10] >= today_str][:5]
        if upcoming:
            output.append(f"\n📆 Upcoming Holidays ({country_code}):")
            for h in upcoming:
                date_obj  = datetime.strptime(h["date"]["iso"][:10], "%Y-%m-%d")
                days_away = (date_obj - today).days
                when      = "Today" if days_away == 0 else "Tomorrow" if days_away == 1 else f"In {days_away} days"
                output.append(f"  • {date_obj.strftime('%d %b')} — {h['name']} ({when})")

        # full list if asked
        if any(k in query.lower() for k in ["list", "all", "full", "year", "month", "show"]):
            label = f"{today.strftime('%B')} {year}" if month_filter else str(year)
            output.append(f"\n📋 All Holidays — {label} ({country_code}):")
            for h in holidays:
                date_obj = datetime.strptime(h["date"]["iso"][:10], "%Y-%m-%d")
                output.append(f"  • {date_obj.strftime('%d %b %Y')} — {h['name']}")

        # Wikipedia On This Day (bonus, no key needed)
        try:
            wiki = requests.get(
                f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{today.month}/{today.day}",
                timeout=3
            )
            if wiki.status_code == 200:
                events = wiki.json().get("events", [])[:3]
                if events:
                    output.append(f"\n📖 On This Day ({today.strftime('%d %B')}):")
                    for e in events:
                        output.append(f"  • {e['year']} — {e['text'][:100]}")
        except:
            pass

        return "\n".join(output)

    except requests.exceptions.Timeout:
        return "Calendar API timed out. Try again."
    except Exception as e:
        return f"Calendar tool error: {str(e)}"
