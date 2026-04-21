# Calendar Tool Setup with Calendarific API

## Overview
The chatbot now includes a **Calendar Tool** that fetches public holidays using the **Calendarific API**. This is a free API with a generous free tier.

## Quick Setup

### Step 1: Get Your Free API Key
1. Visit: https://calendarific.com/
2. Click "Sign Up" and create a free account
3. Go to your dashboard → "API KEY"
4. Copy your API key

### Step 2: Add to .env File
```env
OPENAI_API_KEY=your_openai_key_here
CALENDARIFIC_API_KEY=your_api_key_from_calendarific
HOLIDAY_COUNTRY=IN
```

### Step 3: Test the Setup
```bash
cd tool_testing
python test_calender_calendarific.py
```

## Features

### Supported Queries
- `""`  - Check if today is a holiday (default)
- `"2026"` - Get all holidays for 2026
- `"january"` - Get holidays for January
- `"march"` - Get holidays for March
- `"list all"` - Show full year list
- `"show"` - Show full year list
- `"full"` - Show full year list

### Response Includes
1. **Today's Holiday Status** - Is today a holiday?
2. **Upcoming Holidays** - Next 5 upcoming holidays with day counts
3. **Full Holiday List** - All holidays for the year (if requested)
4. **Wikipedia Facts** - Historical events on today's date (bonus feature)

## API Details

### Free Tier
- **Limit**: 100 requests/month
- **Coverage**: 2000+ holidays for countries worldwide
- **No credit card required**

### Response Example
```
Today (21 April 2026) is not a public holiday in IN.

Upcoming Holidays (IN):
  • 03 May — Eid ul-Fitr (In 11 days)
  • 15 Aug — Indian Independence Day (In 116 days)
  • 02 Oct — Gandhi Jayanti (In 164 days)
  • 25 Dec — Christmas (In 248 days)
```

## Supported Countries

### Popular Countries
- **US** - United States
- **GB** - United Kingdom
- **FR** - France
- **DE** - Germany
- **IN** - India
- **AU** - Australia
- **CA** - Canada
- **JP** - Japan
- **BR** - Brazil
- **MX** - Mexico
- **RU** - Russia
- **KR** - South Korea
- **CN** - China
- **SG** - Singapore
- **AE** - United Arab Emirates

### Full List
See all 200+ supported countries at: https://calendarific.com/api-documentation

## Usage Examples

### In the Chatbot
```
User: "What holidays are coming up in India?"
Bot: "Here are the upcoming holidays in India: [list]"

User: "Is today a holiday?"
Bot: "Today (21 April 2026) is not a public holiday in IN."

User: "Show me all holidays for March"
Bot: "All holidays in March IN: [list]"

User: "What holidays in 2026?"
Bot: "All holidays for 2026 in IN: [list]"
```

### Multiple Countries
```
# Change country code in .env
HOLIDAY_COUNTRY=US

# Now queries will fetch US holidays
User: "What holidays are this month?"
Bot: [US holidays for April]
```

## Troubleshooting

### Error: "CALENDARIFIC_API_KEY not set in .env"
**Solution**: 
1. Add your API key to .env file
2. Restart the chatbot
3. Check that .env file is in the correct directory

### Error: "API error: Unknown error"
**Solution**:
- Your API key might be invalid
- Country code might not be supported
- Check your API quota at https://calendarific.com/

### Getting Warnings about API limit?
**Solution**:
- Free tier has 100 requests/month
- Upgrade to paid plan for more requests
- Each holiday query counts as 1 request

## Advanced Configuration

### Change Country Dynamically
Update `.env` to use different country codes:
```env
HOLIDAY_COUNTRY=US    # For United States holidays
HOLIDAY_COUNTRY=GB    # For United Kingdom holidays
HOLIDAY_COUNTRY=JP    # For Japan holidays
```

### Using Multiple Countries
Currently, the tool uses one country at a time. To support multiple countries:
1. Create environment variables for each country
2. Modify calender_tool.py to accept country parameter
3. User can then ask: "Show holidays for US and India"

## File Structure
```
tools/
└── calender_tool.py              # Main calendar implementation

tool_testing/
└── test_calender_calendarific.py # Test suite

CALENDAR_SETUP.md                 # This file
CLAUDE.md                         # Updated with calendar info
```

## Bonus Feature: Wikipedia "On This Day"

The calendar tool also fetches historical events for today's date from Wikipedia:
```
📖 On This Day (21 April):
  • 1993 — The World Wide Web is released into the public domain
  • 1969 — Apollo 13 crew member Jack Swigert reports explosion
  • 1960 — The Valdivia earthquake, the most powerful earthquake recorded
```

This feature requires no API key and works automatically!

## Testing

### Run Full Test Suite
```bash
cd tool_testing
python test_calender_calendarific.py
```

### Run Backend Integration Test
```bash
cd ..
python test_all_tools.py
```

## Support

- **Calendarific Docs**: https://calendarific.com/api-documentation
- **Supported Countries**: https://calendarific.com/supported-countries
- **Free API Key**: https://calendarific.com/

## Next Steps

1. ✅ Get free API key from Calendarific
2. ✅ Add to .env file
3. ✅ Restart chatbot: `streamlit run frontend.py`
4. ✅ Test: "What holidays are coming up?"
5. ✅ Enjoy holiday information!

