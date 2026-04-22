# India DateTime Spec Sheet

## Purpose
Get current date and time in India (IST - Indian Standard Time).
No API key required, uses Python zoneinfo module.

## Status
[DONE]

## Trigger Phrases
- "what time is it"
- "what is the current date"
- "what day is today"
- "show me India time"
- "get current time in India"
- "what's the date today"

## Input Parameters
None (no parameters required)

## Output Format
Current Date & Time in India (IST):
Date: Tuesday, 22 April 2026
Time: 14:30:00
Timezone: IST (UTC+5:30)

## Dependencies
- zoneinfo (Python stdlib)
- langchain_core.tools

## HITL
No - read-only, no user confirmation needed

## Chaining
Naturally combines with:
- calendar tool → "what date is today and any holidays?"
- monitor tool → timestamp context for monitoring alerts

## Known Issues
None - clean implementation

## Test Command
python -c "
from tools.india_time_tool import get_india_time
print(get_india_time.invoke({}))
"

## Bunge Relevance
Time tracking for commodity monitoring and event timestamps in agricultural data.

## Internal Notes
- Uses ZoneInfo("Asia/Kolkata") for IST
- Returns 3 lines: date (formatted), time (HH:MM:SS), timezone info
- Exception handling returns error string
