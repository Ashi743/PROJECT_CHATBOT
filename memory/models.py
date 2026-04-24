"""Pydantic models for memory system."""

from __future__ import annotations
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Turn(BaseModel):
    """Single conversation turn."""
    role: Literal["user", "assistant", "system"]
    content: str


class SessionState(BaseModel):
    """Current session state — working context."""
    session_id: str
    user_id: str
    created_at: datetime
    last_active: datetime
    turn_count: int = 0
    working_context: list[Turn] = []
    active_topic: str = ""
    pending_tasks: list[str] = []


class SemanticProfile(BaseModel):
    """User facts — filled incrementally by monitors + summariser."""
    # Basic profile
    name: Optional[str] = None
    age: Optional[int] = None
    city: Optional[str] = None

    # Monitor-detected facts
    interests: list[str] = []  # From monitoring: commodities, APIs, tools user follows
    api_health_checks: bool = False  # User monitors API health
    last_monitor_alert: Optional[datetime] = None

    # Custom fields (extensible)
    custom_facts: dict[str, Any] = {}

    updated_at: Optional[datetime] = None


class ProceduralProfile(BaseModel):
    """How to behave with this user — communication preferences."""
    preferred_language: str = "English"
    response_format: Literal["concise", "detailed", "bullet_points", "narrative"] = "concise"
    greeting_style: str = ""
    topics_to_avoid: list[str] = []
    known_triggers: list[str] = []
    recurring_queries: list[str] = []
    last_completed_workflows: list[str] = []
    feedback_signals: dict[str, list[str]] = {"positive": [], "negative": []}
    tone: Literal["formal", "friendly", "neutral"] = "friendly"
    updated_at: Optional[datetime] = None


class EpisodicDoc(BaseModel):
    """Single document in ChromaDB episodic collection."""
    doc_id: str
    document: str
    user_id: str
    type: Literal[
        "session_summary",
        "raw_turn",
        "user_note",
        "event",
        "emotional_signal",
        "monitor_event",
    ]
    session_id: str
    created_at: datetime
    importance: float = Field(ge=0.0, le=1.0)
    tags: list[str] = []


class MonitorEvent(BaseModel):
    """Event detected by monitoring system — converted to episodic memory."""
    event_type: str  # "commodity_alert", "api_down", "storage_issue"
    severity: Literal["info", "warning", "alert", "error"]
    message: str
    timestamp: datetime
    commodities: Optional[list[str]] = None
    affected_components: Optional[list[str]] = None

    def to_episodic_doc(self, user_id: str, session_id: str) -> EpisodicDoc:
        """Convert monitor event to episodic memory."""
        doc_text = f"[{self.severity.upper()}] {self.event_type}: {self.message}"
        return EpisodicDoc(
            doc_id=f"mon_{user_id}_{self.timestamp.timestamp()}",
            document=doc_text,
            user_id=user_id,
            type="monitor_event",
            session_id=session_id,
            created_at=self.timestamp,
            importance=0.7,
            tags=[self.event_type, self.severity],
        )


class LongTermMemory(BaseModel):
    """Complete memory context injected into each prompt."""
    semantic: SemanticProfile
    procedural: ProceduralProfile
    episodic_chunks: list[str] = []


class SummariserOutput(BaseModel):
    """Structured output from summariser — extracted from session."""
    session_summary: str
    events: list[str] = []
    emotional_signal: Optional[str] = None
    importance: float = Field(ge=0.0, le=1.0, default=0.5)
    semantic_updates: dict[str, Any] = {}
    procedural_updates: dict[str, Any] = {}
