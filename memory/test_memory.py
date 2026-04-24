"""Basic memory system tests."""

import logging
from datetime import datetime
from memory.models import SemanticProfile, ProceduralProfile, LongTermMemory, MonitorEvent, EpisodicDoc
from memory.context_builder import build_memory_block
from memory.loader import load_long_term_memory

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_models():
    """Test Pydantic models."""
    print("[TEST] Models...")

    sem = SemanticProfile(
        name="Test User",
        age=25,
        interests=["stock_prices", "commodities"],
    )
    assert sem.name == "Test User"
    print("  [OK] SemanticProfile")

    proc = ProceduralProfile(
        tone="friendly",
        response_format="concise",
    )
    assert proc.tone == "friendly"
    print("  [OK] ProceduralProfile")

    ltm = LongTermMemory(
        semantic=sem,
        procedural=proc,
        episodic_chunks=["Discussed market trends"],
    )
    assert ltm.semantic.name == "Test User"
    print("  [OK] LongTermMemory")

    event = MonitorEvent(
        event_type="commodity_alert",
        severity="alert",
        message="Wheat surge 15%",
        timestamp=datetime.utcnow(),
        commodities=["wheat"],
    )
    doc = event.to_episodic_doc("user_1", "sess_1")
    assert doc.type == "monitor_event"
    print("  [OK] MonitorEvent")


def test_context_builder():
    """Test memory block formatting."""
    print("[TEST] Context builder...")

    sem = SemanticProfile(
        name="Alice",
        interests=["stocks", "crypto"],
    )
    proc = ProceduralProfile(
        tone="formal",
        response_format="detailed",
    )
    ltm = LongTermMemory(
        semantic=sem,
        procedural=proc,
        episodic_chunks=["Learned about portfolio management"],
    )

    block = build_memory_block(ltm)
    assert "<memory>" in block
    assert "</memory>" in block
    assert "Alice" in block
    assert "[facts]" in block
    assert "[prefs]" in block
    print("  [OK] Memory block formatted")
    print(f"  Block:\n{block}")


if __name__ == "__main__":
    print("[START] Memory system tests\n")

    try:
        test_models()
        print()
        test_context_builder()
        print("\n[SUCCESS] All tests passed")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
