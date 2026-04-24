# Gmail Spec Sheet

## Purpose
Send, draft, search, and retrieve emails via Gmail API (OAuth2).
Requires Gmail OAuth2 credentials setup in gmail_toolkit/.
User-initiated only (HITL required).

## Status
[DONE]

## Trigger Phrases
- "send an email to john@example.com"
- "create a draft for my manager"
- "search my inbox for 'wheat prices'"
- "get message ID 12345"
- "show me the email thread"

## Input Parameters (by tool)
### send_email
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| to | str | yes | Recipient email address |
| subject | str | yes | Email subject |
| body | str | yes | Email body text |

### create_draft
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| to | str | yes | Recipient email address |
| subject | str | yes | Draft subject |
| body | str | yes | Draft body text |

### search_messages
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query | str | yes | Gmail search query (e.g., "wheat prices from:boss@example.com") |

### get_message
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| message_id | str | yes | Message ID from search results |

## Output Format
Email sent to john@example.com with subject: Monthly Report
Message ID: 18f9b1c2d4e5f6a7b8c9d0e1

Draft created. Message ID: draft_12345
Recipients: jane@example.com

Search Results for "wheat prices":
1. john@example.com - Wheat price update - May 15, 2026 (ID: msg_001)
2. market@bunge.com - Commodity alert - May 14, 2026 (ID: msg_002)

## Dependencies
- google-auth-oauthlib (pip: google-auth-oauthlib)
- google-auth-httplib2 (pip: google-auth-httplib2)
- google-api-python-client (pip: google-api-python-client)
- langchain_core.tools

## OAuth2 Setup Required
1. Create project at https://console.cloud.google.com/
2. Enable Gmail API
3. Create OAuth2 Desktop credentials
4. Save JSON to gmail_toolkit/credentials.json
5. First run opens browser for OAuth consent
6. Token saved to gmail_toolkit/token.json (gitignored)

## HITL
YES - Always
- send_email → User confirms before sending
- create_draft → User reviews and can edit before sending
- search_messages → Read-only, returns IDs
- get_message → Read-only, returns message content

## Chaining
Combines with:
- csv_analyst → "analyze sales data and email report"
- monitor_tool → "send alert email if wheat drops 5%"

## Known Issues
- Credentials must be first-party Google account (not service account)
- Token expires every hour; refresh handled automatically
- Large attachments not yet supported (text only)
- MIME multipart emails not yet handled

## Test Command
python -c "
from tools.gmail import send_email, search_messages
# Must have credentials.json setup first
# search_messages('from:boss@example.com')
"

## Bunge Relevance
Automated trading alerts and report distribution to stakeholders.

## Internal Notes
- gmail_tools exported as list of langchain @tool objects
- OAuth2 flow: credentials.json → token.json (via browser)
- Gmail API scopes: ['https://www.googleapis.com/auth/gmail.compose', '.modify', '.readonly']
- Message IDs used for retrieval/threading
