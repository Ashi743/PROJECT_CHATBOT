from langchain_core.tools import tool
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones
import re

CITY_TO_TIMEZONE = {
    "new york": "America/New_York",
    "new york city": "America/New_York",
    "nyc": "America/New_York",
    "london": "Europe/London",
    "paris": "Europe/Paris",
    "berlin": "Europe/Berlin",
    "tokyo": "Asia/Tokyo",
    "sydney": "Australia/Sydney",
    "dubai": "Asia/Dubai",
    "mumbai": "Asia/Kolkata",
    "india": "Asia/Kolkata",
    "delhi": "Asia/Kolkata",
    "singapore": "Asia/Singapore",
    "hong kong": "Asia/Hong_Kong",
    "bangkok": "Asia/Bangkok",
    "seoul": "Asia/Seoul",
    "moscow": "Europe/Moscow",
    "toronto": "America/Toronto",
    "vancouver": "America/Vancouver",
    "sao paulo": "America/Sao_Paulo",
    "mexico city": "America/Mexico_City",
    "los angeles": "America/Los_Angeles",
    "chicago": "America/Chicago",
    "denver": "America/Denver",
    "auckland": "Pacific/Auckland",
    "perth": "Australia/Perth",
    "melbourne": "Australia/Melbourne",
    "auckland": "Pacific/Auckland",
    "auckland": "Pacific/Auckland",
    "bangkok": "Asia/Bangkok",
    "istanbul": "Europe/Istanbul",
    "dubai": "Asia/Dubai",
    "johannesburg": "Africa/Johannesburg",
    "cairo": "Africa/Cairo",
    "lagos": "Africa/Lagos",
    "buenos aires": "America/Argentina/Buenos_Aires",
    "shanghai": "Asia/Shanghai",
    "bangkok": "Asia/Bangkok",
    "manila": "Asia/Manila",
    "ho chi minh": "Asia/Ho_Chi_Minh",
    "bangkok": "Asia/Bangkok",
    "kuala lumpur": "Asia/Kuala_Lumpur",
    "jakarta": "Asia/Jakarta",
    "bangkok": "Asia/Bangkok",
}

def get_timezone_from_city(city: str) -> str:
    """
    Map city name to IANA timezone.
    Returns timezone string or None if not found.
    """
    city_lower = city.lower().strip()

    if city_lower in CITY_TO_TIMEZONE:
        return CITY_TO_TIMEZONE[city_lower]

    if city_lower in available_timezones():
        return city_lower

    return None


def get_utc_offset(tz: ZoneInfo) -> str:
    """Calculate UTC offset string from timezone."""
    try:
        now = datetime.now(tz)
        offset = now.strftime("%z")
        if offset:
            return f"UTC{offset[:3]}:{offset[3:]}"
        return "UTC±0:00"
    except Exception:
        return "UTC±0:00"


def get_timezone_abbr(tz: ZoneInfo) -> str:
    """Get timezone abbreviation (e.g., IST, EST, JST)."""
    try:
        now = datetime.now(tz)
        return now.strftime("%Z")
    except Exception:
        return "UNKNOWN"


@tool
def get_world_time(city_or_timezone: str) -> str:
    """
    Get current date and time in any city or timezone worldwide.

    Args:
        city_or_timezone: City name (e.g., 'Tokyo', 'New York', 'London')
                         or IANA timezone (e.g., 'Asia/Tokyo', 'America/New_York')

    Returns:
        Formatted current date/time with timezone info

    Examples:
        get_world_time("Tokyo")
        get_world_time("New York")
        get_world_time("Asia/Kolkata")
        get_world_time("London")
    """
    try:
        timezone_str = get_timezone_from_city(city_or_timezone)

        if not timezone_str:
            return f"[ERROR] Unknown city or timezone: '{city_or_timezone}'"

        tz = ZoneInfo(timezone_str)
        now = datetime.now(tz)

        date_str = now.strftime("%A, %d %B %Y")
        time_str = now.strftime("%H:%M:%S")
        tz_abbr = get_timezone_abbr(tz)
        utc_offset = get_utc_offset(tz)

        output = f"""[OK] Current time in {city_or_timezone}:

Date: {date_str}
Time: {time_str}
Timezone: {tz_abbr} ({utc_offset})
IANA: {timezone_str}"""

        return output

    except Exception as e:
        return f"[ERROR] Failed to get time for '{city_or_timezone}': {str(e)}"


