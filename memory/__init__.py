"""Memory system for LangGraph agentic chatbot.

Provides persistent user facts, conversation history, and preferences.
- Semantic memory: user facts (Redis)
- Procedural memory: user preferences (Redis)
- Episodic memory: conversation context (ChromaDB)
- Session state: working context (Redis)
"""

__version__ = "1.0.0"
