# TOOL SPEC: Context Builder (`memory/context_builder.py`)

## Purpose
Build the final `<memory>` block to inject into system prompt. Formats loaded memory into concise, token-bounded text.

---

## Implementation Notes

Reference `STREAMLIT_MEMORY_SPEC.md` section 9 for complete context builder implementation.

## Module Should Include

### Main Function
```python
def build_memory_block(ltm: LongTermMemory, max_tokens: int = 400) -> str:
    """
    Format long-term memory into <memory> block for prompt.
    
    Args:
        ltm: Assembled LongTermMemory object
        max_tokens: Max tokens to include (default 400)
    
    Returns:
        String formatted as <memory>...</memory> block
    """
```

### Memory Block Format

Example output:
```
<memory>
[facts] Name: Ashish | Income: ₹100,000/mo | Goals: retirement, home loan | Monitors: wheat, corn
[prefs] Format: concise | Tone: friendly
[recent] Session summary: Discussed emergency fund → Next steps: Calculate buffer
</memory>
```

### Structure

1. **Facts** (semantic profile)
   - Name, age, city, income, goals
   - Monitor-detected interests
   - Filter: only include filled fields
   - Format: key:value pairs separated by |

2. **Preferences** (procedural profile)
   - response_format, tone, language
   - preferred_currency_fmt
   - Filter: non-default values only
   - Format: key:value pairs separated by |

3. **Recent** (episodic chunks)
   - Top-K retrieved memories (usually 2-3)
   - Most relevant first
   - Separated by →
   - Truncated to fit token budget

### Token Counting

```python
def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Estimate token count using tiktoken"""
    import tiktoken
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

def build_memory_block_truncated(ltm, max_tokens=400) -> str:
    """Build memory block, truncate episodic if needed"""
    lines = ["<memory>"]
    
    # Add facts (usually ~50-100 tokens)
    facts_line = _build_facts_line(ltm.semantic)
    lines.append(facts_line)
    
    # Add prefs (usually ~30-50 tokens)
    prefs_line = _build_prefs_line(ltm.procedural)
    lines.append(prefs_line)
    
    # Add episodic, truncate if needed
    tokens_used = count_tokens("\n".join(lines))
    tokens_remaining = max_tokens - tokens_used
    
    if tokens_remaining > 50 and ltm.episodic_chunks:
        recent_line = _build_recent_line(ltm.episodic_chunks, tokens_remaining)
        lines.append(recent_line)
    
    lines.append("</memory>")
    return "\n".join(lines)
```

---

## Helper Functions

### Build Facts Line
```python
def _build_facts_line(semantic: SemanticProfile) -> str:
    """Extract and format semantic profile"""
    parts = []
    
    if semantic.name:
        parts.append(f"Name: {semantic.name}")
    if semantic.income_monthly:
        parts.append(f"Income: ₹{semantic.income_monthly:,.0f}/mo")
    if semantic.financial_goals:
        parts.append(f"Goals: {', '.join(semantic.financial_goals)}")
    if semantic.commodity_interests:
        parts.append(f"Monitors: {', '.join(semantic.commodity_interests)}")
    
    if not parts:
        return "[facts] (no profile yet)"
    
    return "[facts] " + " | ".join(parts)
```

### Build Prefs Line
```python
def _build_prefs_line(procedural: ProceduralProfile) -> str:
    """Extract and format procedural profile"""
    parts = [
        f"Format: {procedural.response_format}",
        f"Tone: {procedural.tone}",
    ]
    
    if procedural.preferred_language != "English":
        parts.append(f"Language: {procedural.preferred_language}")
    
    return "[prefs] " + " | ".join(parts)
```

### Build Recent Line
```python
def _build_recent_line(episodic_chunks: list[str], max_tokens: int) -> str:
    """Format top episodic memories, truncate if needed"""
    if not episodic_chunks:
        return ""
    
    # Take first 2-3 chunks, separated by →
    chunks_str = " → ".join(episodic_chunks[:3])
    
    # Truncate if too long
    if count_tokens(chunks_str) > max_tokens:
        chunks_str = chunks_str[:500] + "..."
    
    return "[recent] " + chunks_str
```

---

## Usage Example

```python
from memory.loader import load_long_term_memory
from memory.context_builder import build_memory_block

# In backend.py chat_node:
user_id = "user_123"
user_message = "How much should I save?"

# Load memory
ltm = await load_long_term_memory(user_id, user_message)

# Build memory block
memory_block = build_memory_block(ltm, max_tokens=400)

# Inject into prompt
system_prompt = f"""You are Spendly, a personal finance AI assistant.

{memory_block}

Always refer to user context above before responding."""

# Send to LLM
response = llm.invoke([SystemMessage(content=system_prompt)] + messages)
```

---

## Memory Block in Action

**User**: "How much should I save for retirement?"

**Memory Block Injected**:
```
<memory>
[facts] Name: Ashish | Income: ₹100,000/mo | Goals: retirement, home loan | Monitors: wheat, corn
[prefs] Format: concise | Tone: friendly
[recent] Last session: Discussed emergency fund goal of 3 months expenses → Decided to allocate ₹25K/month
</memory>
```

**LLM Response** (informed by memory):
"Based on your ₹100K monthly income and retirement goal, I'd recommend saving ₹20-25K/month. With your current emergency fund progress, you're on track. Let's build a retirement corpus of ₹50L..."

---

## Notes

- Complete implementation should reference STREAMLIT_MEMORY_SPEC.md section 9
- Token counting ensures memory block never exceeds prompt budget
- Graceful truncation if episodic search returns large documents
- Format is human-readable and parseable by LLM
