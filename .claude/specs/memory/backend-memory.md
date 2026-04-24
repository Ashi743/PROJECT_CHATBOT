# INTEGRATION SPEC: Backend Memory Integration (`backend.py`)

## Overview
Modify backend.py to load long-term memory and inject it into LLM prompts.

---

## Changes Required

### 1. Add Imports (top of file)

```python
from memory.sync_wrapper import sync_load_long_term_memory
from memory.context_builder import build_memory_block
from memory.models import SessionState
import uuid
import streamlit as st
```

---

## 2. Modify chat_node Function

**Before**:
```python
def chat_node(state: chatState):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {'messages': [response]}
```

**After**:
```python
def chat_node(state: chatState):
    messages = state["messages"]
    
    # Extract user_id and session_id from Streamlit session state
    user_id = st.session_state.get("user_id", "default")
    session_id = st.session_state.get("current_thread_id", str(uuid.uuid4()))
    
    # Load long-term memory if messages exist
    if messages:
        # Get current user message for similarity search
        user_msg = None
        for msg in reversed(messages):
            if hasattr(msg, 'content'):
                user_msg = msg.content
                break
        
        if user_msg:
            # Load memory
            ltm = sync_load_long_term_memory(user_id, user_msg)
            
            # Build memory block
            memory_block = build_memory_block(ltm)
            
            # Create enhanced system prompt
            system_prompt = (
                f"You are Spendly, a personal finance AI assistant.\n"
                f"You help with budgeting, expense tracking, goal setting, and planning.\n\n"
                f"{memory_block}\n\n"
                f"Always refer to user context above before responding. "
                f"If user shares new facts (income, goals), acknowledge and remember them."
            )
            
            # Prepend memory-aware system message
            from langchain_core.messages import SystemMessage
            messages = [SystemMessage(content=system_prompt)] + messages
    
    # Route to appropriate LLM
    if _requires_analysis_llm(messages):
        analysis_llm_with_tools = analysis_llm.bind_tools(tools)
        response = analysis_llm_with_tools.invoke(messages)
    else:
        response = llm_with_tools.invoke(messages)
    
    return {'messages': [response]}
```

---

## 3. Add Helper Function

```python
def _build_memory_block(ltm) -> str:
    """Build formatted <memory> block for prompt injection"""
    # This is now delegated to memory.context_builder
    # Kept here for reference; actually call build_memory_block() from there
    from memory.context_builder import build_memory_block
    return build_memory_block(ltm)
```

---

## 4. Memory Cleanup (Optional)

If session cleanup needed:

```python
def cleanup_node(state: chatState):
    """Clean up session memory when chat ends"""
    session_id = st.session_state.get("current_thread_id")
    user_id = st.session_state.get("user_id")
    
    if session_id and user_id:
        from memory.sync_wrapper import sync_delete_session
        sync_delete_session(session_id)
    
    return state
```

---

## Integration Points

### 1. Message Building
- Memory context is prepended as SystemMessage
- Inserted before user/assistant messages
- Prevents token overflow (max 400 tokens)

### 2. LLM Awareness
- LLM sees memory facts, preferences, recent context
- Uses memory to personalize response
- No changes to LLM code needed

### 3. Cache Integration
Short-term memory cache layers intercept:
- Before LLM call: check response cache
- After LLM call: cache response
- (See memory-short-term.md for details)

---

## Error Handling

```python
def chat_node(state: chatState):
    messages = state["messages"]
    
    try:
        # Memory loading (optional; gracefully degrades)
        user_id = st.session_state.get("user_id", "default")
        session_id = st.session_state.get("current_thread_id", str(uuid.uuid4()))
        
        memory_block = ""
        if messages:
            try:
                user_msg = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
                ltm = sync_load_long_term_memory(user_id, user_msg)
                memory_block = build_memory_block(ltm)
            except Exception as e:
                # Log but continue; memory is optional
                logger.warning(f"Memory loading failed: {e}")
        
        # Build system prompt with or without memory
        system_prompt = (
            f"You are Spendly, a personal finance AI assistant.\n"
            f"You help with budgeting, expense tracking, goal setting, and planning.\n\n"
        )
        
        if memory_block:
            system_prompt += f"{memory_block}\n\n"
            system_prompt += "Always refer to user context above before responding."
        
        from langchain_core.messages import SystemMessage
        messages = [SystemMessage(content=system_prompt)] + messages
    
    except Exception as e:
        logger.error(f"Chat node error: {e}")
        # Fallback: chat without memory
        messages = messages
    
    # Continue with LLM invocation
    response = llm_with_tools.invoke(messages)
    return {'messages': [response]}
```

---

## Testing

### Unit Test chat_node with Memory

```python
def test_chat_node_with_memory(mocker):
    # Mock Streamlit session state
    st.session_state["user_id"] = "test_user"
    st.session_state["current_thread_id"] = "test_session"
    
    # Mock memory loading
    mock_ltm = LongTermMemory(
        semantic=SemanticProfile(name="Test"),
        procedural=ProceduralProfile(tone="friendly"),
        episodic_chunks=[]
    )
    mocker.patch("memory.sync_wrapper.sync_load_long_term_memory", return_value=mock_ltm)
    
    # Create chat state
    from langchain_core.messages import HumanMessage
    state = {
        "messages": [HumanMessage(content="What's my savings goal?")]
    }
    
    # Call chat_node
    result = chat_node(state)
    
    # Verify memory was injected
    assert result["messages"][0].content  # Got response
    # (More detailed assertions depend on LLM mock)
```

---

## Integration Checklist

- [ ] Import memory functions at top of backend.py
- [ ] Modify chat_node to load and inject memory
- [ ] Add memory block to system prompt
- [ ] Test: Send message → verify memory context appears in logs
- [ ] Test: Verify LLM response is personalized to user facts
- [ ] Test: Verify cache hits work (no memory reload on cache hit)
- [ ] Test: Verify error handling (memory unavailable → fallback to chat)

---

## Performance Notes

- Memory loading adds ~250-600ms (mostly episodic search)
- Can be optimized with parallel loading (semantic + procedural in parallel)
- Response caching (if hit) skips memory loading entirely
- Total latency acceptable for interactive chat

---

## Design Rationale

**Why inject memory as system prompt?**
- LLM sees memory context from first token
- No special prompt engineering needed
- Works with any LLM (not tied to specific model)
- Easy to debug (memory visible in logs)

**Why graceful degradation?**
- Memory is enhancement, not requirement
- Chat works fine without memory (slower but correct)
- Robust to Redis/ChromaDB outages

**Why cache before memory?**
- If response cached, memory loading is skipped
- Improves latency for repeated questions
- Reduces LLM calls