@tool
def get_world_time_multiple(cities: str) -> str:
    """
    Get current time in multiple cities for comparison.

    Args:
        cities: Comma-separated list of city names
               (e.g., 'New York, London, Tokyo' or 'Tokyo, Sydney, Dubai')

    Returns:
        Formatted times for all cities in a comparison table

    Examples:
        get_world_time_multiple("New York, London, Tokyo")
        get_world_time_multiple("New York, Dubai, Sydney")
        get_world_time_multiple("Tokyo, Singapore, Mumbai")
    """
    try:
        city_list = [c.strip() for c in cities.split(',')]

        if not city_list:
            return "[ERROR] Please provide at least one city"

        results = []
        output_lines = ["[OK] Current time worldwide:\n"]

        for city in city_list:
            timezone_str = get_timezone_from_city(city)

            if not timezone_str:
                output_lines.append(f"{city}:")
                output_lines.append(f"  [ERROR] Unknown city or timezone\n")
                continue

            try:
                tz = ZoneInfo(timezone_str)
                now = datetime.now(tz)

                date_str = now.strftime("%A, %d %B %Y")
                time_str = now.strftime("%H:%M:%S")
                tz_abbr = get_timezone_abbr(tz)
                utc_offset = get_utc_offset(tz)

                output_lines.append(f"{city}:")
                output_lines.append(f"  Date: {date_str}")
                output_lines.append(f"  Time: {time_str}")
                output_lines.append(f"  Timezone: {tz_abbr} ({utc_offset})")
                output_lines.append("")
            except Exception as e:
                output_lines.append(f"{city}:")
                output_lines.append(f"  [ERROR] {str(e)}\n")

        return "\n".join(output_lines)

    except Exception as e:
        return f"[ERROR] Failed to get multiple times: {str(e)}"


@tool
def get_holidays(country: str, year: int = None) -> str:
    """
    Get list of holidays for a specific country and year via Calendarific API.

    Args:
        country: Country code (e.g., 'US', 'IN', 'GB', 'JP', 'FR', 'DE', 'AU', 'CA')
        year: Year to get holidays for (default: current year)

    Returns:
        Formatted list of holidays with dates and descriptions

    Examples:
        get_holidays("US", 2026)
        get_holidays("IN", 2026)
        get_holidays("JP")
    """
    import requests
    import os
    from dotenv import load_dotenv

    load_dotenv()

    CALENDARIFIC_API_KEY = os.getenv("CALENDARIFIC_API_KEY")
    BASE_URL = "https://calendarific.com/api/v2"

    if not CALENDARIFIC_API_KEY:
        return "[ERROR] CALENDARIFIC_API_KEY not configured in .env file"

    if year is None:
        year = datetime.now().year

    try:
        response = requests.get(
            f"{BASE_URL}/holidays",
            params={
                "api_key": CALENDARIFIC_API_KEY,
                "country": country.upper(),
                "year": year
            },
            timeout=10
        )

        if response.status_code != 200:
            error_msg = response.json().get('error', {}).get('description', 'Unknown error')
            return f"[ERROR] Could not fetch holidays: {error_msg}"

        data = response.json()

        if "response" not in data or "holidays" not in data["response"]:
            return f"[ALERT] No holidays found for {country} in {year}"

        holidays = data["response"]["holidays"]

        if not holidays:
            return f"[ALERT] No holidays found for {country} in {year}"

        lines = [f"[OK] Holidays in {country.upper()} for {year}:\n"]
        for holiday in holidays:
            name = holiday.get("name", "Unknown")
            date = holiday.get("date", {}).get("iso", "N/A")
            description = holiday.get("description", "")

            line = f"  {date} - {name}"
            if description:
                line += f" ({description})"
            lines.append(line)

        return "\n".join(lines)

    except requests.exceptions.Timeout:
        return "[ERROR] Request timeout while fetching holidays"
    except requests.exceptions.RequestException as e:
        return f"[ERROR] Network error: {str(e)}"
    except Exception as e:
        return f"[ERROR] Failed to fetch holidays: {str(e)}"


