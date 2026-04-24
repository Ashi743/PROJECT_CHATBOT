"""Session-end summariser — extracts facts from conversations."""

import logging
import json
from datetime import datetime, timezone
from memory.models import SessionState, SummariserOutput, EpisodicDoc
from memory.store import MemoryStore
from memory.config import REDIS_URL, CHROMA_HOST, CHROMA_PORT, SUMMARISER_MODEL

logger = logging.getLogger(__name__)


def summarise_session(
    session_id: str,
    user_id: str,
    session_state: SessionState,
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
    try:
        # For now, create a basic summary without LLM
        # TODO: Integrate with gpt-4o-mini for structured extraction

        turns_text = "\n".join(
            [f"{turn.role.upper()}: {turn.content}" for turn in session_state.working_context]
        )

        # Create basic summary
        summary = f"Session {session_id}: {len(session_state.working_context)} turns discussed."
        if session_state.active_topic:
            summary += f" Topic: {session_state.active_topic}"

        output = SummariserOutput(
            session_summary=summary,
            events=[],
            emotional_signal=None,
            importance=0.5,
            semantic_updates={},
            procedural_updates={},
        )

        # Store session summary in episodic memory
        store = MemoryStore(redis_url=REDIS_URL, chroma_host=CHROMA_HOST, chroma_port=CHROMA_PORT)

        doc = EpisodicDoc(
            doc_id=f"sess_{session_id}",
            document=output.session_summary,
            user_id=user_id,
            type="session_summary",
            session_id=session_id,
            created_at=datetime.now(timezone.utc),
            importance=output.importance,
            tags=["session", "summary"],
        )

        store.save_episodic(doc)
        logger.info(f"Session {session_id} summarised and stored")

        return output

    except Exception as e:
        logger.error(f"Failed to summarise session: {e}")
        return SummariserOutput(
            session_summary="Session occurred",
            importance=0.3,
        )


if __name__ == "__main__":
    # Test
    from memory.models import Turn

    session = SessionState(
        session_id="test_sess",
        user_id="test_user",
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow(),
        working_context=[
            Turn(role="user", content="Hello"),
            Turn(role="assistant", content="Hi there!"),
        ],
    )

    output = summarise_session("test_sess", "test_user", session)
    print(f"[OK] Session summarised: {output}")
