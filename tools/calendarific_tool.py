from langchain_core.tools import tool
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

CALENDARIFIC_API_KEY = os.getenv("CALENDARIFIC_API_KEY")
BASE_URL = "https://calendarific.com/api/v2"


def get_current_date():
    """Get current date"""
    return datetime.now()


def get_next_3_months():
    """Get current month + next 2 months as list of (year, month) tuples"""
    now = get_current_date()
    months = []

    for i in range(3):
        current = now + timedelta(days=30 * i)
        months.append((current.year, current.month))

    return months


@tool
def get_upcoming_holidays(country: str) -> str:
    """
    Get holidays for the next 3 months (current month + 2 upcoming months).
    Smart function that automatically detects current date.

    Args:
        country: Country code (e.g., 'US', 'IN', 'GB', 'FR')

    Returns:
        Formatted list of holidays for next 3 months with dates

    Examples:
        get_upcoming_holidays("IN") -> Holidays in India for next 3 months
        get_upcoming_holidays("US") -> US holidays for next 3 months
    """
    if not CALENDARIFIC_API_KEY:
        return "[ERROR] CALENDARIFIC_API_KEY not configured in .env file"

    try:
        now = get_current_date()
        months_to_fetch = get_next_3_months()

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
            return f"No upcoming holidays found for {country.upper()} in the next 3 months"

        all_holidays.sort(key=lambda x: x["date"])

        lines = [f"Upcoming holidays in {country.upper()} (next 3 months):\n"]
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
def get_holidays(country: str, year: int = None) -> str:
    """
    Get list of holidays for a specific country and year.

    Args:
        country: Country code (e.g., 'US', 'IN', 'GB', 'FR', 'DE', 'JP', 'AU', 'CA')
        year: Year to get holidays for (default: current year)

    Returns:
        Formatted list of holidays with dates and descriptions

    Examples:
        get_holidays("US", 2026) -> List of US holidays in 2026
        get_holidays("IN", 2026) -> List of India holidays in 2026
    """
    if not CALENDARIFIC_API_KEY:
        return "[ERROR] CALENDARIFIC_API_KEY not configured in .env file"

    if year is None:
        year = get_current_date().year

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
            return f"[ERROR] Could not fetch holidays: {response.json().get('error', {}).get('description', 'Unknown error')}"

        data = response.json()

        if "response" not in data or "holidays" not in data["response"]:
            return f"No holidays found for {country} in {year}"

        holidays = data["response"]["holidays"]

        if not holidays:
            return f"No holidays found for {country} in {year}"

        lines = [f"Holidays in {country.upper()} for {year}:\n"]
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
def search_holidays(country: str, year: int = 2026, keyword: str = "") -> str:
    """
    Search holidays in a country by keyword (e.g., 'Easter', 'Christmas', 'New Year').

    Args:
        country: Country code (e.g., 'US', 'IN', 'GB')
        year: Year to search in (default: 2026)
        keyword: Holiday name or keyword to search for

    Returns:
        Matching holidays with dates

    Examples:
        search_holidays("US", 2026, "Christmas")
        search_holidays("IN", 2026, "Diwali")
    """
    if not CALENDARIFIC_API_KEY:
        return "[ERROR] CALENDARIFIC_API_KEY not configured"

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
            return "[ERROR] Could not fetch holidays"

        data = response.json()
        holidays = data.get("response", {}).get("holidays", [])

        if not holidays:
            return f"No holidays found for {country} in {year}"

        if not keyword:
            return "Please provide a keyword to search for (e.g., 'Christmas', 'New Year')"

        keyword_lower = keyword.lower()
        matches = [
            h for h in holidays
            if keyword_lower in h.get("name", "").lower()
               or keyword_lower in h.get("description", "").lower()
        ]

        if not matches:
            return f"No holidays matching '{keyword}' found in {country} for {year}"

        lines = [f"Holidays matching '{keyword}' in {country.upper()} ({year}):\n"]
        for holiday in matches:
            name = holiday.get("name", "Unknown")
            date = holiday.get("date", {}).get("iso", "N/A")
            lines.append(f"  {date} - {name}")

        return "\n".join(lines)

    except Exception as e:
        return f"[ERROR] Search failed: {str(e)}"


@tool
def list_supported_countries() -> str:
    """
    List countries supported by Calendarific API.

    Returns:
        List of supported country codes and names

    Examples:
        list_supported_countries() -> Shows all available countries
    """
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
            return "No countries found"

        lines = ["Supported Countries:\n"]
        for country in sorted(countries, key=lambda x: x.get("country_name", "")):
            code = country.get("iso_3166_1_alpha_2", "??")
            name = country.get("country_name", "Unknown")
            lines.append(f"  {code} - {name}")

        return "\n".join(lines)

    except Exception as e:
        return f"[ERROR] Could not fetch countries: {str(e)}"


if __name__ == "__main__":
    print("Testing Calendarific tool...\n")

    print("[Test 1] Get US holidays for 2026:")
    result = get_holidays.invoke({"country": "US", "year": 2026})
    print(result)
    print()

    print("[Test 2] Search for Christmas:")
    result = search_holidays.invoke({"country": "US", "year": 2026, "keyword": "Christmas"})
    print(result)
    print()

    print("[Test 3] List supported countries:")
    result = list_supported_countries.invoke({})
    print(result)
