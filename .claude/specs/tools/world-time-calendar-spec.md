# World Time & Calendar Spec Sheet

## Purpose
Smart calendar and world clock assistant with access to:
1. **World Time Tool** – fetches current local time for any city or timezone worldwide
2. **Calendarific Tool** – fetches public holidays for any country and year

Combines both tools to provide time + holiday information across multiple countries.

## Status
[WIP] - Implementing world_time_tool.py to replace india_time_tool.py

## Trigger Phrases
- "What time is it in Germany?"
- "Is tomorrow a holiday in the US?"
- "Show me holidays in Japan for 2025"
- "What's the current time in New York, Dubai, and Sydney?"
- "Is today a public holiday anywhere in Europe?"
- "Current time in London and Paris"
- "Holidays in Brazil this month"
- "What time is it in Tokyo right now?"

## Input Parameters

### World Time Tool
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| city_or_timezone | str | yes | none | City name or IANA timezone (e.g., "Tokyo", "America/New_York", "London") |
| multiple_cities | list[str] | no | none | List of cities for multi-city comparison |

### Calendar Tool (via Calendarific)
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| country | str | yes | none | ISO 3166-1 country code (e.g., 'US', 'IN', 'GB', 'JP') |
| year | int | no | current year | Year to fetch holidays for |
| month | int | no | current month | Month to fetch holidays for |
| next_3_months | bool | no | false | Show holidays for next 3 months |

## Output Format

### Single City Time Query
```
[OK] Current time in Tokyo:

Date: Thursday, 23 April 2026
Time: 22:45:30
Timezone: JST (UTC+9:00)
IANA: Asia/Tokyo
```

### Multi-City Comparison
```
[OK] Current time worldwide:

New York:
  Date: Thursday, 23 April 2026
  Time: 09:45:30
  Timezone: EDT (UTC-4:00)
  
London:
  Date: Thursday, 23 April 2026
  Time: 14:45:30
  Timezone: BST (UTC+1:00)
  
Tokyo:
  Date: Thursday, 23 April 2026
  Time: 22:45:30
  Timezone: JST (UTC+9:00)

Dubai:
  Date: Thursday, 23 April 2026
  Time: 18:45:30
  Timezone: GST (UTC+4:00)
```

### Holiday Query
```
[OK] Upcoming holidays in United States (next 3 months):

2026-05-25 - Memorial Day
2026-07-04 - Independence Day
2026-09-07 - Labor Day
```

### Combined Time + Holiday Query
```
[OK] Time in Japan with holidays:

Date: Thursday, 23 April 2026
Time: 22:45:30
Timezone: JST (UTC+9:00)

Upcoming holidays (next 3 months):
  2026-04-29 - Showa Day
  2026-05-03 - Constitution Day
  2026-05-04 - Greenery Day
  2026-05-05 - Children's Day
```

## Dependencies
- zoneinfo (Python stdlib) - for timezone handling
- datetime (Python stdlib) - for time calculations
- pytz (optional, fallback for IANA mapping)
- requests - for Calendarific API calls
- langchain_core.tools

## HITL
No - read-only, no user confirmation needed

## Chaining
Naturally combines with:
- **nlp_tool** → "What time is it in Germany and what's the sentiment of news there?"
- **web_search** → "What time is it in Tokyo and search for news there"
- **monitor_tool** → timestamp context for global monitoring alerts
- **sql_analyst** → timezone context for database timestamp queries

## Known Issues
- Some edge cases: daylight saving time transitions may show stale UTC offsets
- Ambiguous city names (e.g., "London" could be UK or Canada) default to most populous
- Calendarific free tier: 75 requests/day

## Test Command
```bash
python tools/world_time_tool.py
```

## Expected Output
```
Testing World Time Tool...

[Test 1] Get time in Tokyo:
  [OK] Current time in Tokyo:
  
  Date: Thursday, 23 April 2026
  Time: 22:45:30
  Timezone: JST (UTC+9:00)

[Test 2] Get time in multiple cities:
  [OK] Current time worldwide:
  
  New York: 09:45:30 EDT (UTC-4:00)
  London: 14:45:30 BST (UTC+1:00)
  Tokyo: 22:45:30 JST (UTC+9:00)

[Test 3] Get holidays in US:
  [OK] Upcoming holidays in United States:
  
  2026-05-25 - Memorial Day
  2026-07-04 - Independence Day
```

## City to Timezone Mapping

Common mappings supported:
| City | IANA Timezone | UTC Offset |
|------|---------------|-----------|
| New York | America/New_York | UTC-5:00 to UTC-4:00 |
| London | Europe/London | UTC+0:00 to UTC+1:00 |
| Paris | Europe/Paris | UTC+1:00 to UTC+2:00 |
| Tokyo | Asia/Tokyo | UTC+9:00 |
| Sydney | Australia/Sydney | UTC+10:00 to UTC+11:00 |
| Dubai | Asia/Dubai | UTC+4:00 |
| Mumbai | Asia/Kolkata | UTC+5:30 |
| Singapore | Asia/Singapore | UTC+8:00 |
| Hong Kong | Asia/Hong_Kong | UTC+8:00 |
| Bangkok | Asia/Bangkok | UTC+7:00 |
| Seoul | Asia/Seoul | UTC+9:00 |
| Moscow | Europe/Moscow | UTC+3:00 |
| Berlin | Europe/Berlin | UTC+1:00 to UTC+2:00 |
| Toronto | America/Toronto | UTC-5:00 to UTC-4:00 |
| São Paulo | America/Sao_Paulo | UTC-3:00 |
| Mexico City | America/Mexico_City | UTC-6:00 to UTC-5:00 |
| Los Angeles | America/Los_Angeles | UTC-8:00 to UTC-7:00 |
| Chicago | America/Chicago | UTC-6:00 to UTC-5:00 |
| Denver | America/Denver | UTC-7:00 to UTC-6:00 |
| Vancouver | America/Vancouver | UTC-8:00 to UTC-7:00 |
| Auckland | Pacific/Auckland | UTC+12:00 to UTC+13:00 |

