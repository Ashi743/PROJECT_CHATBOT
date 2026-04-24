# TOOL SPEC: Session-End Summariser (`memory/summariser.py`)

## Purpose
Extract facts, preferences, and episodic summaries from session conversation. Update semantic/procedural/episodic memory at session end.

---

## Implementation Notes

Reference `STREAMLIT_MEMORY_SPEC.md` section 10 for complete summariser implementation.

## Module Should Include

### Main Function
```python
async def summarise_session(
    session_id: str,
    user_id: str,
    session_state: SessionState
) -> SummariserOutput:
    """
    Summarise session and auto-update user memory.
    
    Args:
        session_id: Session to summarise
        user_id: User who owns session
        session_state: SessionState with turns to summarise
    
    Returns:
        SummariserOutput with extracted facts and updates
    """
```

### Summariser Workflow

1. **Prepare prompt** with session turns
2. **Call GPT-4o-mini** to extract structure
3. **Parse response** into SummariserOutput
4. **Apply semantic updates** (facts) to Redis
5. **Apply procedural updates** (prefs) to Redis
6. **Store session summary** to ChromaDB (episodic)

---

## Summariser Prompt

Send to GPT-4o-mini (cheaper than GPT-4o):

```
You are analyzing a conversation to extract user facts and preferences.

Conversation:
[insert working_context turns here]

Extract:
1. session_summary: 2-3 sentence summary of what was discussed
2. events: List of decisions/actions taken by user
3. emotional_signal: User's mood/sentiment if evident (optional)
4. importance: 0.0-1.0 score for how important this session is
5. semantic_updates: Object with facts to update {name, age, income_monthly, financial_goals, ...}
6. procedural_updates: Object with preferences to update {response_format, tone, ...}

Respond in JSON format:
{
  "session_summary": "...",
  "events": [...],
  "emotional_signal": "...",
  "importance": 0.5,
  "semantic_updates": {...},
  "procedural_updates": {...}
}
```

---

## Update Logic

```python
async def _apply_semantic_updates(
    user_id: str,
    updates: dict
) -> None:
    """Merge semantic updates into existing profile"""
    current = await long_term.load_semantic(user_id)
    
    # Only update if summariser provided value
    for key, value in updates.items():
        if value is not None:
            setattr(current, key, value)
    
    # Mark as recently updated
    current.updated_at = datetime.now(timezone.utc)
    
    await long_term.save_semantic(user_id, current)


async def _apply_procedural_updates(
    user_id: str,
    updates: dict
) -> None:
    """Merge procedural updates into existing profile"""
    current = await long_term.load_procedural(user_id)
    
    # Only update if summariser provided value
    for key, value in updates.items():
        if value is not None:
            setattr(current, key, value)
    
    # Mark as recently updated
    current.updated_at = datetime.now(timezone.utc)
    
    await long_term.save_procedural(user_id, current)


async def _store_session_summary(
    user_id: str,
    session_id: str,
    summary: str,
    importance: float
) -> None:
    """Store session summary as episodic memory"""
    doc = EpisodicDoc(
        doc_id=f"sess_{session_id}",
        document=summary,
        user_id=user_id,
        type="session_summary",
        session_id=session_id,
        created_at=datetime.now(timezone.utc),
        importance=importance,
        tags=["session", "summary"]
    )
    await long_term.save_episodic(doc)
```

---

## Triggered Conditions

Summariser runs when:

1. **Session reaches SUMMARISE_AFTER_TURNS** (default 10)
   - Auto-triggered in frontend after 10th turn
   - Doesn't block chat (async)

2. **User clicks "Save Session to Memory"** button
   - Explicit user action
   - Guaranteed to summarise

3. **Session ends** (timeout or logout)
   - Cleanup summarisation
   - Final memory update

---

## Usage Example

```python
from memory.summariser import summarise_session

# In frontend.py, after 10 turns or on "Save" button click:
session_id = st.session_state["current_thread_id"]
user_id = st.session_state["user_id"]
session = st.session_state["memory_session"]

# Summarise async (don't wait)
asyncio.create_task(summarise_session(session_id, user_id, session))

# Show success immediately
st.success("Session saved to memory!")
```

---

## Example SummariserOutput

**Input Session**:
```
User: I make ₹100K/month. I want to save for retirement by 2035.
Assistant: Great! With your income and timeline, you could save ₹20-25K/month.
User: I prefer detailed explanations and formal tone.
Assistant: Understood. I'll provide comprehensive responses going forward.
User: What should my emergency fund be?
Assistant: For your income, I recommend ₹3L (3 months of expenses).
```

**Output**:
```json
{
  "session_summary": "User shared income of ₹100K/month and retirement goal for 2035. Discussed savings strategy and emergency fund needs (₹3L recommended). User prefers detailed explanations.",
  "events": [
    "Stated retirement goal: 2035",
    "Discussed savings allocation: ₹20-25K/month",
    "Determined emergency fund: ₹3L"
  ],
  "emotional_signal": "focused, determined",
  "importance": 0.7,
  "semantic_updates": {
    "income_monthly": 100000,
    "financial_goals": ["retirement", "emergency_fund"],
    "current_savings": null
  },
  "procedural_updates": {
    "response_format": "detailed",
    "tone": "formal"
  }
}
```

**Memory After Update**:
- `SemanticProfile.income_monthly` = 100000
- `SemanticProfile.financial_goals` = ["retirement", "emergency_fund"]
- `ProceduralProfile.response_format` = "detailed"
- `ProceduralProfile.tone` = "formal"
- ChromaDB stores session summary with importance 0.7

---

## Error Handling

```python
async def summarise_session(...) -> SummariserOutput:
    try:
        prompt = _build_prompt(session_state.working_context)
        response = await summariser_llm.agenerate([HumanMessage(content=prompt)])
        output = _parse_response(response.content)
        
        # Apply updates
        await _apply_semantic_updates(user_id, output.semantic_updates)
        await _apply_procedural_updates(user_id, output.procedural_updates)
        await _store_session_summary(user_id, session_id, output.session_summary, output.importance)
        
        return output
    except JSONDecodeError:
        logger.error("Summariser returned invalid JSON")
        return SummariserOutput(session_summary="Session occurred", importance=0.3)
    except Exception as e:
        logger.error(f"Summariser failed: {e}")
        # Proceed without update; chat continues
        return SummariserOutput(session_summary="Session occurred", importance=0.3)
```

---

## Notes

- Complete implementation should reference STREAMLIT_MEMORY_SPEC.md section 10
- Non-blocking: runs async to avoid delaying session close
- Graceful degradation if LLM unavailable
- Cost-efficient: uses gpt-4o-mini (cheaper than gpt-4o)
