# TOOL SPEC: Memory Models (`memory/models.py`)

## Purpose
Pydantic models for all memory data structures: sessions, semantic/procedural/episodic profiles, monitor events.

---

## Implementation

```python
from __future__ import annotations
from typing import Any, Literal, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class Turn(BaseModel):
    """Single conversation turn (user or assistant message)"""
    role: Literal["user", "assistant", "system"]
    content: str


class SessionState(BaseModel):
    """Current session state — working context"""
    session_id: str
    user_id: str
    created_at: datetime
    last_active: datetime
    turn_count: int = 0
    working_context: list[Turn] = []      # Messages in this session
    active_topic: str = ""                 # Current conversation topic
    pending_tasks: list[str] = []          # Tasks mentioned but not completed


class SemanticProfile(BaseModel):
    """User facts — all optional, filled incrementally by monitors + summariser"""
    name: Optional[str] = None
    age: Optional[int] = None
    city: Optional[str] = None
    income_monthly: Optional[float] = None        # ₹
    income_source: Optional[str] = None
    dependents: Optional[int] = None
    risk_tolerance: Optional[Literal["low","medium","high"]] = None
    financial_goals: list[str] = []
    current_savings: Optional[float] = None
    monthly_expenses: Optional[float] = None
    debt_emi: Optional[float] = None
    investment_style: Optional[str] = None
    preferred_banks: list[str] = []
    tax_bracket: Optional[str] = None
    
    # Monitor-detected facts (stored but not manually edited)
    commodity_interests: list[str] = []          # From monitor: "User follows wheat, corn"
    api_health_checks: bool = False              # From monitor: "User enabled API monitoring"
    last_monitor_alert: Optional[datetime] = None
    
    updated_at: Optional[datetime] = None


class ProceduralProfile(BaseModel):
    """How to behave with this user — communication preferences"""
    preferred_language: str = "English"
    response_format: Literal["concise","detailed","bullet_points","narrative"] = "concise"
    preferred_currency_fmt: str = "₹"
    greeting_style: str = ""
    topics_to_avoid: list[str] = []
    known_triggers: list[str] = []
    recurring_queries: list[str] = []
    last_completed_workflows: list[str] = []
    feedback_signals: dict[str, list[str]] = {"positive": [], "negative": []}
    tone: Literal["formal","friendly","neutral"] = "friendly"
    updated_at: Optional[datetime] = None


class EpisodicDoc(BaseModel):
    """Single document in ChromaDB episodic collection — individual memories"""
    doc_id: str
    document: str                          # Text content
    user_id: str
    type: Literal[
        "session_summary",
        "raw_turn",
        "user_note",
        "event",
        "emotional_signal",
        "monitor_event"
    ]
    session_id: str
    created_at: datetime
    importance: float = Field(ge=0.0, le=1.0)  # 0.0-1.0 priority for retrieval
    tags: list[str] = []


class MonitorEvent(BaseModel):
    """Event detected by monitoring system — converted to episodic memory"""
    event_type: str                       # "commodity_alert", "api_down", "storage_issue"
    severity: Literal["info","warning","alert","error"]
    message: str
    timestamp: datetime
    commodities: Optional[list[str]] = None     # For commodity events
    affected_components: Optional[list[str]] = None  # For system events
    
    def to_episodic_doc(self, user_id: str, session_id: str) -> EpisodicDoc:
        """Convert monitor event to episodic memory"""
        doc_text = f"[{self.severity.upper()}] {self.event_type}: {self.message}"
        return EpisodicDoc(
            doc_id=f"mon_{user_id}_{self.timestamp.timestamp()}",
            document=doc_text,
            user_id=user_id,
            type="monitor_event",
            session_id=session_id,
            created_at=self.timestamp,
            importance=0.7,  # From config
            tags=[self.event_type, self.severity]
        )


class LongTermMemory(BaseModel):
    """Complete memory context injected into each prompt"""
    semantic: SemanticProfile
    procedural: ProceduralProfile
    episodic_chunks: list[str] = []      # Top-K retrieved episodic memories


class SummariserOutput(BaseModel):
    """Structured output from gpt-4o-mini summariser — extracted from session"""
    session_summary: str                  # High-level summary of conversation
    events: list[str] = []               # Noteworthy events/decisions made
    emotional_signal: Optional[str] = None  # User sentiment/mood if detected
    importance: float = Field(ge=0.0, le=1.0, default=0.5)  # Overall importance
    semantic_updates: dict[str, Any] = {}  # Facts to update (e.g., {"name": "Ashish"})
    procedural_updates: dict[str, Any] = {}  # Preferences to update (e.g., {"tone": "formal"})
```

---

## Model Relationships

```
SessionState
  ├─ working_context: list[Turn]     (current conversation)
  ├─ turn_count: int
  └─ active_topic: str

LongTermMemory (injected into chat)
  ├─ semantic: SemanticProfile       (facts about user)
  ├─ procedural: ProceduralProfile   (how to behave)
  └─ episodic_chunks: list[str]      (recent events/context)

SemanticProfile
  ├─ name, age, city, income, goals, etc. (user facts)
  └─ commodity_interests, api_health_checks (from monitors)

ProceduralProfile
  ├─ response_format, tone, language (communication style)
  └─ topics_to_avoid, known_triggers (behavior rules)

EpisodicDoc
  ├─ type: [session_summary, raw_turn, user_note, event, emotional_signal, monitor_event]
  ├─ importance: float (0.0-1.0)
  └─ tags: list[str] (for filtering)

MonitorEvent → EpisodicDoc (converted by to_episodic_doc)
  └─ Also updates SemanticProfile.commodity_interests
```

---

## Field Descriptions

### SemanticProfile
- **Financial fields**: income_monthly, current_savings, monthly_expenses, debt_emi (₹)
- **Goals**: financial_goals (list of strings, e.g., ["retirement", "home loan"])
- **Monitor fields**: commodity_interests, api_health_checks auto-populated from monitors
- **Tax**: tax_bracket (optional, used by finance tool)

### ProceduralProfile
- **Format**: response_format controls LLM output structure
- **Tone**: formal/friendly/neutral affects language style
- **Preferences**: preferred_currency_fmt, preferred_language
- **Signals**: feedback_signals track positive/negative responses for refinement

### EpisodicDoc
- **Types**: session_summary (periodical), raw_turn (individual), event (monitor-detected)
- **Importance**: 0.0-1.0 score; higher = retrieved more often
- **Tags**: searchable metadata (e.g., ["commodity", "wheat", "alert"])

### MonitorEvent
- **event_type**: matches monitor check names ("commodity_alert", "api_down", "storage_issue")
- **severity**: info/warning/alert/error (escalation level)
- **to_episodic_doc()**: method converts event to storable memory format

---

## Usage

```python
from memory.models import LongTermMemory, SemanticProfile, ProceduralProfile, EpisodicDoc

# Load and build context
sem = SemanticProfile(name="Ashish", income_monthly=100000)
proc = ProceduralProfile(tone="friendly", response_format="concise")
episodic = ["Session summary: Discussed retirement planning"]

ltm = LongTermMemory(
    semantic=sem,
    procedural=proc,
    episodic_chunks=episodic
)

# Use in prompt building
print(ltm.semantic.name)  # "Ashish"
print(ltm.procedural.tone)  # "friendly"
```

---

## Notes

- All fields are optional (except doc_id, document, user_id in EpisodicDoc)
- Fields default to empty/None; filled incrementally by monitors + summariser
- Importance scores (0.0-1.0) control episodic memory retrieval ranking
- MonitorEvent.to_episodic_doc() provides automatic conversion for storage
