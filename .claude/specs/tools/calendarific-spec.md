# Calendarific Tool Spec

## Overview
LangChain tool for querying holidays and calendar events via the Calendarific API. Allows users to:
- Get holidays for any country/year
- Search holidays by keyword (e.g., "Christmas", "Diwali")
- List all supported countries

## Tool File
`tools/calendarific_tool.py`

## Configuration
**Required environment variable:**
```
CALENDARIFIC_API_KEY=your_api_key_here
```

Get free API key at: https://calendarific.com/

## Functions

### 1. get_holidays()
Retrieve all holidays for a specific country and year.

**Signature:**
```python
get_holidays(country: str, year: int = 2026) -> str
```

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `country` | str | Required | ISO 3166-1 country code (e.g., 'US', 'IN', 'GB', 'FR') |
| `year` | int | 2026 | Year to fetch holidays for |

**Returns:**
- Formatted string with list of holidays
- Each line: `YYYY-MM-DD - Holiday Name (description)`
- Error message if API call fails

**Examples:**

Example 1: US holidays 2026
```
Input:
  get_holidays("US", 2026)

Output:
  Holidays in US for 2026:
  
  2026-01-01 - New Year's Day
  2026-01-19 - MLK Jr. Day
  2026-02-16 - Presidents' Day
  2026-03-29 - Easter Sunday
  2026-05-25 - Memorial Day
  2026-07-04 - Independence Day
  2026-09-07 - Labor Day
  ...
```

Example 2: India holidays 2026
```
Input:
  get_holidays("IN", 2026)

Output:
  Holidays in IN for 2026:
  
  2026-01-26 - Republic Day
  2026-03-25 - Holi
  2026-04-10 - Good Friday
  2026-04-14 - Ambedkar Jayanti
  2026-08-15 - Independence Day
  2026-10-02 - Gandhi Jayanti
  ...
```

**Error Handling:**
- Returns `[ERROR]` message if API key not configured
- Returns error if country code invalid
- Handles network timeouts (10 second timeout)
- Handles malformed responses gracefully

---

### 2. search_holidays()
Search for specific holidays by keyword in a country.

**Signature:**
```python
search_holidays(country: str, year: int = 2026, keyword: str = "") -> str
```

**Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `country` | str | Required | ISO 3166-1 country code |
| `year` | int | 2026 | Year to search in |
| `keyword` | str | "" | Holiday name or keyword (case-insensitive) |

**Returns:**
- Matching holidays with dates
- Empty result if no matches found
- Error message if API fails

**Examples:**

Example 1: Find Christmas in US
```
Input:
  search_holidays("US", 2026, "Christmas")

Output:
  Holidays matching 'Christmas' in US (2026):
  
  2026-12-25 - Christmas Day
```

Example 2: Find Diwali in India
```
Input:
  search_holidays("IN", 2026, "Diwali")

Output:
  Holidays matching 'Diwali' in IN (2026):
  
  2026-11-08 - Diwali
```

Example 3: Find "New Year" across countries
```
Input:
  search_holidays("GB", 2026, "New Year")

Output:
  Holidays matching 'New Year' in GB (2026):
  
  2026-01-01 - New Year's Day
```

**Keyword Matching:**
- Case-insensitive
- Matches against holiday name AND description
- Partial matches supported (e.g., "Christ" matches "Christmas")

---

### 3. list_supported_countries()
List all countries supported by Calendarific API.

**Signature:**
```python
list_supported_countries() -> str
```

**Parameters:**
None

**Returns:**
- Formatted list of country codes and names
- Format: `CODE - Country Name`
- Sorted alphabetically by country name

**Example Output:**
```
Supported Countries:

  AE - United Arab Emirates
  AF - Afghanistan
  AL - Albania
  AU - Australia
  AT - Austria
  BD - Bangladesh
  BE - Belgium
  BR - Brazil
  CA - Canada
  CN - China
  ...
  US - United States
  GB - United Kingdom
  IN - India
  ...
  ZA - South Africa
```

