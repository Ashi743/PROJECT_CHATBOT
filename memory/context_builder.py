"""Context builder — formats memory into <memory> block."""

import logging
from memory.models import LongTermMemory
from memory.config import MEMORY_BLOCK_MAX_TOKENS

logger = logging.getLogger(__name__)


def build_memory_block(ltm: LongTermMemory, max_tokens: int = MEMORY_BLOCK_MAX_TOKENS) -> str:
    """
    Format long-term memory into <memory> block for prompt.

    Args:
        ltm: Assembled LongTermMemory object
        max_tokens: Max tokens to include (default 400)

    Returns:
        String formatted as <memory>...</memory> block
    """
    lines = ["<memory>"]

    # Build facts line (semantic)
    facts_line = _build_facts_line(ltm.semantic)
    lines.append(facts_line)

    # Build prefs line (procedural)
    prefs_line = _build_prefs_line(ltm.procedural)
    lines.append(prefs_line)

    # Add episodic chunks if available
    if ltm.episodic_chunks:
        recent_line = _build_recent_line(ltm.episodic_chunks)
        if recent_line:
            lines.append(recent_line)

    lines.append("</memory>")

    result = "\n".join(lines)
    return result


def _build_facts_line(semantic) -> str:
    """Extract and format semantic profile."""
    parts = []

    if semantic.name:
        parts.append(f"Name: {semantic.name}")
    if semantic.age:
        parts.append(f"Age: {semantic.age}")
    if semantic.city:
        parts.append(f"City: {semantic.city}")
    if semantic.interests:
        parts.append(f"Interests: {', '.join(semantic.interests)}")
    if semantic.api_health_checks:
        parts.append("Monitors API health")
    if semantic.custom_facts:
        for k, v in semantic.custom_facts.items():
            parts.append(f"{k}: {v}")

    if not parts:
        return "[facts] (no profile yet)"

    return "[facts] " + " | ".join(parts)


def _build_prefs_line(procedural) -> str:
    """Extract and format procedural profile."""
    parts = [
        f"Format: {procedural.response_format}",
        f"Tone: {procedural.tone}",
    ]

    if procedural.preferred_language != "English":
        parts.append(f"Language: {procedural.preferred_language}")

    if procedural.topics_to_avoid:
        parts.append(f"Avoid: {', '.join(procedural.topics_to_avoid)}")

    return "[prefs] " + " | ".join(parts)


def _build_recent_line(episodic_chunks: list[str]) -> str:
    """Format top episodic memories."""
    if not episodic_chunks:
        return ""

    # Take first 2-3 chunks, separated by →
    chunks_str = " → ".join(episodic_chunks[:3])

    # Truncate if too long
    if len(chunks_str) > 500:
        chunks_str = chunks_str[:500] + "..."

    return "[recent] " + chunks_str


if __name__ == "__main__":
    # Test
    from memory.models import SemanticProfile, ProceduralProfile, LongTermMemory

    sem = SemanticProfile(name="Test User", interests=["commodity_prices"])
    proc = ProceduralProfile(tone="friendly", response_format="concise")
    ltm = LongTermMemory(
        semantic=sem,
        procedural=proc,
        episodic_chunks=["Discussed interest in commodity prices"],
    )

    block = build_memory_block(ltm)
    print(block)
