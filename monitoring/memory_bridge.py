"""Monitor-to-Memory Bridge — connects monitoring to memory system."""

import logging
from datetime import datetime, timezone
from memory.models import MonitorEvent
from memory.store import MemoryStore
from memory.config import REDIS_URL, CHROMA_HOST, CHROMA_PORT, MONITOR_MEMORY_ENABLED

logger = logging.getLogger(__name__)


def store_monitor_event(user_id: str, session_id: str, event: MonitorEvent) -> dict:
    """
    Store a monitoring event as episodic memory.

    Args:
        user_id: User whose memory to update
        session_id: Current session ID
        event: MonitorEvent from monitoring system

    Returns:
        {status: "ok", doc_id: "..."} or {status: "error", message: "..."}
    """
    if not MONITOR_MEMORY_ENABLED:
        return {"status": "disabled"}

    try:
        store = MemoryStore(redis_url=REDIS_URL, chroma_host=CHROMA_HOST, chroma_port=CHROMA_PORT)

        # Convert event to episodic doc
        doc = event.to_episodic_doc(user_id, session_id)

        # Save to ChromaDB
        store.save_episodic(doc)

        # Update semantic memory if applicable
        if event.event_type == "commodity_alert" and event.commodities:
            sem = store.get_semantic(user_id)

            # Add to user's interests
            existing = set(sem.interests or [])
            for commodity in event.commodities:
                existing.add(commodity)

            updates = {
                "interests": list(existing),
                "last_monitor_alert": datetime.now(timezone.utc),
            }
            store.update_semantic(user_id, updates)

        elif event.event_type == "api_down":
            updates = {
                "api_health_checks": True,
                "last_monitor_alert": datetime.now(timezone.utc),
            }
            store.update_semantic(user_id, updates)

        logger.info(f"Monitor event stored for {user_id}: {event.event_type}")
        return {"status": "ok", "doc_id": doc.doc_id}

    except Exception as e:
        logger.error(f"Failed to store monitor event: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    # Test
    event = MonitorEvent(
        event_type="commodity_alert",
        severity="alert",
        message="Wheat price surged 15%",
        timestamp=datetime.now(timezone.utc),
        commodities=["wheat"],
    )

    result = store_monitor_event("test_user", "test_session", event)
    print(f"[OK] Monitor event stored: {result}")