---

## Usage in Chat

### User can say:
```
"Get holidays for US in 2026"
→ Tool: get_holidays("US", 2026)

"What's Christmas in the US?"
→ Tool: search_holidays("US", 2026, "Christmas")

"Show me all holidays in India"
→ Tool: get_holidays("IN", 2026)

"Find Diwali"
→ Tool: search_holidays("IN", 2026, "Diwali")

"What countries are supported?"
→ Tool: list_supported_countries()

"Get UK holidays for 2025"
→ Tool: get_holidays("GB", 2025)
```

---

## Integration with Backend

**Add to `backend.py`:**

```python
from tools.calendarific_tool import get_holidays, search_holidays, list_supported_countries

base_tools = [
    # ... existing tools ...
    get_holidays,
    search_holidays,
    list_supported_countries
]
```

**Add to `AVAILABLE_TOOLS` in `frontend.py`:**

```python
AVAILABLE_TOOLS = {
    # ... existing tools ...
    "Get Holidays": "Get holidays for any country via Calendarific",
    "Search Holidays": "Search holidays by keyword (e.g., Christmas, Diwali)",
    "List Countries": "List all supported countries",
}
```

---

## Error Handling

| Error | Message | Cause |
|-------|---------|-------|
| No API Key | `[ERROR] CALENDARIFIC_API_KEY not configured` | .env missing key |
| Invalid Country | `[ERROR] Could not fetch holidays: Invalid country` | Bad country code |
| Network Timeout | `[ERROR] Request timeout while fetching holidays` | API slow/unreachable |
| No Results | `No holidays found for {country} in {year}` | No holidays for that country |
| Keyword Not Found | `No holidays matching '{keyword}' found` | No matching holidays |

---

## Country Codes Reference

**Common countries:**
| Code | Country |
|------|---------|
| US | United States |
| GB | United Kingdom |
| IN | India |
| CA | Canada |
| AU | Australia |
| FR | France |
| DE | Germany |
| JP | Japan |
| BR | Brazil |
| MX | Mexico |
| ZA | South Africa |

Full list: Run `list_supported_countries()`

---

## API Details

**Base URL:** `https://calendarific.com/api/v2`

**Endpoints used:**
- `/holidays` - Get holidays for country/year
- `/countries` - Get list of supported countries

**Rate Limits:**
- Free tier: 75 requests/day
- Timeout: 10 seconds per request

**Response Format:**
```json
{
  "response": {
    "holidays": [
      {
        "name": "New Year's Day",
        "description": "New Year's Day is the first day of the year",
        "date": {
          "iso": "2026-01-01"
        }
      },
      ...
    ]
  }
}
```

---

## Testing

**Run tests:**
```bash
python tools/calendarific_tool.py
```

**Expected output:**
```
Testing Calendarific tool...

[Test 1] Get US holidays for 2026:
  Holidays in US for 2026:
  
  2026-01-01 - New Year's Day
  ...

[Test 2] Search for Christmas:
  Holidays matching 'Christmas' in US (2026):
  
  2026-12-25 - Christmas Day

[Test 3] List supported countries:
  Supported Countries:
  
  AE - United Arab Emirates
  ...
  US - United States
  ...
```

---

## Performance

- **get_holidays()**: ~800-1000ms (API call + parsing)
- **search_holidays()**: ~800-1000ms (API call + filtering)
- **list_supported_countries()**: ~500-700ms (API call)
- **Caching**: None (real-time API calls)

---

## Security

- API key stored in `.env` (not in code)
- No sensitive data in requests
- Timeouts prevent hanging (10 second max)
- Error messages don't expose internal details

---

## Limitations

- Requires CALENDARIFIC_API_KEY in .env
- Free tier: 75 requests/day
- Limited to standard holidays (not custom events)
- No timezone support (returns ISO dates)
- Some countries may have incomplete data