## Country Codes Reference
Complete list available via `get_supported_countries()` from Calendarific tool.

Common codes: US, GB, IN, JP, FR, DE, CN, BR, MX, AU, CA, ZA, SG, AE, etc.

## API Details

### World Time Tool
- Source: Python zoneinfo (stdlib, no API key needed)
- Timezone: IANA Timezone Database
- Accuracy: System clock dependent
- Rate limits: None (local)

### Calendarific Tool
- Base URL: https://calendarific.com/api/v2
- Endpoints: `/holidays`, `/countries`
- Rate limit: 75 requests/day (free tier)
- Timeout: 10 seconds per request
- Requires: CALENDARIFIC_API_KEY in .env

## Error Handling

| Error | Message | Cause |
|-------|---------|-------|
| Invalid City | [ERROR] Unknown city or timezone: 'Xyz' | City not in mapping or invalid IANA timezone |
| Invalid Country | [ERROR] Invalid country code: 'XX' | Bad country code |
| No API Key | [ERROR] CALENDARIFIC_API_KEY not configured | .env missing key |
| Network Timeout | [ERROR] Request timeout while fetching holidays | API slow/unreachable |
| Empty Results | [ALERT] No holidays found for {country} in {period} | No holidays for that country/period |

## Output Status Codes
Following CLAUDE.md conventions (Windows cp1252 compatibility, no emojis):
- `[OK]` - Successful query, data retrieved
- `[ALERT]` - No data found, but query valid
- `[ERROR]` - Query failed or invalid input
- `[WARN]` - Partial data retrieved or deprecated timezone

## Limitations
- Requires CALENDARIFIC_API_KEY for holiday queries (75 req/day limit)
- World time depends on system timezone accuracy
- Some timezones have daylight saving time (UTC offset changes seasonally)
- Ambiguous city names (multiple cities same name) default to most populous
- Holiday data may be incomplete for some countries

## Performance
- **get_world_time(city)**: ~5-10ms (local calculation)
- **get_world_time_multiple(cities)**: ~5-50ms (local calculations)
- **get_holidays(country)**: ~800-1000ms (API call + parsing)
- **get_upcoming_holidays(country)**: ~800-1000ms (API call + filtering)

## Security
- World time tool: No external calls, no sensitive data
- API keys stored in .env (not in code)
- Timeouts prevent hanging (10 second max for API calls)
- Error messages don't expose internal details

## Integration with Backend

**Add to `backend.py`:**

```python
from tools.world_time_tool import (
    get_world_time,
    get_world_time_multiple,
    get_holidays,
    get_upcoming_holidays,
    list_supported_countries
)

base_tools = [
    # ... existing tools ...
    get_world_time,
    get_world_time_multiple,
    get_holidays,
    get_upcoming_holidays,
    list_supported_countries
]
```

**Add to `AVAILABLE_TOOLS` in `frontend.py`:**

```python
AVAILABLE_TOOLS = {
    # ... existing tools ...
    "World Time": "Get current time in any city worldwide",
    "Time Comparison": "Compare time across multiple cities",
    "Get Holidays": "Get holidays for any country via Calendarific",
    "Upcoming Holidays": "Get holidays for next 3 months",
    "Supported Countries": "List all countries with holiday data",
}
```

## User Examples

### Example 1: Single City
User: "What time is it in Tokyo?"
Tool: get_world_time("Tokyo")
Output: Shows Tokyo time with timezone info

### Example 2: Multiple Cities
User: "Show current time in New York, London, and Dubai"
Tool: get_world_time_multiple(["New York", "London", "Dubai"])
Output: Side-by-side comparison of all three cities

### Example 3: Holidays Only
User: "Show me holidays in Japan for 2025"
Tool: get_holidays("JP", 2025)
Output: List of all Japan holidays in 2025

### Example 4: Next 3 Months
User: "What holidays are coming up in the US?"
Tool: get_upcoming_holidays("US")
Output: Holidays for next 3 months starting from today

### Example 5: Combined Query
User: "What time is it in Berlin and are there any holidays coming up there?"
Tools: 
  1. get_world_time("Berlin") → show Berlin time
  2. get_upcoming_holidays("DE") → show German holidays
Output: Time + upcoming holidays combined

## Testing
See test command above. Run independently:
```bash
python tools/world_time_tool.py
```

## Migration from india_time_tool.py
- Old: `tools/india_time_tool.py` (IST only)
- New: `tools/world_time_tool.py` (all timezones)
- Update imports in backend.py
- Deprecate india_time_tool.py (can be removed after migration)