@tool
def get_upcoming_holidays(country: str) -> str:
    """
    Get holidays for the next 3 months (current month + 2 upcoming months).
    Smart function that automatically detects current date.

    Args:
        country: Country code (e.g., 'US', 'IN', 'GB', 'JP', 'FR')

    Returns:
        Formatted list of holidays for next 3 months with dates

    Examples:
        get_upcoming_holidays("IN")
        get_upcoming_holidays("US")
        get_upcoming_holidays("JP")
    """
    import requests
    import os
    from dotenv import load_dotenv
    from datetime import timedelta

    load_dotenv()

    CALENDARIFIC_API_KEY = os.getenv("CALENDARIFIC_API_KEY")
    BASE_URL = "https://calendarific.com/api/v2"

    if not CALENDARIFIC_API_KEY:
        return "[ERROR] CALENDARIFIC_API_KEY not configured in .env file"

    try:
        now = datetime.now()
        months_to_fetch = []

        for i in range(3):
            current = now + timedelta(days=30 * i)
            months_to_fetch.append((current.year, current.month))

        all_holidays = []

        for year, month in months_to_fetch:
            response = requests.get(
                f"{BASE_URL}/holidays",
                params={
                    "api_key": CALENDARIFIC_API_KEY,
                    "country": country.upper(),
                    "year": year,
                    "month": month
                },
                timeout=10
            )

            if response.status_code != 200:
                continue

            data = response.json()
            holidays = data.get("response", {}).get("holidays", [])

            for holiday in holidays:
                date_str = holiday.get("date", {}).get("iso", "")

                if date_str:
                    try:
                        date_obj = datetime.fromisoformat(date_str)
                        now_date = now.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)

                        if date_obj >= now_date:
                            all_holidays.append({
                                "date": date_str,
                                "name": holiday.get("name", "Unknown"),
                                "description": holiday.get("description", "")
                            })
                    except Exception:
                        continue

        if not all_holidays:
            return f"[ALERT] No upcoming holidays found for {country.upper()} in the next 3 months"

        all_holidays.sort(key=lambda x: x["date"])

        lines = [f"[OK] Upcoming holidays in {country.upper()} (next 3 months):\n"]
        for holiday in all_holidays:
            line = f"  {holiday['date']} - {holiday['name']}"
            if holiday["description"]:
                line += f" ({holiday['description']})"
            lines.append(line)

        return "\n".join(lines)

    except requests.exceptions.Timeout:
        return "[ERROR] Request timeout while fetching holidays"
    except Exception as e:
        return f"[ERROR] Failed to fetch upcoming holidays: {str(e)}"


@tool
def list_supported_countries() -> str:
    """
    List countries supported by Calendarific API.

    Returns:
        List of supported country codes and names

    Examples:
        list_supported_countries()
    """
    import requests
    import os
    from dotenv import load_dotenv

    load_dotenv()

    CALENDARIFIC_API_KEY = os.getenv("CALENDARIFIC_API_KEY")
    BASE_URL = "https://calendarific.com/api/v2"

    if not CALENDARIFIC_API_KEY:
        return "[ERROR] CALENDARIFIC_API_KEY not configured"

    try:
        response = requests.get(
            f"{BASE_URL}/countries",
            params={"api_key": CALENDARIFIC_API_KEY},
            timeout=10
        )

        if response.status_code != 200:
            return "[ERROR] Could not fetch countries list"

        data = response.json()
        countries = data.get("response", {}).get("countries", [])

        if not countries:
            return "[ALERT] No countries found"

        lines = ["[OK] Supported Countries:\n"]
        for country in sorted(countries, key=lambda x: x.get("country_name", "")):
            code = country.get("iso_3166_1_alpha_2", "??")
            name = country.get("country_name", "Unknown")
            lines.append(f"  {code} - {name}")

        return "\n".join(lines)

    except Exception as e:
        return f"[ERROR] Could not fetch countries: {str(e)}"


if __name__ == "__main__":
    print("Testing World Time Tool...\n")

    print("[Test 1] Get time in Tokyo:")
    result = get_world_time.invoke({"city_or_timezone": "Tokyo"})
    print(result)
    print()

    print("[Test 2] Get time in New York:")
    result = get_world_time.invoke({"city_or_timezone": "New York"})
    print(result)
    print()

    print("[Test 3] Get time in multiple cities:")
    result = get_world_time_multiple.invoke({"cities": "New York, London, Tokyo, Dubai"})
    print(result)
    print()

    print("[Test 4] Get holidays in US:")
    result = get_holidays.invoke({"country": "US", "year": 2026})
    print(result)
    print()

    print("[Test 5] Get upcoming holidays in India:")
    result = get_upcoming_holidays.invoke({"country": "IN"})
    print(result)
    print()

    print("[Test 6] List supported countries:")
    result = list_supported_countries.invoke({})
    print(result)
